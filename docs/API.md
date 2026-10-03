# API workflow

All examples assume a locally running product. `/docs` provides the schema. The browser and Swagger mutation operations use `X-AgentBench-Request: browser`.

```bash
curl -c /tmp/agentbench-cookie.txt -H 'Content-Type: application/json' \
  -H 'X-AgentBench-Request: browser' \
  -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD"}' \
  http://localhost:8100/api/auth/login
```

Use placeholders in published instructions; avoid putting real credentials in shell history. The cookie file contains a session secret and should be deleted after the demonstration.

```bash
curl -b /tmp/agentbench-cookie.txt http://localhost:8100/api/catalog
curl -b /tmp/agentbench-cookie.txt http://localhost:8100/api/runner
curl -b /tmp/agentbench-cookie.txt -H 'Content-Type: application/json' \
  -H 'X-AgentBench-Request: browser' \
  -d '{"name":"Reference control","agent":"reference","task_ids":["merge-intervals","money-to-cents","stable-dedup","retry-policy","redact-secrets","page-window"],"repeats":1,"idempotency_key":"unique-request-001"}' \
  http://localhost:8100/api/runs
```

The response includes the evaluation ID. Reuse the same idempotency key only for an identical request; changed content returns 409.

| Endpoint | Purpose |
| --- | --- |
| GET /api/health | Database readiness; not a worker health guarantee |
| POST /api/auth/login | Create a browser session |
| POST /api/auth/logout | Revoke current session |
| GET /api/me | Current account |
| GET /api/catalog | Public task specifications and agent availability |
| GET /api/runner | Recent worker readiness heartbeat |
| POST /api/runs | Queue an evaluation |
| GET /api/runs?page=1 | Account history, 20 records per page |
| GET /api/runs/{id} | Report, source files and test evidence |
| POST /api/runs/{id}/cancel | Cancel queued/running work |
| GET /api/runs/{id}/export?format=json | Complete JSON evidence |
| GET /api/runs/{id}/export?format=csv | Trial summary CSV |
| GET /api/compare?left={id}&right={id} | Compatible completed comparison |

Invalid inputs return 422, unknown/not-owned runs return 404, missing/expired sessions return 401, missing mutation guards return 403, conflicting comparisons/keys return 409, and backlog/sign-in limits return 429. Runner infrastructure errors appear in a report's `error` state. Candidate/provider trial errors count as zero-pass trials in a completed evaluation.
