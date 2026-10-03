import json
import secrets
import time
import uuid
from sqlalchemy import select, update, and_, or_, insert
from sqlalchemy.exc import IntegrityError
from . import config
from .db import transaction, engine, runs, trials, now, worker_status
from .agents import generate, AgentError
from .runner import evaluate, RunnerError, readiness
from .security import digest


_last_heartbeat = 0


def heartbeat():
    global _last_heartbeat
    if now() - _last_heartbeat < 10:
        return
    status = readiness()
    with transaction() as c:
        values = dict(
            mode=status["mode"], ready=status["ready"], detail=status["detail"], seen=now()
        )
        changed = c.execute(
            update(worker_status).where(worker_status.c.id == "worker").values(**values)
        ).rowcount
        if not changed:
            try:
                with c.begin_nested():
                    c.execute(insert(worker_status).values(id="worker", **values))
            except IntegrityError:
                c.execute(
                    update(worker_status).where(worker_status.c.id == "worker").values(**values)
                )
    _last_heartbeat = now()


def claim():
    token = secrets.token_hex(16)
    with transaction() as c:
        eligible = and_(
            runs.c.cancel_requested.is_(False),
            or_(
                runs.c.state == "queued",
                and_(runs.c.state == "running", runs.c.lease_until < now()),
            ),
        )
        row = (
            c.execute(select(runs).where(eligible).order_by(runs.c.created).limit(1))
            .mappings()
            .first()
        )
        if not row:
            return None
        changed = c.execute(
            update(runs)
            .where(runs.c.id == row["id"], eligible)
            .values(state="running", lease_token=token, lease_until=now() + config.LEASE_SECONDS)
        ).rowcount
        if not changed:
            return None
        return dict(row) | {"lease_token": token, "state": "running"}


def active(run):
    with engine.connect() as c:
        row = (
            c.execute(
                select(runs.c.cancel_requested, runs.c.lease_token, runs.c.state).where(
                    runs.c.id == run["id"]
                )
            )
            .mappings()
            .first()
        )
    return (
        row
        and row["lease_token"] == run["lease_token"]
        and row["state"] == "running"
        and not row["cancel_requested"]
    )


def finish(run, state, error=None):
    with transaction() as c:
        c.execute(
            update(runs)
            .where(
                runs.c.id == run["id"],
                runs.c.lease_token == run["lease_token"],
                runs.c.state == "running",
            )
            .values(state=state, finished=now(), error=error, lease_token=None, lease_until=None)
        )


def process(run):
    status = readiness()
    if not status["ready"]:
        finish(run, "error", status["detail"])
        return
    tasks = json.loads(run["snapshot"])
    for repetition in range(1, run["repeats"] + 1):
        for task in tasks:
            heartbeat()
            if not active(run):
                finish(run, "cancelled")
                return
            with transaction() as c:
                # Renewal and result writes use the same lease fencing token.
                renewed = c.execute(
                    update(runs)
                    .where(
                        runs.c.id == run["id"],
                        runs.c.lease_token == run["lease_token"],
                        runs.c.state == "running",
                        runs.c.cancel_requested.is_(False),
                    )
                    .values(lease_until=now() + config.LEASE_SECONDS)
                ).rowcount
                if not renewed:
                    return
                existing = c.execute(
                    select(trials.c.id).where(
                        trials.c.run_id == run["id"],
                        trials.c.task_id == task["id"],
                        trials.c.repeat == repetition,
                    )
                ).first()
            if existing:
                continue
            data = dict(
                id=uuid.uuid4().hex,
                run_id=run["id"],
                task_id=task["id"],
                repeat=repetition,
                created=now(),
                passed=0,
                total=len(task["cases"]),
                cases="[]",
                source=None,
                source_hash=None,
                generation_ms=None,
                execution_ms=None,
                input_tokens=None,
                output_tokens=None,
                cost_usd=None,
                model=None,
                error=None,
            )
            try:
                gen = generate(run["agent"], task)
                data.update(
                    source=gen.source,
                    source_hash=digest(gen.source),
                    generation_ms=gen.elapsed_ms,
                    input_tokens=gen.input_tokens,
                    output_tokens=gen.output_tokens,
                    cost_usd=gen.cost_usd,
                    model=gen.model,
                )
                result = evaluate(gen.source, task, run["agent"])
                data.update(result)
                data["cases"] = json.dumps(data["cases"])
            except AgentError as e:
                data.update(state="failed", error=str(e))
            except RunnerError as e:
                finish(run, "error", str(e))
                return
            except Exception:
                finish(run, "error", "Worker failed unexpectedly; inspect server logs")
                raise
            with transaction() as c:
                # Conditional UPDATE serializes completion/cancellation against this write.
                held = c.execute(
                    update(runs)
                    .where(
                        runs.c.id == run["id"],
                        runs.c.lease_token == run["lease_token"],
                        runs.c.state == "running",
                        runs.c.cancel_requested.is_(False),
                    )
                    .values(lease_until=now() + config.LEASE_SECONDS)
                ).rowcount
                if held:
                    c.execute(insert(trials).values(**data))
            if not held:
                finish(run, "cancelled")
                return
    if active(run):
        finish(run, "completed")
    else:
        finish(run, "cancelled")


def tick():
    heartbeat()
    run = claim()
    if run:
        process(run)
    return bool(run)


if __name__ == "__main__":
    print("AgentBench worker started", flush=True)
    while True:
        try:
            if not tick():
                time.sleep(1)
        except Exception:
            import traceback

            traceback.print_exc()
            time.sleep(2)
