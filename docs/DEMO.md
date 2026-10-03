# Three-minute demonstration

1. Sign in and open Task library. Explain why exact money, deduplication and nested redaction are useful engineering checks.
2. Create **Reference control** using the reference baseline, all six tasks and one repeat. Watch recorded trial progress. Explain that results come from running authored code, not a simulated AI score.
3. Open the report. Inspect the source and a passing case. Show the suite fingerprint and JSON report download.
4. Create **Naive control** with the same six tasks/repeat count. Inspect a failed merge or redaction case and its actual versus expected output.
5. Open Compare runs. Select both controls and compare case pass rate and measured latency. State that baseline fixtures are not model comparisons and that latency includes process/container startup.
6. Create a one-task subset run. Attempt to compare it against the full suite and show the compatibility rejection.
7. Open Environment. Show the worker heartbeat and Docker/trusted-local boundary. Explain how to configure a model provider without sharing credentials with candidate containers.

For an interview, also demonstrate cancellation and a worker restart: queue a run, stop the worker, restart it, and explain how accepted work survives. A killed running worker can be reclaimed after its 180-second lease; already-recorded trials are retained.

Do not claim the reference baseline proves AI performance. A real provider run requires your own credentials and Docker isolation. Capture a short narrated recording after you can independently explain the scoring and recovery code.
