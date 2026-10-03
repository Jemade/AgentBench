import { useState, useEffect } from "react";
import { ArrowUpRight } from "lucide-react";
import { api, errorMessage, type RunPage, type Run, type Catalog } from "./api";
import { Status, date, score } from "./ui";
export function useRuns(page: number, refresh = 0) {
  const [data, setData] = useState<RunPage | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    const load = () =>
      api<RunPage>("/runs?page=" + page)
        .then((r) => {
          if (alive) {
            setData(r);
            setError("");
          }
        })
        .catch((e) => {
          if (alive) setError(errorMessage(e));
        });
    load();
    const timer = setInterval(load, 2500);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [page, refresh]);
  return { data, error };
}
export function agentName(catalog: Catalog, id: string) {
  return catalog.agents.find((a) => a.id === id)?.name ?? id;
}
export function PageHeading({
  label,
  title,
  description,
  children,
}: {
  label: string;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <span className="eyebrow">{label}</span>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {children}
    </div>
  );
}
export function RunTable({
  runs,
  catalog,
  open,
}: {
  runs: Run[];
  catalog: Catalog;
  open: (id: string) => void;
}) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Evaluation</th>
            <th>Agent</th>
            <th>Status</th>
            <th>Pass rate</th>
            <th>Trials</th>
            <th>Created</th>
            <th>
              <span className="sr-only">Open</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr key={r.id}>
              <td>
                <button className="text-button" onClick={() => open(r.id)}>
                  {r.name}
                </button>
                <small>{r.suite_version}</small>
              </td>
              <td>
                {agentName(catalog, r.agent)}
                <small>
                  {r.agent === "provider" ? "Model run" : "Authored baseline"}
                </small>
              </td>
              <td>
                <Status state={r.state} />
              </td>
              <td className="numeric">
                {score(r.score)}
                {r.state !== "completed" && r.score !== null && (
                  <small>Partial</small>
                )}
              </td>
              <td className="numeric">
                {r.completed_trials}/{r.expected_trials}
              </td>
              <td>{date(r.created)}</td>
              <td>
                <button
                  className="icon-button"
                  aria-label={"Open " + r.name}
                  onClick={() => open(r.id)}
                >
                  <ArrowUpRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}
