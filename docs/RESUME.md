# Resume and interview evidence

**AgentBench | Python, FastAPI, PostgreSQL, React/TypeScript, Docker, GitHub Actions**

Repository: https://github.com/Jemade/AgentBench

- Built a Python coding-agent evaluation workbench with versioned task snapshots, generated-source provenance, per-case scoring, repeat evaluations, and JSON/CSV evidence exports.
- Implemented a durable evaluation queue with idempotent acceptance, atomic leases, resumable trial persistence, fenced cancellation, and account-scoped access.
- Added an optional model-provider adapter and Docker candidate execution with network/resource restrictions, plus automated correctness, browser and sandbox verification.

Use these bullets after you have run the application, reviewed the implementation and can independently explain/modify it. State that the public demonstration uses authored baselines and a small inspectable suite. Do not claim a real provider evaluation until you have configured and run one. Do not claim research-level model rankings, enterprise adoption, pass@k statistics or autonomous repository engineering.

## Show these engineering decisions

1. Why immutable snapshots and source hashes matter when tasks evolve.
2. Why comparison rejects incompatible task subsets and repetition counts.
3. Why missing token cost is null rather than zero.
4. Why a worker lease needs a fencing token for completion and cancellation.
5. Why database acceptance and execution are separate operations.
6. Why a failed candidate is scored while broken infrastructure is classified separately.
7. Why generated code needs an execution boundary and why containers still have limits.
8. Why repeated API generation can be billed twice after a worker crash.

The initial implementation used coding assistance. Record your own changes, investigations, task additions and provider experiments as you develop ownership. Follow the disclosure and AI-use rules of each hiring assessment; a portfolio project does not authorize AI assistance during a prohibited test.
