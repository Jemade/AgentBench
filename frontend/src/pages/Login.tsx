import { useState, type FormEvent } from "react";
import { Check, ArrowRight } from "lucide-react";
import { api, errorMessage, type User } from "../api";
import { Logo, ErrorBox } from "../ui";
export default function Login({ onLogin }: { onLogin: (u: User) => void }) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      onLogin(await api<User>("/auth/login", "POST", { email, password }));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="login">
      <section className="login-story">
        <Logo />
        <div>
          <span className="eyebrow">THE EVALUATION WORKSPACE</span>
          <h1>
            Put the code
            <br />
            to the test.
          </h1>
          <p>
            Measure how coding agents handle real Python tasks. Keep the source,
            the evidence, and the tradeoffs in one place.
          </p>
          <div className="login-note">
            <Check size={18} /> Repeatable tasks <Check size={18} /> Actual test
            results
          </div>
        </div>
        <small>A portfolio product by Jayden Mapasure.</small>
      </section>
      <section className="login-form">
        <form onSubmit={submit}>
          <span className="eyebrow">WELCOME BACK</span>
          <h2>Open your workspace</h2>
          <p>Sign in with the account created during setup.</p>
          <ErrorBox text={error} />
          <label>
            Email address
            <input
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <label>
            Password
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
            <ArrowRight size={17} />
          </button>
          <small className="help">
            First time here? Create your account with the documented setup
            command.
          </small>
        </form>
      </section>
    </div>
  );
}
