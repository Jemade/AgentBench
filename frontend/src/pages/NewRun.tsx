import { useState, type FormEvent } from "react";
import { ArrowRight } from "lucide-react";
import { api, errorMessage, type Catalog, type Run } from "../api";
import { Dialog, ErrorBox } from "../ui";
export default function NewRun({
  catalog,
  close,
  created,
}: {
  catalog: Catalog;
  close: () => void;
  created: (id: string) => void;
}) {
  const [name, setName] = useState(""),
    [agent, setAgent] = useState("reference"),
    [tasks, setTasks] = useState(catalog.tasks.map((t) => t.id)),
    [repeats, setRepeats] = useState(1),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [key] = useState(crypto.randomUUID());
  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const r = await api<Run>("/runs", "POST", {
        name,
        agent,
        task_ids: tasks,
        repeats,
        idempotency_key: key,
      });
      created(r.id);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog title="New evaluation" close={close}>
      <form onSubmit={submit}>
        <p className="dialog-intro">
          Choose an agent and an immutable set of Python tasks. Each repeat
          generates and tests a fresh solution.
        </p>
        <ErrorBox text={error} />
        <label>
          Evaluation name
          <input
            autoFocus
            required
            maxLength={100}
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Reference baseline · Python core"
          />
        </label>
        <div className="form-row">
          <label>
            Agent
            <select value={agent} onChange={(e) => setAgent(e.target.value)}>
              {catalog.agents.map((a) => (
                <option
                  key={a.id}
                  value={a.id}
                  disabled={
                    !a.available ||
                    (a.id === "provider" && catalog.runner_mode !== "docker")
                  }
                >
                  {a.name}
                  {!a.available ? " · Not configured" : ""}
                </option>
              ))}
            </select>
          </label>
          <label>
            Repeats per task
            <select
              value={repeats}
              onChange={(e) => setRepeats(Number(e.target.value))}
            >
              {[1, 2, 3].map((n) => (
                <option key={n}>{n}</option>
              ))}
            </select>
          </label>
        </div>
        <p className="small-note">
          {catalog.agents.find((a) => a.id === agent)?.description}
        </p>
        <fieldset>
          <legend>Benchmark tasks</legend>
          <div className="task-checks">
            {catalog.tasks.map((t) => (
              <label key={t.id}>
                <input
                  type="checkbox"
                  checked={tasks.includes(t.id)}
                  onChange={() =>
                    setTasks(
                      tasks.includes(t.id)
                        ? tasks.filter((id) => id !== t.id)
                        : [...tasks, t.id],
                    )
                  }
                />
                <span>
                  {t.title}
                  <small>
                    {t.category} · {t.test_count} cases
                  </small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        <div className="dialog-footer">
          <span>{tasks.length * repeats} planned trials</span>
          <button className="primary" disabled={busy || tasks.length === 0}>
            {busy ? "Creating…" : "Start evaluation"}
            <ArrowRight size={16} />
          </button>
        </div>
      </form>
    </Dialog>
  );
}
