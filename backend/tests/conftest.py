# ruff: noqa: E402
import os
import tempfile
import uuid
from pathlib import Path
import pytest

temp = tempfile.TemporaryDirectory(prefix="agentbench-tests-")
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "sqlite:///" + str(Path(temp.name) / "test.db")
)
os.environ["RUNNER"] = "trusted-local"
os.environ["ALLOW_TRUSTED_LOCAL"] = "true"
from app.db import metadata, engine, users
from app.security import password_hash
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def database():
    metadata.drop_all(engine)
    metadata.create_all(engine)
    with engine.begin() as c:
        c.execute(
            users.insert().values(
                id="owner",
                email="jayden@example.com",
                name="Jayden Mapasure",
                password=password_hash("Local-demo-pass-2026"),
            )
        )
        c.execute(
            users.insert().values(
                id="other",
                email="other@example.com",
                name="Other User",
                password=password_hash("Other-user-pass-2026"),
            )
        )
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.headers["X-AgentBench-Request"] = "browser"
        assert (
            c.post(
                "/api/auth/login",
                json={"email": "jayden@example.com", "password": "Local-demo-pass-2026"},
            ).status_code
            == 200
        )
        yield c


def payload(**changes):
    return (
        dict(
            name="Baseline evaluation",
            agent="reference",
            task_ids=[
                "merge-intervals",
                "money-to-cents",
                "stable-dedup",
                "retry-policy",
                "redact-secrets",
                "page-window",
            ],
            repeats=1,
            idempotency_key=uuid.uuid4().hex,
        )
        | changes
    )
