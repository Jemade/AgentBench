# AgentBench

[![Verify AgentBench](https://github.com/Jemade/AgentBench/actions/workflows/ci.yml/badge.svg)](https://github.com/Jemade/AgentBench/actions/workflows/ci.yml)

[Hosted demo](https://agentbench-ycv7.onrender.com) · Account sign-in required. The current free demo uses temporary SQLite storage; data can reset when Render restarts the instance.

An independent evaluation workbench for single-file Python coding agents. Run a versioned task suite, inspect the generated source and each test case, export evidence, and compare compatible evaluations.

![AgentBench workspace](docs/screenshots/workspace.png)

## Hosted demo access

- Application: [https://agentbench-ycv7.onrender.com](https://agentbench-ycv7.onrender.com)
- Health endpoint: [`/api/health`](https://agentbench-ycv7.onrender.com/api/health)
- Sign-in email for the configured administrator: `mapasurejayden@gmail.com`
- Administrator password: supplied privately to the account owner. It is stored in the Render service's `ADMIN_PASSWORD` environment variable and is not published in this repository.
- Recruiter or collaborator access: request credentials privately from the project owner.

The hosted interface and health endpoint were verified on 3 October 2026. The current free deployment uses temporary SQLite storage, so application data can reset on instance replacement or redeployment. Persistent PostgreSQL wiring is pending.

The hosted worker evaluates the authored reference and naive baselines. Provider-generated code evaluation requires a separate Docker worker host.

## What works

- Six authored Python tasks covering algorithms, money parsing, event deduplication, retry policy, nested redaction, and pagination.
- A reference baseline and an intentionally naive baseline, both clearly labelled as authored fixtures.
- An optional OpenAI-compatible Chat Completions adapter that generates a fresh Python solution per trial.
- Real execution and test scoring, exact suite/source fingerprints, immutable run snapshots, repeat counts, generation/execution latency, provider-reported token usage and optional cost estimates.
- Durable database queue, atomic worker claims, lease fencing, expired-run recovery, resumable recorded trials, cancellation and idempotent submission.
- Private account-scoped evaluation history, expiring HTTP-only sessions, password hashing, sign-in throttling and browser mutation guards.
- JSON/CSV downloads and controlled comparisons that reject different task subsets, suite fingerprints and repeat counts.
- A hand-coded responsive React/TypeScript interface, original SVG identity, restrained forest/amber colours, and no gradients or glow effects.
- SQLite development, PostgreSQL support, schema migrations, Docker configuration and automated backend/browser/sandbox checks.

## Evaluation scope

This release evaluates **one generated Python source file per task**, not repository-wide agents with tool-use loops. The tasks are small and public. A score describes this exact suite; it is not a general intelligence ranking, a research benchmark claim, or evidence of customer adoption.

Baseline results come from actually executing authored solutions. They are not simulated model scores. The model adapter is available only when you supply your own server credentials and use the Docker runner. No provider key is bundled, and screenshots use the free baseline workflow. See [measurement](docs/MEASUREMENT.md) and [validation](docs/VALIDATION.md).

## Deploy to Render

[Deploy to Render](https://render.com/deploy?repo=https://github.com/Jemade/AgentBench)

The Blueprint starts the interface, API, and demonstration worker. Supply a dedicated PostgreSQL database URL and initial account credentials. See [Render deployment](docs/RENDER.md) for startup, persistence, service-plan limits, and verification.

The hosted worker executes authored baselines. Live model evaluation requires a separate Docker worker host.

## Quick start: free baseline workflow

Requirements: Python 3.12 and Node.js 24. From a fresh checkout:

```bash
git clone https://github.com/Jemade/AgentBench.git
cd AgentBench
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd frontend
npm ci
npm run build
cd ..
cp .env.example .env
```

Edit `.env` with your own email and a unique password of at least 12 characters. For this **authored-baseline-only** demo, set:

```dotenv
RUNNER=trusted-local
ALLOW_TRUSTED_LOCAL=true
```

Load your trusted environment file in Bash and create the database/account:

```bash
set -a
. ./.env
set +a
cd backend
alembic upgrade head
python -m app.seed
uvicorn app.main:app --port 8100
```

In a second terminal, activate the same environment, load the same `.env`, enter `backend`, and run:

```bash
python -m app.worker
```

Open **http://localhost:8100**, sign in, and create a reference evaluation. Run the naive baseline with the same tasks/repeat count, inspect its failed cases, and open Compare runs. Nothing is pre-filled with invented evaluation totals. `/docs` contains the API reference.

The local runner refuses provider-generated source and any source that differs from the exact authored baseline fixture. This mode is a convenient demo, not a sandbox for external code.

## Evaluate a model with Docker isolation

Install Docker Engine/Desktop on the worker host. From the repository root:

```bash
docker build -f Dockerfile.sandbox -t agentbench-sandbox:1 .
```

Set these in `.env`, then restart both API and worker with the same environment:

```dotenv
RUNNER=docker
ALLOW_TRUSTED_LOCAL=false
PROVIDER_BASE_URL=https://YOUR_PROVIDER/v1
PROVIDER_MODEL=YOUR_MODEL
PROVIDER_API_KEY=YOUR_SERVER_KEY
# Optional USD prices per million tokens, supplied by you:
INPUT_PRICE_PER_MILLION=
OUTPUT_PRICE_PER_MILLION=
```

The adapter appends `/chat/completions` to the configured base URL. It sends only the task prompt, starter and first public example, not the reference solution. Select the provider agent in New evaluation. Each repeat makes a new provider request and may incur charges. Missing usage/prices remain unknown, not zero. Configure a model compatible with `temperature: 0`, `max_tokens`, and Chat Completions; provider-specific adapters are separate extensions.

Each candidate runs with network disabled, a read-only filesystem, no capabilities, a non-root UID, bounded memory/CPU/process count, and a deadline. Candidate containers receive no provider credential. The worker controls Docker and belongs on a dedicated trusted host. See [execution boundaries](docs/SECURITY.md).

## PostgreSQL API deployment

Compose starts PostgreSQL and the API. The evaluation worker runs on the Docker host so the API container never needs the Docker socket.

Set a random URL-safe `POSTGRES_PASSWORD` in `.env`, then:

```bash
docker compose up --build -d --wait
set -a
. ./.env
set +a
docker compose exec -e ADMIN_EMAIL -e ADMIN_PASSWORD -e ADMIN_NAME api python -m app.seed
```

In the host worker's shell, with the virtual environment and `.env` loaded:

```bash
export DATABASE_URL="postgresql+psycopg://bench:${POSTGRES_PASSWORD}@127.0.0.1:5433/agentbench"
cd backend
python -m app.worker
```

API and PostgreSQL ports bind to localhost. Set up HTTPS and `SECURE_COOKIE=true` before exposing the service. Use a process supervisor for the worker; instructions are in [operations](docs/OPERATIONS.md). Docker image inspection and heartbeat readiness are performed by the worker, so the Environment screen reports the host worker's status.

## Validation commands

```bash
cd backend
pytest -q
ruff check app tests migrations
```

With the sandbox image built and Docker running:

```bash
TEST_DOCKER=true pytest -q -k docker_runner
```

The Docker test executes actual external source, checks UID/credential absence/network restriction, and verifies deadline enforcement. PostgreSQL tests require an isolated test database:

```bash
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@localhost:5432/agentbench_test pytest -q
```

**The tests drop and recreate their schema. Never use a production database.**

Browser tests, with the baseline API and worker running and matching `ADMIN_EMAIL`/`ADMIN_PASSWORD`:

```bash
cd frontend
npx playwright install chromium
npm run test:e2e
```

GitHub Actions checks SQLite, PostgreSQL, migrations, browser workflows, Docker sandbox behaviour, production image build and Compose health.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Metric definitions and limits](docs/MEASUREMENT.md)
- [Security and execution boundaries](docs/SECURITY.md)
- [Three-minute demonstration](docs/DEMO.md)
- [API examples](docs/API.md)
- [Deployment and recovery](docs/OPERATIONS.md)
- [Validation record](docs/VALIDATION.md)
- [Resume and interview evidence](docs/RESUME.md)
- [Interface decisions](docs/DESIGN.md)

```text
backend/app/           API, fixtures, model adapter, execution runner, worker
backend/migrations/    Frozen initial schema and Alembic environment
backend/tests/         Correctness, account isolation, concurrency, sandbox checks
frontend/src/          React/TypeScript workspace and report screens
frontend/tests/        Browser workflow checks
docs/                  Architecture, operations, evidence and actual screenshots
.github/workflows/     Continuous verification
Dockerfile.sandbox     Candidate execution image
Dockerfile             API and built frontend image
compose.yaml           PostgreSQL and API deployment
```

## Product extensions

Custom task authoring/version publishing, repository-wide agent adapters, isolated VM execution, task-level statistical estimates on larger suites, additional provider protocols, team roles, retention policies and provider budget enforcement. These are future extensions rather than represented features.

## License

MIT. See [LICENSE](LICENSE).
