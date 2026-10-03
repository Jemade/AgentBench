import csv
from contextlib import asynccontextmanager
import io
import json
import secrets
import uuid
from decimal import Decimal
from pathlib import Path
from statistics import median
from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.exc import IntegrityError
from . import config
from .db import (
    transaction,
    engine,
    users,
    sessions,
    throttles,
    runs,
    trials,
    now,
    initialize,
    worker_status,
)
from .security import current_user, password_matches, password_hash, digest
from .benchmarks import TASKS, VERSION, public_task, snapshot, fingerprint
from .agents import available_agents


@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app = FastAPI(title="AgentBench API", version="1.0.0", lifespan=lifespan)
DUMMY_HASH = password_hash("unknown-account-placeholder")


@app.middleware("http")
async def guards(request, call_next):
    if request.url.path.startswith("/api/") and request.method in (
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    ):
        if request.headers.get("X-AgentBench-Request") != "browser":
            return JSONResponse({"detail": "Missing request guard header"}, 403)
        length = request.headers.get("content-length")
        if not length or not length.isdigit() or int(length) > 100_000:
            return JSONResponse({"detail": "Request body must have a length below 100 KB"}, 413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'"
        if request.url.path not in ("/docs", "/redoc")
        else "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com; connect-src 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=1, max_length=256)


class RunInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    agent: str
    task_ids: list[str] = Field(min_length=1, max_length=6)
    repeats: int = Field(default=1, ge=1, le=3)
    idempotency_key: str = Field(min_length=8, max_length=100)

    @field_validator("name")
    @classmethod
    def name_valid(cls, value):
        if not value.strip():
            raise ValueError("Name must not be blank")
        return value.strip()


@app.get("/api/health")
def health():
    with engine.connect() as c:
        c.execute(select(1))
    return {"status": "ok"}


@app.post("/api/auth/login")
def login(data: Login, request: Request, response: Response):
    email = data.email.strip().lower()
    key = digest((request.client.host if request.client else "unknown") + "|" + email)
    with transaction() as c:
        try:
            with c.begin_nested():
                c.execute(insert(throttles).values(key=key, count=0, until=now() + 900))
        except IntegrityError:
            pass
        c.execute(
            update(throttles)
            .where(throttles.c.key == key, throttles.c.until < now())
            .values(count=0, until=now() + 900)
        )
        allowed = c.execute(
            update(throttles)
            .where(throttles.c.key == key, throttles.c.count < 10)
            .values(count=throttles.c.count + 1)
        ).rowcount
    if not allowed:
        raise HTTPException(429, "Too many attempts. Try again in 15 minutes.")
    with engine.connect() as c:
        user = c.execute(select(users).where(users.c.email == email)).mappings().first()
    valid = password_matches(data.password, user["password"] if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Invalid email or password")
    secret = secrets.token_urlsafe(32)
    with transaction() as c:
        c.execute(delete(throttles).where(throttles.c.key == key))
        c.execute(delete(sessions).where(sessions.c.expires < now()))
        c.execute(
            insert(sessions).values(token=digest(secret), user_id=user["id"], expires=now() + 43200)
        )
    response.set_cookie(
        "agentbench_session",
        secret,
        httponly=True,
        samesite="strict",
        secure=config.SECURE_COOKIE,
        max_age=43200,
    )
    return {k: user[k] for k in ("id", "name", "email")}


@app.post("/api/auth/logout")
def logout(request: Request, response: Response, user=Depends(current_user)):
    with transaction() as c:
        c.execute(
            delete(sessions).where(
                sessions.c.token == digest(request.cookies.get("agentbench_session", ""))
            )
        )
    response.delete_cookie("agentbench_session")
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


@app.get("/api/catalog")
def catalog(user=Depends(current_user)):
    return {
        "version": VERSION,
        "tasks": [public_task(t) for t in TASKS],
        "agents": available_agents(),
        "runner_mode": config.RUNNER,
        "provider_requires_docker": True,
    }


@app.get("/api/runner")
def runner_status(user=Depends(current_user)):
    with engine.connect() as c:
        row = (
            c.execute(select(worker_status).where(worker_status.c.id == "worker"))
            .mappings()
            .first()
        )
    if not row or row["seen"] < now() - 90:
        return {
            "mode": config.RUNNER,
            "ready": False,
            "detail": "No recent worker heartbeat. Start the worker process.",
        }
    if row["mode"] != config.RUNNER:
        return {
            "mode": config.RUNNER,
            "ready": False,
            "detail": "API and worker runner modes differ. Use the same environment.",
        }
    return {
        "mode": row["mode"],
        "ready": row["ready"],
        "detail": row["detail"],
        "last_seen": row["seen"],
    }


def owned(c, id, user):
    run = (
        c.execute(select(runs).where(runs.c.id == id, runs.c.user_id == user["id"]))
        .mappings()
        .first()
    )
    if not run:
        raise HTTPException(404, "Evaluation not found")
    return run


def trial_rows(c, id):
    return list(
        c.execute(
            select(trials).where(trials.c.run_id == id).order_by(trials.c.repeat, trials.c.task_id)
        ).mappings()
    )


def summary(run, rows):
    expected = len(json.loads(run["snapshot"])) * run["repeats"]
    passed = sum(t["passed"] for t in rows)
    total = sum(t["total"] for t in rows)
    latency = [
        t["generation_ms"] + t["execution_ms"]
        for t in rows
        if t["generation_ms"] is not None and t["execution_ms"] is not None
    ]
    costs = [Decimal(t["cost_usd"]) for t in rows if t["cost_usd"] is not None]
    return {
        k: run[k]
        for k in (
            "id",
            "name",
            "agent",
            "repeats",
            "suite_version",
            "suite_hash",
            "state",
            "created",
            "finished",
            "error",
            "cancel_requested",
        )
    } | {
        "completed_trials": len(rows),
        "expected_trials": expected,
        "passed": passed,
        "total": total,
        "score": round(100 * passed / total, 1) if total else None,
        "median_latency_ms": round(median(latency)) if latency else None,
        "cost_usd": str(sum(costs)) if len(costs) == expected else None,
        "failed_trials": sum(t["state"] == "failed" for t in rows),
    }


@app.post("/api/runs", status_code=201)
def create_run(data: RunInput, response: Response, user=Depends(current_user)):
    ids = sorted(set(data.task_ids))
    tasks = snapshot(ids)
    if len(ids) != len(data.task_ids) or len(tasks) != len(ids):
        raise HTTPException(422, "Choose unique tasks from this benchmark suite")
    agents = {a["id"]: a for a in available_agents()}
    if data.agent not in agents or not agents[data.agent]["available"]:
        raise HTTPException(422, "Choose an available agent")
    if data.agent == "provider" and config.RUNNER != "docker":
        raise HTTPException(422, "Model-generated code requires the Docker runner")
    payload = dict(name=data.name, agent=data.agent, task_ids=ids, repeats=data.repeats)
    request_hash = fingerprint(payload)
    with transaction() as c:
        c.execute(select(users.c.id).where(users.c.id == user["id"]).with_for_update()).one()
        existing = (
            c.execute(
                select(runs).where(
                    runs.c.user_id == user["id"], runs.c.idempotency_key == data.idempotency_key
                )
            )
            .mappings()
            .first()
        )
        if existing:
            if existing["request_hash"] != request_hash:
                raise HTTPException(409, "Idempotency key was used for another evaluation")
            response.status_code = 200
            return summary(existing, trial_rows(c, existing["id"]))
        count = c.execute(
            select(func.count())
            .select_from(runs)
            .where(runs.c.user_id == user["id"], runs.c.state.in_(["queued", "running"]))
        ).scalar_one()
        if count >= 10:
            raise HTTPException(429, "Finish or cancel active evaluations before adding more")
        row = dict(
            id=uuid.uuid4().hex,
            user_id=user["id"],
            name=data.name,
            agent=data.agent,
            repeats=data.repeats,
            suite_version=VERSION,
            suite_hash=fingerprint(tasks),
            snapshot=json.dumps(tasks),
            state="queued",
            created=now(),
            finished=None,
            cancel_requested=False,
            lease_token=None,
            lease_until=None,
            idempotency_key=data.idempotency_key,
            request_hash=request_hash,
            error=None,
        )
        try:
            with c.begin_nested():
                c.execute(insert(runs).values(**row))
        except IntegrityError:
            existing = (
                c.execute(
                    select(runs).where(
                        runs.c.user_id == user["id"], runs.c.idempotency_key == data.idempotency_key
                    )
                )
                .mappings()
                .one()
            )
            if existing["request_hash"] != request_hash:
                raise HTTPException(409, "Idempotency key was used for another evaluation")
            response.status_code = 200
            return summary(existing, trial_rows(c, existing["id"]))
        return summary(row, [])


@app.get("/api/runs")
def list_runs(page: int = 1, user=Depends(current_user)):
    page = max(1, page)
    with engine.connect() as c:
        count = c.execute(
            select(func.count()).select_from(runs).where(runs.c.user_id == user["id"])
        ).scalar_one()
        records = (
            c.execute(
                select(runs)
                .where(runs.c.user_id == user["id"])
                .order_by(runs.c.created.desc())
                .offset((page - 1) * 20)
                .limit(20)
            )
            .mappings()
            .all()
        )
        return {
            "items": [summary(r, trial_rows(c, r["id"])) for r in records],
            "total": count,
            "page": page,
            "size": 20,
        }


@app.get("/api/runs/{id}")
def get_run(id: str, user=Depends(current_user)):
    with engine.connect() as c:
        run = owned(c, id, user)
        rows = trial_rows(c, id)
        return summary(run, rows) | {
            "tasks": [public_task(t) for t in json.loads(run["snapshot"])],
            "trials": [dict(t) | {"cases": json.loads(t["cases"])} for t in rows],
        }


@app.post("/api/runs/{id}/cancel")
def cancel(id: str, user=Depends(current_user)):
    with transaction() as c:
        owned(c, id, user)
        c.execute(
            update(runs)
            .where(runs.c.id == id, runs.c.state.in_(["queued", "running"]))
            .values(
                cancel_requested=True,
                state="cancelled",
                finished=now(),
                lease_token=None,
                lease_until=None,
            )
        )
    return {"ok": True}


@app.get("/api/runs/{id}/export")
def export(id: str, format: str = "json", user=Depends(current_user)):
    report = get_run(id, user)
    if format == "json":
        return JSONResponse(
            report, headers={"Content-Disposition": f'attachment; filename="agentbench-{id}.json"'}
        )
    if format != "csv":
        raise HTTPException(422, "Choose json or csv")
    file = io.StringIO()
    fields = [
        "task_id",
        "repeat",
        "state",
        "passed",
        "total",
        "generation_ms",
        "execution_ms",
        "input_tokens",
        "output_tokens",
        "cost_usd",
        "model",
        "source_hash",
        "error",
    ]
    writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in report["trials"]:
        clean = {
            k: (
                "'" + v
                if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r"))
                else v
            )
            for k, v in row.items()
        }
        writer.writerow(clean)
    return Response(
        file.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="agentbench-{id}.csv"'},
    )


@app.get("/api/compare")
def compare(left: str, right: str, user=Depends(current_user)):
    with engine.connect() as c:
        a, b = owned(c, left, user), owned(c, right, user)
        if a["state"] != "completed" or b["state"] != "completed":
            raise HTTPException(409, "Both evaluations must be completed")
        if a["suite_hash"] != b["suite_hash"] or a["repeats"] != b["repeats"]:
            raise HTTPException(409, "Compare the same suite fingerprint and repeat count")
        return {"left": summary(a, trial_rows(c, left)), "right": summary(b, trial_rows(c, right))}


# Swagger's mutation operations use the same request guard as the browser.
base_openapi = app.openapi


def custom_openapi():
    schema = base_openapi()
    for path, verbs in schema.get("paths", {}).items():
        if path.startswith("/api/"):
            for method, operation in verbs.items():
                if method in ("post", "put", "patch", "delete"):
                    operation.setdefault("parameters", []).append(
                        {
                            "name": "X-AgentBench-Request",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "default": "browser"},
                        }
                    )
    return schema


app.openapi = custom_openapi
static = Path(__file__).resolve().parents[1] / "static"
if static.exists():
    app.mount("/", StaticFiles(directory=static, html=True), name="frontend")
