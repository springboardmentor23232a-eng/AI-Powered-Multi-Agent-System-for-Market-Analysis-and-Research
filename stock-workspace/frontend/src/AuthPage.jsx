import React, { useState } from "react";
import { api } from "./api.js";
import { Spinner, useToast } from "./ui.jsx";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function strength(p) {
  let s = 0;
  if (p.length >= 8) s++;
  if (/[A-Za-z]/.test(p) && /\d/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p) || p.length >= 12) s++;
  return s; // 0..3
}

function Field({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-rose-600">{error}</span>}
    </label>
  );
}

export default function AuthPage({ onLogin, dark, toggleTheme }) {
  const toast = useToast();
  const [mode, setMode] = useState("login");
  const [f, setF] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [touched, setTouched] = useState({});
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const reg = mode === "register";

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const blur = (k) => () => setTouched({ ...touched, [k]: true });

  const errs = {};
  if (reg && f.full_name.trim().length < 2) errs.full_name = "Enter your full name";
  if (!EMAIL_RE.test(f.email)) errs.email = "Enter a valid email address";
  if (reg && (f.password.length < 8 || !/[A-Za-z]/.test(f.password) || !/\d/.test(f.password))) errs.password = "Use 8+ characters with letters and numbers";
  if (!reg && !f.password) errs.password = "Enter your password";
  if (reg && f.confirm_password !== f.password) errs.confirm_password = "Passwords do not match";
  const shown = (k) => (touched[k] ? errs[k] : undefined);

  const switchMode = (m) => { setMode(m); setError(""); setTouched({}); };

  const submit = async (e) => {
    e.preventDefault();
    setTouched({ full_name: true, email: true, password: true, confirm_password: true });
    if (Object.keys(errs).length) return;
    setBusy(true); setError("");
    try {
      if (reg) {
        await api.register(f);
        toast("Registration successful! Please sign in.");
        setF({ ...f, password: "", confirm_password: "" });
        switchMode("login");
      } else {
        onLogin(await api.login({ email: f.email, password: f.password }));
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const s = strength(f.password);
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-100 via-slate-50 to-sky-100 p-4 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950">
      <button onClick={toggleTheme} className="btn-ghost fixed right-4 top-4">{dark ? "☀️ Light" : "🌙 Dark"}</button>
      <div className="animate-pop w-full max-w-md">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-600 text-2xl text-white">📈</div>
          <h1 className="text-2xl font-bold">Stock Research Analyst</h1>
          <p className="text-sm text-slate-500">Your personal multi-agent research workspace</p>
        </div>
        <div className="card">
          <div className="mb-5 grid grid-cols-2 rounded-xl bg-slate-100 p-1 text-sm dark:bg-slate-800">
            {[["login", "Sign in"], ["register", "Create account"]].map(([id, label]) => (
              <button key={id} onClick={() => switchMode(id)} className={`rounded-lg py-2 font-medium transition ${mode === id ? "bg-white shadow dark:bg-slate-700" : "text-slate-500"}`}>{label}</button>
            ))}
          </div>
          <form onSubmit={submit} className="space-y-4" noValidate>
            {reg && (
              <Field label="Full name" error={shown("full_name")}>
                <input className="input" value={f.full_name} onChange={set("full_name")} onBlur={blur("full_name")} autoComplete="name" />
              </Field>
            )}
            <Field label="Email address" error={shown("email")}>
              <input className="input" type="email" value={f.email} onChange={set("email")} onBlur={blur("email")} autoComplete="email" />
            </Field>
            <Field label="Password" error={shown("password")}>
              <div className="relative">
                <input className="input pr-16" type={show ? "text" : "password"} value={f.password} onChange={set("password")} onBlur={blur("password")} autoComplete={reg ? "new-password" : "current-password"} />
                <button type="button" onClick={() => setShow(!show)} className="absolute right-3 top-2 text-xs text-indigo-600">{show ? "Hide" : "Show"}</button>
              </div>
              {reg && f.password && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex flex-1 gap-1">
                    {[1, 2, 3].map((i) => <div key={i} className={`h-1.5 flex-1 rounded-full ${s >= i ? ["", "bg-rose-500", "bg-amber-500", "bg-emerald-500"][s] : "bg-slate-200 dark:bg-slate-700"}`} />)}
                  </div>
                  <span className="text-xs text-slate-500">{["", "Weak", "Okay", "Strong"][s]}</span>
                </div>
              )}
            </Field>
            {reg && (
              <Field label="Confirm password" error={shown("confirm_password")}>
                <input className="input" type={show ? "text" : "password"} value={f.confirm_password} onChange={set("confirm_password")} onBlur={blur("confirm_password")} autoComplete="new-password" />
              </Field>
            )}
            {error && <p className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error}</p>}
            <button className="btn w-full" disabled={busy}>{busy && <Spinner />}{reg ? "Create account" : "Sign in"}</button>
          </form>
        </div>
      </div>
    </div>
  );
}
