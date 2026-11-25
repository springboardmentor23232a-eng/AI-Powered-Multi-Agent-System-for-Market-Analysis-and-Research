import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";
import AuthShell from "../components/AuthShell";
import PasswordInput from "../components/PasswordInput";

export default function Login() {
  const nav = useNavigate();
  const { state } = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api("/auth/login", { method: "POST", body: JSON.stringify(form) });
      nav("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to your research workspace"
      footer={<>New here? <Link to="/register">Create an account</Link></>}
    >
      <form className="form" onSubmit={onSubmit}>
        {state?.message && <div className="form-ok">{state.message}</div>}
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="field">
          <label htmlFor="email">Email address</label>
          <input id="email" name="email" type="email" className="input" placeholder="jane@example.com"
            value={form.email} onChange={onChange} autoComplete="email" required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <PasswordInput id="password" name="password" value={form.password} onChange={onChange}
            placeholder="Your password" autoComplete="current-password" />
        </div>
        <button className="btn btn-primary" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</button>
      </form>
    </AuthShell>
  );
}
