import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api.js";
import AuthLayout, { Alert, Field } from "../components/AuthLayout.jsx";
import SocialButtons from "../components/SocialButtons.jsx";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validate(f) {
  const e = {};
  if (f.full_name.trim().length < 2) e.full_name = "Please enter your full name.";
  if (!EMAIL_RE.test(f.email.trim())) e.email = "Enter a valid email address.";
  const p = f.password;
  if (p.length < 8) e.password = "Password must be at least 8 characters.";
  else if (!/[a-z]/.test(p) || !/[A-Z]/.test(p) || !/\d/.test(p)) e.password = "Use upper and lower case letters and a digit.";
  if (f.confirm_password !== p) e.confirm_password = "Passwords do not match.";
  return e;
}

export default function Register() {
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);
  const set = (k) => (ev) => setForm({ ...form, [k]: ev.target.value });

  async function submit(ev) {
    ev.preventDefault();
    setServerError("");
    const e = validate(form);
    setErrors(e);
    if (Object.keys(e).length) return;
    setBusy(true);
    try {
      await api("/auth/register", { method: "POST", body: form, auth: false });
      setDone(true);
    } catch (err) {
      setErrors(err.errors || {});
      setServerError(err.message);
    } finally { setBusy(false); }
  }

  if (done) {
    return (
      <AuthLayout title="You're all set" subtitle="Your account has been created.">
        <Alert kind="success">Registration successful! You can now sign in.</Alert>
        <Link to="/login" className="btn-primary mt-4 w-full">Go to sign in</Link>
      </AuthLayout>
    );
  }
  return (
    <AuthLayout title="Create your account" subtitle="Multi-Agent Stock Research Analyst"
      footer={<>Already registered? <Link className="font-medium text-brand-600" to="/login">Sign in</Link></>}>
      <SocialButtons />
      <form onSubmit={submit} className="mt-4 space-y-4" noValidate>
        {serverError && <Alert>{serverError}</Alert>}
        <Field label="Full Name" name="full_name" autoComplete="name" value={form.full_name} onChange={set("full_name")} error={errors.full_name} />
        <Field label="Email Address" name="email" type="email" autoComplete="email" value={form.email} onChange={set("email")} error={errors.email} />
        <Field label="Password" name="password" type="password" autoComplete="new-password" value={form.password} onChange={set("password")} error={errors.password} />
        <Field label="Confirm Password" name="confirm_password" type="password" autoComplete="new-password" value={form.confirm_password} onChange={set("confirm_password")} error={errors.confirm_password} />
        <p className="text-xs text-slate-500">At least 8 characters with upper-case, lower-case and a number. Passwords are never stored — only a secure hash.</p>
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Creating account…" : "Register"}</button>
      </form>
    </AuthLayout>
  );
}
