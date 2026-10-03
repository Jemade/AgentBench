import { useState, useEffect } from "react";
import { Activity, ArrowUpRight } from "lucide-react";
import { api, errorMessage, type Catalog } from "../api";
import { ErrorBox, Status } from "../ui";
import { PageHeading } from "../components";
export default function Environment({ catalog }: { catalog: Catalog }) {
  const [runner, setRunner] = useState<{
      mode: string;
      ready: boolean;
      detail: string;
    } | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api<{ mode: string; ready: boolean; detail: string }>("/runner")
      .then(setRunner)
      .catch((e) => setError(errorMessage(e)));
  }, []);
  return (
    <>
      <PageHeading
        label="WORKSPACE ENVIRONMENT"
        title="An explicit execution boundary."
        description="Provider credentials stay on the server. Generated code executes only in the Docker runner."
      />
      <ErrorBox text={error} />
      <section className="panel environment">
        <div className="panel-heading">
          <h2>Execution runner</h2>
          <Activity size={18} />
        </div>
        <div className="environment-row">
          <div>
            <strong>{runner?.mode ?? catalog.runner_mode}</strong>
            <p>{runner?.detail ?? "Checking runner availability…"}</p>
          </div>
          {runner && <Status state={runner.ready ? "ready" : "unavailable"} />}
        </div>
        <p className="small-note">
          Readiness checks the configured runner image, not the worker
          heartbeat. Queued evaluations need a running worker process.
        </p>
        {catalog.runner_mode === "trusted-local" && (
          <div className="notice">
            Demo mode executes only the exact authored baseline fixtures.
            External model source is refused.
          </div>
        )}
      </section>
      <section className="panel environment">
        <div className="panel-heading">
          <h2>Agents</h2>
          <span>Server configuration</span>
        </div>
        {catalog.agents.map((a) => (
          <div className="environment-row" key={a.id}>
            <div>
              <strong>{a.name}</strong>
              <span className="tag">{a.kind}</span>
              <p>{a.description}</p>
            </div>
            <Status state={a.available ? "ready" : "unavailable"} />
          </div>
        ))}
      </section>
      <section className="panel environment">
        <h2>Connect a model provider</h2>
        <p>
          Configure PROVIDER_BASE_URL, PROVIDER_MODEL, and PROVIDER_API_KEY in
          the server environment, then restart the API and worker. The adapter
          calls the Chat Completions-compatible endpoint.
        </p>
        <p>
          Optional input/output prices per million tokens produce a cost
          estimate when usage is reported. Missing usage or prices remain “Not
          reported”.
        </p>
        <a
          className="text-button"
          href="/docs"
          target="_blank"
          rel="noreferrer"
        >
          Open the API reference
          <ArrowUpRight size={16} />
        </a>
      </section>
    </>
  );
}
