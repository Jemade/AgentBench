import { useEffect, useRef, type ReactNode } from "react";
import { X, FlaskConical } from "lucide-react";
export function Logo() {
  return (
    <span className="identity">
      <img src="/logo.svg" alt="" width="30" height="30" />
      <span>AgentBench</span>
    </span>
  );
}
export function Status({ state }: { state: string }) {
  return (
    <span className={"status " + state}>
      {state === "error"
        ? "Runner error"
        : state.charAt(0).toUpperCase() + state.slice(1)}
    </span>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <FlaskConical size={26} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function ErrorBox({ text }: { text: string }) {
  return text ? (
    <div className="error" role="alert">
      {text}
    </div>
  ) : null;
}
export function Dialog({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: ReactNode;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    ref.current?.showModal();
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
      aria-label={title}
    >
      <div className="dialog-title">
        <h2>{title}</h2>
        <button
          className="icon-button"
          aria-label="Close dialog"
          onClick={close}
        >
          <X size={20} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function date(value: number) {
  return new Date(value * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
export function score(value: number | null) {
  return value === null ? "—" : value.toFixed(1) + "%";
}
export function money(value: string | null) {
  return value === null ? "Not reported" : "$" + Number(value).toFixed(6);
}
