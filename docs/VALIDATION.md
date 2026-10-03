# Validation record

Initial implementation checked on 3 October 2026. Results reflect actual checks, not assumed production behaviour.

| Check | Result |
| --- | --- |
| Backend suite on local SQLite | 24 passed; Docker integration test skipped because Docker is unavailable locally |
| TypeScript checks and production frontend build | Passed |
| Ruff checks | Passed |
| Reference full-suite execution | 36/36 cases per repeat; source hashes recorded |
| Naive full-suite execution | Actual failed edge cases recorded |

Local browser checks passed for baseline execution/source inspection/exports/comparison, mobile navigation/dialogs/page width, and incompatible task-set rejection. Screenshot capture reported no browser runtime errors. A clean SQLite migration and schema comparison passed. GitHub Actions results are added after their runs complete. The configured workflow covers SQLite/PostgreSQL, migrations, Docker execution restrictions/deadline, production API image build, Compose health and browser workflows.

## Coverage

Tests cover immutable task snapshots, idempotency/conflicts, concurrent submissions, single worker ownership, expired lease recovery, skipping recorded trials, queued/in-flight cancellation, provider errors, runner errors, comparison compatibility, account isolation, session/logout/guards, sign-in throttling, local-runner refusal, decimal cost accounting, provider response parsing, CSV formula escaping, backlog limits and pagination.

Concurrent claim testing caught a SQLite read-snapshot upgrade failure. Mutating transactions now reserve SQLite's writer lock before reading; PostgreSQL uses conditional writes and account-row locks. This is exercised by regression tests.

## Remaining limits

- Live external-provider evaluation requires credentials not provided during implementation. The adapter contract is tested using a mock HTTP transport.
- This is a small public suite with authored fixtures. No anti-cheating assurance, generalized model ranking or production load claim.
- Independent security review, full accessibility audit, distributed-worker load testing and public HTTPS deployment remain separate work.
