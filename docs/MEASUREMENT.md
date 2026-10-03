# What the numbers mean

## Test pass rate

`100 × passed test cases / recorded test cases`. The full suite contains 36 test cases across six tasks. With two repeats, it contains 72 case executions. The UI labels unfinished evaluations as partial. A trial that cannot generate usable source or whose candidate crashes/times out records zero passes and the task's full test-case denominator.

This is a case-weighted score: the money task has eight cases and some tasks have five. It is not pass@k, a task-level success rate, or an unbiased estimate of broad software engineering capability. Repeats make additional requests but do not guarantee independent samples; reference baselines are deterministic.

A `completed` run means every planned trial has a record, including failed trials. A runner infrastructure failure produces run state `error` and is excluded from comparison; it is not scored as model incompetence. Cancelled/partial runs are also excluded.

## Latency

- Generation time: wall-clock time around the baseline lookup or provider request.
- Execution time: wall-clock time around runner setup, container launch and test execution, including startup overhead.
- Median measured latency: median of generation plus execution for trials with both timings available. It excludes generation failures without execution timing.

This is not provider-only latency or a production request SLA. Baselines usually generate in less than a millisecond and show 0 ms after rounding. Hardware, Docker cold starts and network conditions affect timings. Trials run serially within a run.

## Tokens and cost

Tokens are reported by the configured provider; they are not estimated from character count. Unknown usage stays null. Configured USD rates per million input/output tokens determine estimated cost using decimal arithmetic:

`(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`

A run-level cost is shown only when every planned trial has a known cost. This estimate excludes taxes, caching differences, provider surcharges and retried requests lost before persistence. Baselines show “Not reported”, rather than claiming API billing. Prices are supplied by the operator; AgentBench does not fetch live pricing.

## Comparison controls

Comparisons require both runs to be completed, have the exact same task snapshot SHA-256, and use the same repeat count. The fingerprint includes task IDs, prompts, starter files, case fixtures, and both authored baseline sources. Runs created after any suite change are intentionally incompatible, even if their displayed version name is unchanged. Increment VERSION when publishing a new suite.

The scorer compares outputs, top-level return type and input mutation. It is designed for normal candidate correctness, not adversarial grader manipulation. Candidate code shares its container with the test harness and may inspect public fixtures. A hostile candidate can attack measurement integrity; do not use this release as a high-stakes hiring assessment.

## Evidence retained

Every trial retains exact source, source hash, case results, model identifier, usage, timing and error classification. JSON includes the full report; CSV includes summary rows and escapes formula-leading strings. Downloaded reports can explain a score without trusting a screenshot alone.
