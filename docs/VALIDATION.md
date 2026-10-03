# Validation record

Initial implementation checked on 3 October 2026. Results reflect actual checks, not assumed production behaviour.

| Check | Result |
| --- | --- |
| Backend suite on SQLite | 24 passed locally and in GitHub Actions; Docker test excluded from this job |
| Backend suite on PostgreSQL 17 | 24 passed in GitHub Actions; Docker test excluded from this job |
| Docker runner integration | Passed actual external-source scoring, non-root UID, credential absence, network restriction and deadline checks |
| Browser workflows | All 3 passed locally and in GitHub Actions |
| TypeScript checks and production frontend build | Passed locally and in GitHub Actions |
| Ruff checks | Passed |
| Initial migrations and schema comparison | Passed on clean SQLite locally and PostgreSQL in GitHub Actions |
| Production API Docker image | Built successfully in GitHub Actions |
| Compose PostgreSQL/API deployment | Started successfully; HTTP database health check passed |
| Screenshot capture | No browser runtime errors observed |
| Published source | All 65 initial file blob hashes matched the tested local source |
| Reference full-suite execution | 36/36 cases per repeat; source hashes recorded |
| Naive full-suite execution | 19/36 cases passed (52.8%); actual failures recorded |

[Verified final code CI run](https://github.com/Jemade/AgentBench/actions/runs/37151337799) covers code commit `29d3d860991705887e60ccbab5fc723fda81e770`. Later documentation-only changes do not trigger repeated tests.

The browser checks cover baseline execution/source inspection/exports/comparison, mobile navigation/dialogs/page width, and incompatible task-set rejection. A Docker worker host remains a separate supervised process in deployment; the Compose health test verifies the API and database, while the sandbox integration test verifies candidate execution.

## Coverage

Tests cover immutable task snapshots, idempotency/conflicts, concurrent submissions, single worker ownership, expired lease recovery, skipping recorded trials, queued/in-flight cancellation, provider errors, runner errors, comparison compatibility, account isolation, session/logout/guards, sign-in throttling, local-runner refusal, decimal cost accounting, provider response parsing, CSV formula escaping, backlog limits and pagination.

Concurrent claim testing caught a SQLite read-snapshot upgrade failure. Mutating transactions now reserve SQLite's writer lock before reading; PostgreSQL uses conditional writes and account-row locks. This is exercised by regression tests.

## Remaining limits

- Live external-provider evaluation requires credentials not provided during implementation. The adapter contract is tested using a mock HTTP transport.
- This is a small public suite with authored fixtures. No anti-cheating assurance, generalized model ranking or production load claim.
- Independent security review, full accessibility audit, distributed-worker load testing and public HTTPS deployment remain separate work.

## Render startup verification

Checked on 3 October 2026: 29 backend tests passed locally on SQLite, including PostgreSQL URL normalization, provider port binding, child-process cleanup after component failure, and graceful platform shutdown. Ruff checks passed. All three browser workflows passed using `python -m app.hosted`; restarting the service retained the account without duplicate seeding. AgentBench's Docker-specific integration test was skipped locally because Docker was unavailable.

The hosted startup was checked locally. A live Render deployment is not claimed by these results. The Blueprint requires a dedicated PostgreSQL connection and initial account credentials.
