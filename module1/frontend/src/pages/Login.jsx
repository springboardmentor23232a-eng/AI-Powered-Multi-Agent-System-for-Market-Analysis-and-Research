import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../AuthContext.jsx";
import AuthLayout, { Alert, Field } from "../components/AuthLayout.jsx";
import SocialButtons from "../components/SocialButtons.jsx";

export default function Login() {
  const { login, sessionNotice } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [params] = useSearchParams();
  const [error, setError] = useState(params.get("oauth_error") || "");  // set when Google/Apple sign-in fails or is cancelled
  const [busy, setBusy] = useState(false);

  async function submit(ev) {
    ev.preventDefault();
    setError("");
    if (!form.email.trim() || !form.password) return setError("Please enter your email and password.");
    setBusy(true);
    try {
      await login(form.email.trim(), form.password);
      nav("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message);  // e.g. "Invalid email or password."
    } finally { setBusy(false); }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Sign in to your research workspace"
      footer={<>New here? <Link className="font-medium text-brand-600" to="/register">Create an account</Link></>}>
      <SocialButtons />
      <form onSubmit={submit} className="mt-4 space-y-4" noValidate>
        {sessionNotice && !error && <Alert kind="warn">{sessionNotice}</Alert>}
        {error && <Alert>{error}</Alert>}
        <Field label="Email Address" name="email" type="email" autoComplete="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Field label="Password" name="password" type="password" autoComplete="current-password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Login"}</button>
      </form>
    </AuthLayout>
  );
}
