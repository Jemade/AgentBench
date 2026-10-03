"""Initial AgentBench schema. Frozen for repeatable migrations."""

from alembic import op
from sqlalchemy import (
    MetaData,
    Table,
    Column,
    String,
    Integer,
    Float,
    Text,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)

metadata = MetaData()
users = Table(
    "users",
    metadata,
    Column("id", String, primary_key=True),
    Column("email", String, unique=True, nullable=False),
    Column("name", String, nullable=False),
    Column("password", Text, nullable=False),
)
sessions = Table(
    "sessions",
    metadata,
    Column("token", String, primary_key=True),
    Column("user_id", String, ForeignKey("users.id"), nullable=False),
    Column("expires", Float, nullable=False),
)
throttles = Table(
    "throttles",
    metadata,
    Column("key", String, primary_key=True),
    Column("count", Integer, nullable=False),
    Column("until", Float, nullable=False),
)
runs = Table(
    "runs",
    metadata,
    Column("id", String, primary_key=True),
    Column("user_id", String, ForeignKey("users.id"), nullable=False),
    Column("name", String, nullable=False),
    Column("agent", String, nullable=False),
    Column("repeats", Integer, nullable=False),
    Column("suite_version", String, nullable=False),
    Column("suite_hash", String, nullable=False),
    Column("snapshot", Text, nullable=False),
    Column("state", String, nullable=False),
    Column("created", Float, nullable=False),
    Column("finished", Float),
    Column("cancel_requested", Boolean, nullable=False, default=False),
    Column("lease_token", String),
    Column("lease_until", Float),
    Column("idempotency_key", String, nullable=False),
    Column("request_hash", String, nullable=False),
    Column("error", Text),
    UniqueConstraint("user_id", "idempotency_key"),
)
trials = Table(
    "trials",
    metadata,
    Column("id", String, primary_key=True),
    Column("run_id", String, ForeignKey("runs.id"), nullable=False),
    Column("task_id", String, nullable=False),
    Column("repeat", Integer, nullable=False),
    Column("state", String, nullable=False),
    Column("passed", Integer, nullable=False),
    Column("total", Integer, nullable=False),
    Column("generation_ms", Integer),
    Column("execution_ms", Integer),
    Column("input_tokens", Integer),
    Column("output_tokens", Integer),
    Column("cost_usd", String),
    Column("model", String),
    Column("source", Text),
    Column("source_hash", String),
    Column("cases", Text, nullable=False),
    Column("error", Text),
    Column("created", Float, nullable=False),
    UniqueConstraint("run_id", "task_id", "repeat"),
)


worker_status = Table(
    "worker_status",
    metadata,
    Column("id", String, primary_key=True),
    Column("mode", String, nullable=False),
    Column("ready", Boolean, nullable=False),
    Column("detail", Text, nullable=False),
    Column("seen", Float, nullable=False),
)


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    metadata.create_all(op.get_bind())


def downgrade():
    metadata.drop_all(op.get_bind())
