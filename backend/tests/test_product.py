import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pytest
from sqlalchemy import select, update, func
from fastapi.testclient import TestClient
from app import config
from app.main import app
from app.db import engine, runs, trials, now
from app.benchmarks import TASKS, fingerprint
from app.worker import claim, process, tick
from app.runner import evaluate, RunnerError
from app.agents import generate, AgentError, cost
from conftest import payload


def create(client, **changes):
    r = client.post("/api/runs", json=payload(**changes))
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_reference_full_suite_and_exports(client):
    id = create(client, repeats=2)
    assert tick()
    report = client.get("/api/runs/" + id).json()
    assert report["state"] == "completed" and report["score"] == 100
    assert report["completed_trials"] == 12 and len(report["trials"]) == 12
    assert report["total"] == 72 and report["passed"] == 72
    assert report["cost_usd"] is None
    assert all(
        t["source_hash"] == __import__("hashlib").sha256(t["source"].encode()).hexdigest()
        for t in report["trials"]
    )
    export = client.get("/api/runs/" + id + "/export")
    assert export.json() == report and "attachment" in export.headers["content-disposition"]
    csv = client.get("/api/runs/" + id + "/export?format=csv")
    assert len(csv.text.splitlines()) == 13
    assert client.get("/api/runs/" + id + "/export?format=xml").status_code == 422


def test_naive_baseline_really_fails(client):
    id = create(client, agent="naive")
    tick()
    report = client.get("/api/runs/" + id).json()
    assert report["state"] == "completed" and 0 < report["score"] < 100
    assert any(not c["passed"] for t in report["trials"] for c in t["cases"])


def test_idempotent_retry_conflict(client):
    p = payload(idempotency_key="repeated-request")
    a = client.post("/api/runs", json=p)
    b = client.post("/api/runs", json=p)
    assert b.status_code == 200 and a.json()["id"] == b.json()["id"]
    assert client.post("/api/runs", json=p | {"repeats": 2}).status_code == 409
    assert client.get("/api/runs").json()["total"] == 1


def test_concurrent_identical_requests(client):
    p = payload(idempotency_key="concurrent-request")
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: client.post("/api/runs", json=p), range(8)))
    assert all(r.status_code in (200, 201) for r in responses)
    assert len({r.json()["id"] for r in responses}) == 1


def test_atomic_worker_claim_and_recovery(client):
    id = create(client)
    with ThreadPoolExecutor(max_workers=4) as pool:
        claims = list(pool.map(lambda _: claim(), range(4)))
    held = [r for r in claims if r]
    assert len(held) == 1
    with engine.begin() as c:
        c.execute(update(runs).where(runs.c.id == id).values(lease_until=now() - 1))
    replacement = claim()
    assert replacement["lease_token"] != held[0]["lease_token"]
    process(held[0])
    process(replacement)
    assert client.get("/api/runs/" + id).json()["completed_trials"] == 6


def test_resume_skips_existing_trials(client):
    id = create(client)
    run = claim()
    process(run)
    with engine.begin() as c:
        c.execute(
            update(runs)
            .where(runs.c.id == id)
            .values(state="running", finished=None, lease_token="expired", lease_until=now() - 1)
        )
    process(claim())
    with engine.connect() as c:
        assert c.execute(select(func.count()).select_from(trials)).scalar_one() == 6


def test_queued_cancellation(client):
    id = create(client)
    assert client.post("/api/runs/" + id + "/cancel", json={}).status_code == 200
    assert not claim()
    assert client.get("/api/runs/" + id).json()["state"] == "cancelled"


def test_cancellation_discards_inflight_trial(client, monkeypatch):
    id = create(client)
    from app import worker

    original = worker.evaluate

    def cancel_then_score(source, task, agent):
        client.post("/api/runs/" + id + "/cancel", json={})
        return original(source, task, agent)

    monkeypatch.setattr(worker, "evaluate", cancel_then_score)
    tick()
    report = client.get("/api/runs/" + id).json()
    assert report["state"] == "cancelled" and report["completed_trials"] == 0


def test_provider_failure_counts_zero_not_skipped(client, monkeypatch):
    id = create(client)
    from app import worker

    def failure(*args):
        raise AgentError("Provider unavailable")

    monkeypatch.setattr(worker, "generate", failure)
    tick()
    report = client.get("/api/runs/" + id).json()
    assert report["state"] == "completed" and report["score"] == 0 and report["failed_trials"] == 6
    assert report["total"] == 36


def test_infrastructure_error_not_ranked(client, monkeypatch):
    id = create(client)
    from app import worker

    def failure(*args):
        raise RunnerError("Docker unavailable")

    monkeypatch.setattr(worker, "evaluate", failure)
    tick()
    report = client.get("/api/runs/" + id).json()
    assert report["state"] == "error" and report["score"] is None
    assert client.get("/api/compare", params={"left": id, "right": id}).status_code == 409


def test_comparison_requires_equal_suite_and_repeats(client):
    a = create(client)
    b = create(client, agent="naive")
    c = create(client, task_ids=["merge-intervals"])
    d = create(client, repeats=2)
    while tick():
        pass
    r = client.get("/api/compare", params={"left": a, "right": b})
    assert r.status_code == 200 and r.json()["left"]["score"] > r.json()["right"]["score"]
    for other in (c, d):
        assert client.get("/api/compare", params={"left": a, "right": other}).status_code == 409


def test_owner_isolation(client):
    id = create(client)
    with TestClient(app) as other:
        other.headers["X-AgentBench-Request"] = "browser"
        other.post(
            "/api/auth/login",
            json={"email": "other@example.com", "password": "Other-user-pass-2026"},
        )
        assert other.get("/api/runs").json()["total"] == 0
        for suffix in ("", "/export"):
            assert other.get("/api/runs/" + id + suffix).status_code == 404
        assert other.post("/api/runs/" + id + "/cancel", json={}).status_code == 404
        assert other.get("/api/compare", params={"left": id, "right": id}).status_code == 404


def test_guard_session_logout_and_throttle(client):
    assert (
        client.post("/api/runs", json=payload(), headers={"X-AgentBench-Request": ""}).status_code
        == 403
    )
    assert client.post("/api/auth/logout", json={}).status_code == 200
    assert client.get("/api/me").status_code == 401
    for _ in range(10):
        assert (
            client.post(
                "/api/auth/login", json={"email": "missing@example.com", "password": "bad"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login", json={"email": "missing@example.com", "password": "bad"}
        ).status_code
        == 429
    )


def test_catalog_does_not_expose_solutions_and_validates_input(client):
    catalog = client.get("/api/catalog").json()
    assert len(catalog["tasks"]) == 6
    assert not any("reference" in t or "cases" in t for t in catalog["tasks"])
    for change in (
        {"task_ids": ["unknown"]},
        {"task_ids": ["merge-intervals", "merge-intervals"]},
        {"name": "  "},
        {"repeats": 4},
        {"agent": "unknown"},
    ):
        assert client.post("/api/runs", json=payload(**change)).status_code == 422


def test_local_runner_refuses_external_source():
    task = TASKS[0]
    for source, agent in ((task["reference"], "provider"), ('print("hi")', "reference")):
        with pytest.raises(RunnerError):
            evaluate(source, task, agent)


def test_provider_requires_docker(client, monkeypatch):
    monkeypatch.setattr(config, "PROVIDER_BASE_URL", "https://provider.example/v1")
    monkeypatch.setattr(config, "PROVIDER_MODEL", "test-model")
    monkeypatch.setattr(config, "PROVIDER_API_KEY", "test-key")
    assert client.post("/api/runs", json=payload(agent="provider")).status_code == 422


def test_fingerprint_and_immutable_snapshot(client, monkeypatch):
    id = create(client)
    with engine.connect() as c:
        run = c.execute(select(runs).where(runs.c.id == id)).mappings().one()
    original = json.loads(run["snapshot"])
    assert fingerprint(original) == run["suite_hash"]
    monkeypatch.setitem(TASKS[0], "prompt", "Changed after acceptance")
    tick()
    report = client.get("/api/runs/" + id).json()
    assert report["tasks"][0]["prompt"] == original[0]["prompt"]


def test_cost_is_exact_and_unknown_stays_null(monkeypatch):
    monkeypatch.setattr(config, "INPUT_PRICE", "1.25")
    monkeypatch.setattr(config, "OUTPUT_PRICE", "5.5")
    assert Decimal(cost(1000, 2000)) == Decimal("0.01225")
    assert cost(None, 2000) is None
    monkeypatch.setattr(config, "INPUT_PRICE", "NaN")
    assert cost(1, 1) is None


def test_provider_adapter_parses_source_and_usage(monkeypatch):
    import httpx

    monkeypatch.setattr(config, "PROVIDER_BASE_URL", "https://provider.example/v1")
    monkeypatch.setattr(config, "PROVIDER_MODEL", "test-model")
    monkeypatch.setattr(config, "PROVIDER_API_KEY", "test-secret")

    def handle(request):
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-secret"
        data = json.loads(request.content)
        assert TASKS[0]["reference"] not in data["messages"][1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "```python\ndef solve(x):\n    return x\n```"}}
                ],
                "model": "test-model",
                "usage": {"prompt_tokens": 20, "completion_tokens": 10},
            },
        )

    real = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda **kw: real(transport=httpx.MockTransport(handle), **kw)
    )
    gen = generate("provider", TASKS[0])
    assert gen.source.startswith("def solve") and gen.input_tokens == 20 and gen.output_tokens == 10


def test_csv_formula_injection_is_escaped(client):
    id = create(client, task_ids=["merge-intervals"])
    tick()
    with engine.begin() as c:
        c.execute(update(trials).where(trials.c.run_id == id).values(model="=malicious-formula"))
    assert "'=malicious-formula" in client.get("/api/runs/" + id + "/export?format=csv").text


def test_backlog_and_pagination(client):
    for _ in range(10):
        create(client, task_ids=["merge-intervals"])
    assert client.post("/api/runs", json=payload()).status_code == 429
    for r in client.get("/api/runs").json()["items"]:
        client.post("/api/runs/" + r["id"] + "/cancel", json={})
    for _ in range(11):
        id = create(client, task_ids=["merge-intervals"])
        client.post("/api/runs/" + id + "/cancel", json={})
    first = client.get("/api/runs").json()
    second = client.get("/api/runs?page=2").json()
    assert first["total"] == 21 and len(first["items"]) == 20 and len(second["items"]) == 1


@pytest.mark.skipif(
    __import__("os").environ.get("TEST_DOCKER") != "true",
    reason="Docker integration is enabled explicitly in CI",
)
def test_docker_runner_scores_real_external_source_and_restricts_environment(monkeypatch):
    monkeypatch.setattr(config, "RUNNER", "docker")
    task = TASKS[0]
    result = evaluate(task["reference"], task, "provider")
    assert result["state"] == "scored" and result["passed"] == len(task["cases"])
    bad = evaluate("def solve(x):\n    return []\n", task, "provider")
    assert bad["passed"] < bad["total"]
    probe = dict(cases=[(None, True)], reference="", naive="")
    source = """import os, socket
def solve(x):
    blocked = False
    try:
        socket.create_connection(("1.1.1.1", 80), timeout=.2)
    except OSError:
        blocked = True
    return os.getuid()==65534 and "PROVIDER_API_KEY" not in os.environ and blocked
"""
    assert evaluate(source, probe, "provider")["passed"] == 1
    timeout = evaluate("while True: pass", task, "provider")
    assert timeout["state"] == "failed" and timeout["passed"] == 0


def test_worker_readiness_comes_from_recent_heartbeat(client, monkeypatch):
    from app import worker
    from app.db import worker_status

    monkeypatch.setattr(worker, "_last_heartbeat", 0)
    assert not client.get("/api/runner").json()["ready"]
    worker.heartbeat()
    assert client.get("/api/runner").json()["ready"]
    with engine.begin() as c:
        c.execute(update(worker_status).values(seen=now() - 100))
    assert not client.get("/api/runner").json()["ready"]


def test_invalid_provider_responses_are_trial_errors_without_secrets(monkeypatch):
    import httpx

    monkeypatch.setattr(config, "PROVIDER_BASE_URL", "https://provider.example/v1")
    monkeypatch.setattr(config, "PROVIDER_MODEL", "test-model")
    monkeypatch.setattr(config, "PROVIDER_API_KEY", "secret-that-must-not-leak")
    real = httpx.Client
    for body in (
        {"choices": []},
        {"choices": [{"message": {"content": "def solve(x): return x"}}], "usage": "invalid"},
    ):
        monkeypatch.setattr(
            httpx,
            "Client",
            lambda **kw: real(
                transport=httpx.MockTransport(lambda r: httpx.Response(200, json=body)), **kw
            ),
        )
        with pytest.raises(AgentError) as error:
            generate("provider", TASKS[0])
        assert "secret-that-must-not-leak" not in str(error.value)
    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kw: real(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"x" * 256_001)),
            **kw,
        ),
    )
    with pytest.raises(AgentError, match="exceeds"):
        generate("provider", TASKS[0])


def test_unavailable_runner_does_not_request_a_model(client, monkeypatch):
    from app import worker

    id = create(client)
    monkeypatch.setattr(
        worker, "readiness", lambda: dict(mode="docker", ready=False, detail="Sandbox unavailable")
    )

    def must_not_generate(*args):
        raise AssertionError("Generation should not start without an available runner")

    monkeypatch.setattr(worker, "generate", must_not_generate)
    process(claim())
    report = client.get("/api/runs/" + id).json()
    assert report["state"] == "error" and report["completed_trials"] == 0
