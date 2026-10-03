import { Plus, ArrowRight, FlaskConical } from "lucide-react";
import { type Catalog } from "../api";
import { ErrorBox, Empty } from "../ui";
import { useRuns, PageHeading, RunTable, Metric } from "../components";
import { type Tab } from "../App";
export default function Workspace({
  catalog,
  refresh,
  open,
  create,
  navigate,
}: {
  catalog: Catalog;
  refresh: number;
  open: (id: string) => void;
  create: () => void;
  navigate: (tab: Tab) => void;
}) {
  const { data, error } = useRuns(1, refresh);
  const completed = data?.items.filter((r) => r.state === "completed") ?? [];
  const active =
    data?.items.filter((r) => ["running", "queued"].includes(r.state)).length ??
    0;
  return (
    <>
      <PageHeading
        label="YOUR WORKSPACE"
        title="Good code needs evidence."
        description="Run a benchmark, inspect the failures, and compare what changed."
      >
        <button className="primary" onClick={create}>
          <Plus size={17} />
          New evaluation
        </button>
      </PageHeading>
      <ErrorBox text={error} />
      <div className="metric-grid">
        <Metric
          label="Total evaluations"
          value={String(data?.total ?? 0)}
          note="All recorded runs"
        />
        <Metric
          label="Completed on this page"
          value={String(completed.length)}
          note="Latest 20 evaluations"
        />
        <Metric
          label="Active on this page"
          value={String(active)}
          note="Queued or running"
        />
        <Metric
          label="Benchmark tasks"
          value={String(catalog.tasks.length)}
          note="Python core suite v1.0"
        />
      </div>
      <div className="workspace-grid">
        <section className="panel">
          <div className="panel-heading">
            <h2>Recent evaluations</h2>
            <button
              className="text-button subtle"
              onClick={() => navigate("evaluations")}
            >
              View all
              <ArrowRight size={15} />
            </button>
          </div>
          {!data ? (
            <p className="pad">Loading evaluations…</p>
          ) : data.items.length ? (
            <RunTable
              runs={data.items.slice(0, 6)}
              catalog={catalog}
              open={open}
            />
          ) : (
            <Empty title="Your first evaluation starts here">
              Choose the reference or naive baseline to try the full workflow
              without a model API key.
            </Empty>
          )}
        </section>
        <section className="panel starter">
          <span className="eyebrow">START WITH A CONTROL</span>
          <div className="line-icon">
            <FlaskConical size={25} />
          </div>
          <h2>A benchmark you can inspect.</h2>
          <p>
            The reference baseline should pass every test. The naive baseline
            demonstrates where edge cases break.
          </p>
          <button className="secondary" onClick={create}>
            Run a baseline
            <ArrowRight size={16} />
          </button>
          <div className="small-note">
            Baselines are authored fixtures, not AI performance claims.
          </div>
        </section>
      </div>
      <section className="panel suite-strip">
        <div>
          <span className="eyebrow">PYTHON CORE · 1.0.0</span>
          <h2>Six tasks. Different kinds of correctness.</h2>
          <p>
            Algorithms, exact money, events, retry policy, redaction, and
            pagination.
          </p>
        </div>
        <button className="secondary" onClick={() => navigate("library")}>
          Explore the task library
          <ArrowRight size={16} />
        </button>
      </section>
    </>
  );
}
