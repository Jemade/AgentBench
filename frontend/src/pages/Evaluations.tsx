import { useState } from "react";
import { Plus, ChevronLeft, ChevronRight } from "lucide-react";
import { type Catalog } from "../api";
import { ErrorBox, Empty } from "../ui";
import { useRuns, PageHeading, RunTable } from "../components";
export default function Evaluations({
  refresh,
  catalog,
  open,
  create,
}: {
  refresh: number;
  catalog: Catalog;
  open: (id: string) => void;
  create: () => void;
}) {
  const [page, setPage] = useState(1);
  const { data, error } = useRuns(page, refresh);
  return (
    <>
      <PageHeading
        label="EVALUATION HISTORY"
        title="Every run, with its evidence."
        description="Completed runs retain the exact benchmark snapshot and generated source."
      >
        <button className="primary" onClick={create}>
          <Plus size={17} />
          New evaluation
        </button>
      </PageHeading>
      <ErrorBox text={error} />
      <section className="panel">
        {!data ? (
          <p className="pad">Loading…</p>
        ) : data.items.length ? (
          <>
            <RunTable runs={data.items} catalog={catalog} open={open} />
            <div className="pager">
              <span>
                {data.total} evaluations · Page {page}
              </span>
              <button
                aria-label="Previous page"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                <ChevronLeft size={17} />
              </button>
              <button
                aria-label="Next page"
                disabled={page * 20 >= data.total}
                onClick={() => setPage(page + 1)}
              >
                <ChevronRight size={17} />
              </button>
            </div>
          </>
        ) : (
          <Empty title="No evaluations yet">
            Create an evaluation to build a record of actual results.
          </Empty>
        )}
      </section>
    </>
  );
}
