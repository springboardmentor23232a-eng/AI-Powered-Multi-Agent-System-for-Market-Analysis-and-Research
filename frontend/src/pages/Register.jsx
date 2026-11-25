import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import AuthShell from "../components/AuthShell";
import PasswordInput from "../components/PasswordInput";

const LABELS = ["Too short", "Weak", "Okay", "Strong", "Very strong"];

function strength(p) {
  let s = 0;
  if (p.length >= 8) s++;
  if (/[A-Za-z]/.test(p) && /\d/.test(p)) s++;
  if (/[A-Z]/.test(p) && /[^A-Za-z0-9]/.test(p)) s++;
  if (p.length >= 12) s++;
  return s;
}

export default function Register() {
  const nav = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const level = strength(form.password);
  const mismatch = form.confirm_password && form.password !== form.confirm_password;
  const match = form.confirm_password && form.password === form.confirm_password;

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm_password) return setError("Passwords do not match.");
    setLoading(true);
    try {
      await api("/auth/register", { method: "POST", body: JSON.stringify(form) });
      nav("/login", { state: { message: `Account created. Welcome, ${form.full_name.split(" ")[0]}. Please sign in.` } });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Research stocks with a team of AI agents"
      footer={<>Already registered? <Link to="/login">Sign in</Link></>}
    >
      <form className="form" onSubmit={onSubmit}>
        {error && <div className="form-error" role="alert">{error}</div>}
        <div className="field">
          <label htmlFor="full_name">Full name</label>
          <input id="full_name" name="full_name" className="input" placeholder="Jane Doe"
            value={form.full_name} onChange={onChange} autoComplete="name" required minLength={2} />
        </div>
        <div className="field">
          <label htmlFor="email">Email address</label>
          <input id="email" name="email" type="email" className="input" placeholder="jane@example.com"
            value={form.email} onChange={onChange} autoComplete="email" required />
        </div>
        <div className="field">
          <label htmlFor="password">Password</label>
          <PasswordInput id="password" name="password" value={form.password} onChange={onChange}
            placeholder="At least 8 characters, with a letter and a number" autoComplete="new-password" />
          {form.password && (
            <>
              <div className="meter" aria-hidden="true">
                {[1, 2, 3, 4].map((n) => <i key={n} className={level >= n ? `l${level}` : ""} />)}
              </div>
              <span className="field-msg">{LABELS[level]}</span>
            </>
          )}
        </div>
        <div className="field">
          <label htmlFor="confirm_password">Confirm password</label>
          <PasswordInput id="confirm_password" name="confirm_password" value={form.confirm_password}
            onChange={onChange} placeholder="Re-enter your password" autoComplete="new-password" />
          {mismatch && <span className="field-msg bad">Passwords do not match yet.</span>}
          {match && <span className="field-msg good">Passwords match.</span>}
        </div>
        <button className="btn btn-primary" disabled={loading}>{loading ? "Creating account…" : "Create account"}</button>
      </form>
    </AuthShell>
  );
}
