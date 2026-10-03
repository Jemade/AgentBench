import { useState, useEffect } from "react";
import {
  LayoutDashboard,
  FlaskConical,
  GitCompareArrows,
  BookOpen,
  Settings,
  LogOut,
  Menu,
} from "lucide-react";
import { api, errorMessage, type User, type Catalog } from "./api";
import { Logo, ErrorBox } from "./ui";
import Login from "./pages/Login";
import Workspace from "./pages/Workspace";
import Evaluations from "./pages/Evaluations";
import NewRun from "./pages/NewRun";
import RunDetail from "./pages/RunDetail";
import Compare from "./pages/Compare";
import Library from "./pages/Library";
import Environment from "./pages/Environment";
export type Tab =
  "workspace" | "evaluations" | "compare" | "library" | "settings";
const nav = [
  { id: "workspace" as Tab, label: "Workspace", icon: LayoutDashboard },
  { id: "evaluations" as Tab, label: "Evaluations", icon: FlaskConical },
  { id: "compare" as Tab, label: "Compare runs", icon: GitCompareArrows },
  { id: "library" as Tab, label: "Task library", icon: BookOpen },
  { id: "settings" as Tab, label: "Environment", icon: Settings },
];

export default function App() {
  const [user, setUser] = useState<User | null>(null),
    [loading, setLoading] = useState(true),
    [tab, setTab] = useState<Tab>("workspace"),
    [catalog, setCatalog] = useState<Catalog | null>(null),
    [newRun, setNewRun] = useState(false),
    [selected, setSelected] = useState<string | null>(null),
    [refresh, setRefresh] = useState(0),
    [mobile, setMobile] = useState(false),
    [error, setError] = useState("");
  useEffect(() => {
    api<User>("/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setLoading(false));
    const expire = () => {
      setUser(null);
      setCatalog(null);
      setSelected(null);
    };
    window.addEventListener("agentbench:expired", expire);
    return () => window.removeEventListener("agentbench:expired", expire);
  }, []);
  useEffect(() => {
    if (user)
      api<Catalog>("/catalog")
        .then(setCatalog)
        .catch((e) => setError(errorMessage(e)));
  }, [user]);
  async function logout() {
    try {
      await api("/auth/logout", "POST");
      setUser(null);
      setSelected(null);
      setCatalog(null);
    } catch (e) {
      setError(errorMessage(e));
    }
  }
  function open(id: string) {
    setSelected(id);
    setTab("evaluations");
  }
  if (loading) return <div className="loading">Loading workspace…</div>;
  if (!user) return <Login onLogin={setUser} />;
  const title = selected
    ? "Evaluation report"
    : nav.find((n) => n.id === tab)?.label;
  return (
    <div className="app">
      <aside className={mobile ? "sidebar open" : "sidebar"}>
        <div className="brand">
          <Logo />
          <span className="workspace-name">Evaluation studio</span>
        </div>
        <nav aria-label="Main navigation">
          {nav.map((n) => (
            <button
              key={n.id}
              className={tab === n.id ? "active" : ""}
              onClick={() => {
                setTab(n.id);
                setSelected(null);
                setMobile(false);
              }}
            >
              <n.icon size={18} />
              {n.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="avatar">JM</div>
          <div>
            <strong>{user.name}</strong>
            <small>Personal workspace</small>
          </div>
          <button
            className="icon-button"
            aria-label="Sign out"
            onClick={logout}
          >
            <LogOut size={17} />
          </button>
        </div>
      </aside>
      {mobile && (
        <button
          className="scrim"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        />
      )}
      <div className="main">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="mobile-toggle icon-button"
              aria-label="Open navigation"
              onClick={() => setMobile(!mobile)}
            >
              <Menu size={21} />
            </button>
            <span>Studio</span>
            <span className="slash">/</span>
            <strong>{title}</strong>
          </div>
          <span className="version">Python suite · v1.0</span>
        </header>
        <main>
          <ErrorBox text={error} />
          {catalog && (
            <>
              {selected ? (
                <RunDetail
                  id={selected}
                  catalog={catalog}
                  back={() => {
                    setSelected(null);
                    setRefresh((x) => x + 1);
                  }}
                />
              ) : (
                <>
                  {tab === "workspace" && (
                    <Workspace
                      catalog={catalog}
                      refresh={refresh}
                      open={open}
                      create={() => setNewRun(true)}
                      navigate={setTab}
                    />
                  )}
                  {tab === "evaluations" && (
                    <Evaluations
                      refresh={refresh}
                      catalog={catalog}
                      open={open}
                      create={() => setNewRun(true)}
                    />
                  )}
                  {tab === "compare" && (
                    <Compare catalog={catalog} open={open} />
                  )}
                  {tab === "library" && <Library catalog={catalog} />}
                  {tab === "settings" && <Environment catalog={catalog} />}
                </>
              )}
              {newRun && (
                <NewRun
                  catalog={catalog}
                  close={() => setNewRun(false)}
                  created={(id) => {
                    setNewRun(false);
                    setRefresh((x) => x + 1);
                    open(id);
                  }}
                />
              )}
            </>
          )}
        </main>
        <footer>AgentBench · Versioned tasks. Inspectable results.</footer>
      </div>
    </div>
  );
}
