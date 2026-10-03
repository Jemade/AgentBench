import { useState, useEffect } from "react";
import { ChevronLeft, Download, ArrowUpRight } from "lucide-react";
import {
  api,
  errorMessage,
  type Catalog,
  type Detail,
  type Trial,
  type Task,
} from "../api";
import { ErrorBox, Status, Empty, Dialog, score, money, date } from "../ui";
import { PageHeading, agentName, Metric } from "../components";
export default function RunDetail({
  id,
  catalog,
  back,
}: {
  id: string;
  catalog: Catalog;
  back: () => void;
}) {
  const [data, setData] = useState<Detail | null>(null),
    [error, setError] = useState(""),
    [trial, setTrial] = useState<Trial | null>(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    const load = () =>
      api<Detail>("/runs/" + id)
        .then((r) => {
          if (active) {
            setData(r);
            setError("");
          }
        })
        .catch((e) => {
          if (active) setError(errorMessage(e));
        });
    load();
    const interval = setInterval(load, 1500);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [id]);
  async function cancel() {
    setBusy(true);
    try {
      await api("/runs/" + id + "/cancel", "POST");
      setData(await api<Detail>("/runs/" + id));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button className="back text-button" onClick={back}>
        <ChevronLeft size={15} />
        All evaluations
      </button>
      <ErrorBox text={error} />
      {!data ? (
        <p>Loading report…</p>
      ) : (
        <>
          <PageHeading
            label="EVALUATION REPORT"
            title={data.name}
            description={
              agentName(catalog, data.agent) +
              " · " +
              data.suite_version +
              " · " +
              data.repeats +
              " repeat" +
              (data.repeats > 1 ? "s" : "")
            }
          >
            <div className="actions">
              <a
                className="secondary"
                href={"/api/runs/" + id + "/export?format=json"}
              >
                <Download size={16} />
                JSON report
              </a>
              <a
                className="secondary"
                href={"/api/runs/" + id + "/export?format=csv"}
              >
                CSV
              </a>
            </div>
          </PageHeading>
          <div className="run-banner">
            <Status state={data.state} />
            <span>
              {data.completed_trials} of {data.expected_trials} trials recorded
            </span>
            <progress
              value={data.completed_trials}
              max={data.expected_trials}
              aria-label="Evaluation progress"
            />
            {["running", "queued"].includes(data.state) && (
              <button
                className="text-button danger"
                disabled={busy}
                onClick={cancel}
              >
                Cancel evaluation
              </button>
            )}
          </div>
          {data.error && <ErrorBox text={data.error} />}
          <div className="metric-grid">
            <Metric
              label={
                data.state === "completed"
                  ? "Test pass rate"
                  : "Partial test pass rate"
              }
              value={score(data.score)}
              note={data.passed + " of " + data.total + " recorded test cases"}
            />
            <Metric
              label="Median measured latency"
              value={
                data.median_latency_ms === null
                  ? "—"
                  : data.median_latency_ms + " ms"
              }
              note="Generation + execution time"
            />
            <Metric
              label="Estimated token cost"
              value={money(data.cost_usd)}
              note="Requires usage and configured prices"
            />
            <Metric
              label="Failed trials"
              value={String(data.failed_trials)}
              note="Generation or candidate execution errors"
            />
          </div>
          <section className="panel">
            <div className="panel-heading">
              <h2>Task results</h2>
              <span>
                {data.agent === "provider"
                  ? "Model-generated solutions"
                  : "Authored baseline solutions"}
              </span>
            </div>
            {data.trials.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Task</th>
                      <th>Repeat</th>
                      <th>Result</th>
                      <th>Passed</th>
                      <th>Generation</th>
                      <th>Execution</th>
                      <th>
                        <span className="sr-only">Inspect</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.trials.map((t) => (
                      <tr key={t.id}>
                        <td>
                          {data.tasks.find((x) => x.id === t.task_id)?.title}
                          <small>{t.model ?? "No model response"}</small>
                        </td>
                        <td>{t.repeat}</td>
                        <td>
                          <Status state={t.state} />
                        </td>
                        <td className="numeric">
                          {t.passed}/{t.total}
                        </td>
                        <td>
                          {t.generation_ms === null
                            ? "—"
                            : t.generation_ms + " ms"}
                        </td>
                        <td>
                          {t.execution_ms === null
                            ? "—"
                            : t.execution_ms + " ms"}
                        </td>
                        <td>
                          <button
                            className="text-button"
                            onClick={() => setTrial(t)}
                          >
                            Inspect
                            <ArrowUpRight size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <Empty
                title={
                  data.state === "queued"
                    ? "Waiting for the worker"
                    : "No recorded trials"
                }
              >
                The worker claims durable evaluations from the database. Check
                Environment if a run stays queued.
              </Empty>
            )}
          </section>
          <section className="panel fingerprint">
            <div>
              <h3>Reproducibility record</h3>
              <p>
                Suite fingerprint covers the exact task specifications, test
                fixtures, and baseline sources.
              </p>
              <code>{data.suite_hash}</code>
            </div>
            <div>
              <span>Created {date(data.created)}</span>
              {data.finished && <span>Finished {date(data.finished)}</span>}
            </div>
          </section>
          {trial && (
            <TrialDialog
              trial={trial}
              task={data.tasks.find((t) => t.id === trial.task_id)}
              close={() => setTrial(null)}
            />
          )}
        </>
      )}
    </>
  );
}
function TrialDialog({
  trial,
  task,
  close,
}: {
  trial: Trial;
  task?: Task;
  close: () => void;
}) {
  const [tab, setTab] = useState("tests");
  return (
    <Dialog title={task?.title ?? trial.task_id} close={close}>
      <div className="trial-summary">
        <Status state={trial.state} />
        <strong>
          {trial.passed}/{trial.total} cases passed
        </strong>
        <span>Repeat {trial.repeat}</span>
      </div>
      <ErrorBox text={trial.error ?? ""} />
      <div className="tabs">
        <button
          className={tab === "tests" ? "active" : ""}
          onClick={() => setTab("tests")}
        >
          Test cases
        </button>
        <button
          className={tab === "source" ? "active" : ""}
          onClick={() => setTab("source")}
        >
          Source code
        </button>
        <button
          className={tab === "usage" ? "active" : ""}
          onClick={() => setTab("usage")}
        >
          Usage & provenance
        </button>
      </div>
      {tab === "tests" && (
        <div className="case-list">
          {trial.cases.length ? (
            trial.cases.map((c) => (
              <div key={c.index} className="case">
                <div>
                  <strong>Case {c.index}</strong>
                  <Status state={c.passed ? "passed" : "failed"} />
                </div>
                {c.error ? (
                  <p>{c.error}</p>
                ) : (
                  <>
                    <span>Expected</span>
                    <pre>{JSON.stringify(c.expected, null, 2)}</pre>
                    <span>Actual</span>
                    <pre>{JSON.stringify(c.actual, null, 2)}</pre>
                    {c.mutated_input && (
                      <p className="danger">Input was mutated.</p>
                    )}
                  </>
                )}
              </div>
            ))
          ) : (
            <p>No individual case output was produced.</p>
          )}
        </div>
      )}
      {tab === "source" && (
        <>
          <p className="small-note">
            The exact solution evaluated in this trial.
          </p>
          <pre className="source">
            <code>{trial.source ?? "No source returned"}</code>
          </pre>
        </>
      )}
      {tab === "usage" && (
        <dl className="metadata">
          <dt>Model</dt>
          <dd>{trial.model ?? "Not reported"}</dd>
          <dt>Input tokens</dt>
          <dd>{trial.input_tokens ?? "Not reported"}</dd>
          <dt>Output tokens</dt>
          <dd>{trial.output_tokens ?? "Not reported"}</dd>
          <dt>Estimated cost</dt>
          <dd>{money(trial.cost_usd)}</dd>
          <dt>Source SHA-256</dt>
          <dd>
            <code>{trial.source_hash ?? "Not available"}</code>
          </dd>
        </dl>
      )}
    </Dialog>
  );
}
