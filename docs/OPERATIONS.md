# Deployment and recovery

## Process layout

Use PostgreSQL for deployment and run the API plus a separately supervised worker. The API never launches candidate containers. The host worker needs Python dependencies, Docker CLI/daemon access, the built sandbox image, and the same database/provider/runner configuration as the API.

Do not expose the service with the demonstration credentials. The account seed requires explicit credentials and does not overwrite an existing account. Put a reverse proxy with HTTPS in front of port 8100 and set `SECURE_COOKIE=true`. Keep PostgreSQL and API bind addresses private. Candidate containers receive no provider credentials.

Example systemd service, replacing paths/user/environment file with your installation:

```ini
[Unit]
Description=AgentBench evaluation worker
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
User=YOUR_DEDICATED_WORKER_USER
WorkingDirectory=/opt/agentbench/backend
EnvironmentFile=/etc/agentbench/worker.env
ExecStart=/opt/agentbench/.venv/bin/python -m app.worker
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

The environment file must contain the host-reachable database URL, runner mode/image, provider configuration and optional prices. Limit its permissions to the service administrator and worker user. Docker group access is a privileged trust boundary; a dedicated worker host is recommended over sharing a general workstation with arbitrary candidates.

## Health

`GET /api/health` confirms database connectivity. It does not prove execution progress. `GET /api/runner` returns the most recent worker readiness heartbeat; older than 90 seconds becomes unavailable. Monitor queued age, oldest running lease, runner errors, container cleanup, disk space, database size and provider error counts.

Run states `completed`, `cancelled`, and `error` are terminal. To retry an infrastructure-error evaluation after fixing Docker, create a new run with the same task selection/repeat count; comparisons preserve the distinction between the original interrupted run and new evidence.

## Worker interruptions

If a worker process stops, accepted queued runs remain in the database. A running run can be reclaimed after its 180-second lease expires. Already-persisted task/repetition results are skipped. An in-flight generation lost before recording can run again and be billed twice. Do not claim exactly-once billing.

User cancellation marks the run cancelled and clears the lease token. The current bounded operation may finish, but the fenced result write will be discarded. A dead worker can leave a Docker container until it exits or is manually removed; the normal finally block performs cleanup. List `agentbench-` containers on the worker host after unexpected process termination and remove only confirmed stale candidate containers.

## Database changes and backups

Run `alembic upgrade head` before starting upgraded services. The initial migration is frozen. A future revision should explicitly declare schema changes; do not edit revision 0001 after deployment. `alembic check` verifies model/schema alignment. Downgrading the initial revision deletes every product table and must never be used casually.

For PostgreSQL, use a dedicated backup connection and `pg_dump`:

```bash
pg_dump --dbname="$BACKUP_DATABASE_URL" --format=custom --file=agentbench-backup.dump
```

`BACKUP_DATABASE_URL` should use PostgreSQL's ordinary `postgresql://` syntax, not SQLAlchemy's `postgresql+psycopg://` driver syntax. Store backups privately; they contain source files, account hashes, session hashes and reports. Restore into a separate empty database and verify row counts/reports before switching services.

For local SQLite, stop API and worker before copying the database, or use SQLite's online backup API. Copying only the main file during active WAL writes can lose recent records. Compose `down` retains the database volume; `down -v` deliberately deletes it.

## Resource and spending limits

Each run is capped at six unique tasks and three repeats; each account can have ten queued/running evaluations. These bound one request but do not enforce a monetary budget. A provider run may make up to eighteen API calls. Configure provider-side spending limits. Cost estimates require supplied prices and reported token counts and are not a billing ledger.

There is no retention scheduler. Apply an explicit archive/deletion policy before collecting substantial user data. Use tested migrations for deletes and preserve evidence needed for a reproducible comparison.
