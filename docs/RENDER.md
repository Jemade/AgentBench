# Deploy AgentBench to Render

The repository includes a Docker web-service Blueprint in `render.yaml`.

[Deploy to Render](https://render.com/deploy?repo=https://github.com/Jemade/AgentBench)

## Deployment inputs

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | PostgreSQL connection URL for a dedicated AgentBench database |
| `ADMIN_EMAIL` | Initial account email |
| `ADMIN_PASSWORD` | Unique password of at least 12 characters |

The Blueprint enables secure cookies and runs `python -m app.hosted`. PostgreSQL URLs from Render are normalized to the installed psycopg driver. Use a separate database from BridgeSync because their table names overlap.

Startup applies migrations, creates the account if absent, and supervises the API and baseline worker. No evaluation results are pre-seeded. The API binds Render's `PORT`; a component exit stops the service so Render can restart it.

## Hosted baseline demo

The embedded worker uses `RUNNER=trusted-local` and `ALLOW_TRUSTED_LOCAL=true`. It executes only the exact authored reference and naive fixtures. Provider-generated source remains refused by this runner.

This deployment supports task browsing, baseline evaluation, case inspection, evidence export, comparison, cancellation, and persistent run history. It is not a hosted execution sandbox for external code.

## Live provider evaluation

Run a dedicated worker on a trusted Docker host and connect it to the same PostgreSQL database:

1. Set `HOSTED_WORKER=false` on Render to disable its embedded worker.
2. Set `RUNNER=docker` and `ALLOW_TRUSTED_LOCAL=false` in both environments.
3. Configure matching provider/model settings for the API and worker.
4. Build `Dockerfile.sandbox` on the worker host and start `python -m app.worker`.
5. Verify the worker heartbeat and sandbox readiness in the Environment screen.

Render's support for Docker-built web services does not supply the application's required worker-host Docker daemon. See [execution boundaries](SECURITY.md) and [operations](OPERATIONS.md). Keep provider keys in secret environment variables.

## Storage and service plan

The Blueprint uses a free web service and prompts for an external PostgreSQL URL. It does not create paid resources automatically. PostgreSQL retains accounts and run history across service restarts.

Free Render web services sleep after inactivity. Evaluation work pauses while the service is stopped; durable queue records remain in PostgreSQL and resume when a worker starts again. Use an appropriate paid always-on service for continuous execution after reviewing current pricing.

## Verify after deployment

1. Open `/api/health` and sign in at the service URL.
2. Confirm the baseline worker is ready.
3. Run reference and naive evaluations with matching tasks and repeat counts.
4. Inspect failed cases, compare runs, and download evidence.
5. Redeploy and confirm PostgreSQL retains run history.

## Reference

- [Render Docker services](https://render.com/docs/docker)
- [Render Blueprint specification](https://render.com/docs/blueprint-spec)
- [Render free-service limits](https://render.com/docs/free)
