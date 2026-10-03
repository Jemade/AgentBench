import { useState } from "react";
import { Code2, ArrowUpRight } from "lucide-react";
import { type Catalog, type Task } from "../api";
import { Dialog } from "../ui";
import { PageHeading } from "../components";
export default function Library({ catalog }: { catalog: Catalog }) {
  const [task, setTask] = useState<Task | null>(null);
  return (
    <>
      <PageHeading
        label="VERSIONED BENCHMARK"
        title="Know what you are measuring."
        description="A compact, inspectable Python suite. Task specifications stay fixed within each recorded evaluation."
      />
      <div className="library-grid">
        {catalog.tasks.map((t) => (
          <section className="panel task-card" key={t.id}>
            <div className="task-meta">
              <span>{t.category}</span>
              <Code2 size={18} />
            </div>
            <h2>{t.title}</h2>
            <p>{t.prompt}</p>
            <div className="task-bottom">
              <span>
                {t.difficulty} · {t.test_count} cases
              </span>
              <button className="text-button" onClick={() => setTask(t)}>
                View task
                <ArrowUpRight size={16} />
              </button>
            </div>
          </section>
        ))}
      </div>
      {task && (
        <Dialog title={task.title} close={() => setTask(null)}>
          <p>{task.prompt}</p>
          <h3>Starter file</h3>
          <pre className="source">{task.starter}</pre>
          <h3>Public example</h3>
          <pre>{JSON.stringify(task.examples, null, 2)}</pre>
          <p className="small-note">
            Additional cases are held by the runner. Fixtures are public in this
            repository; this is an inspectable benchmark, not an anti-cheating
            assessment.
          </p>
        </Dialog>
      )}
    </>
  );
}
