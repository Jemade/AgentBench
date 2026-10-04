# Engineering notes: AgentBench

## Purpose and scope

Coding-agent evaluation with deterministic verifiers. This repository is an independently inspectable project; customer adoption, production scale and commercial readiness are not claimed without evidence.

## Request and data flow

Run request → selected task/provider → isolated candidate execution → verifier cases → stored results and comparison UI.

## Implementation map

Primary implementation and review locations: `backend/app/main.py`, `backend/app/runner.py`, `backend/app/agents.py`. Dependency manifests and `.github/workflows/` specify installation and automated checks. Read the source for exact contracts and data models.

## Local verification

From `backend` in a configured virtual environment:

```sh
pip install -r requirements-dev.txt
ruff check app tests migrations
pytest -q
```

From the repository root, run `python scripts/repository_check.py` for documentation and tracked-file checks. CI evidence is available in [GitHub Actions](https://github.com/Jemade/AgentBench/actions). Green hygiene checks alone do not mean application tests passed.

## Decisions and boundaries

Hosted trusted-local mode accepts authored baselines only. External candidate code requires the Docker sandbox. Free hosted SQLite data may reset.

Use the README's current run instructions and configuration examples. Keep provider credentials outside Git. Test changes against controlled fixtures before enabling external services. Health checks indicate process/service state, not end-to-end correctness.

## Review and operational evidence

[Review checklist](REVIEW_CHECKLIST.md) distinguishes repository evidence from outstanding human and deployment validation. Report measured workload, environment and method with any performance claim. Document incident fixes through reproducible issues and regression tests; do not invent user counts or peer reviews.

## Reuse and licensing

The root LICENSE describes the repository license. Third-party dependencies and assets retain their respective licenses.
