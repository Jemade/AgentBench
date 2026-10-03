import { useState, type FormEvent } from "react";
import { GitCompareArrows, ArrowUpRight } from "lucide-react";
import { api, errorMessage, type Catalog, type Run } from "../api";
import { ErrorBox, Empty, score, money } from "../ui";
import { useRuns, PageHeading, agentName } from "../components";
export default function Compare({
  catalog,
  open,
}: {
  catalog: Catalog;
  open: (id: string) => void;
}) {
  const { data, error: loadError } = useRuns(1);
  const [left, setLeft] = useState(""),
    [right, setRight] = useState(""),
    [result, setResult] = useState<{ left: Run; right: Run } | null>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const choices = data?.items.filter((r) => r.state === "completed") ?? [];
  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);
    setBusy(true);
    try {
      setResult(await api("/compare?left=" + left + "&right=" + right));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageHeading
        label="CONTROLLED COMPARISON"
        title="Compare like with like."
        description="Only completed runs with identical tasks, suite fingerprints, and repeat counts can be compared."
      />
      <ErrorBox text={loadError || error} />
      <section className="panel compare-picker">
        <form onSubmit={submit}>
          <label>
            Left evaluation
            <select
              required
              value={left}
              onChange={(e) => setLeft(e.target.value)}
            >
              <option value="">Choose a completed run</option>
              {choices.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <GitCompareArrows size={22} />
          <label>
            Right evaluation
            <select
              required
              value={right}
              onChange={(e) => setRight(e.target.value)}
            >
              <option value="">Choose a completed run</option>
              {choices.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </label>
          <button
            className="primary"
            disabled={busy || !left || !right || left === right}
          >
            {busy ? "Comparing…" : "Compare"}
          </button>
        </form>
        <p className="small-note">
          Choose from the latest 20 evaluations. Different task subsets are
          deliberately rejected.
        </p>
      </section>
      {result ? (
        <div className="compare-grid">
          {[result.left, result.right].map((r) => (
            <section className="panel comparison" key={r.id}>
              <span className="eyebrow">{agentName(catalog, r.agent)}</span>
              <h2>{r.name}</h2>
              <div className="score-big">{score(r.score)}</div>
              <span>Test pass rate</span>
              <progress
                max={100}
                value={r.score ?? 0}
                aria-label={r.name + " pass rate"}
              />
              <dl>
                <dt>Tests passed</dt>
                <dd>
                  {r.passed}/{r.total}
                </dd>
                <dt>Median latency</dt>
                <dd>{r.median_latency_ms} ms</dd>
                <dt>Estimated cost</dt>
                <dd>{money(r.cost_usd)}</dd>
                <dt>Failed trials</dt>
                <dd>{r.failed_trials}</dd>
              </dl>
              <button className="text-button" onClick={() => open(r.id)}>
                Open full report
                <ArrowUpRight size={16} />
              </button>
            </section>
          ))}
          <p className="small-note">
            These small authored tasks measure this suite only. A higher pass
            rate is not a general ranking of agent capability.
          </p>
        </div>
      ) : (
        <section className="panel">
          <Empty title="Two runs, one benchmark">
            Run both baselines on the full suite, then compare their recorded
            test results.
          </Empty>
        </section>
      )}
    </>
  );
}
