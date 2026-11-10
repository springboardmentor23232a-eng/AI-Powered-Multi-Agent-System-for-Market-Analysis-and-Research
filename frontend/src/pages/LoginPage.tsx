import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { authenticated, signIn } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (authenticated) return <Navigate to="/" replace />;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (mode === "register") {
      if (!fullName.trim()) {
        setError("Please enter your full name");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }
    }
    setBusy(true);
    try {
      await signIn(email, password, mode, fullName.trim(), confirmPassword);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach the server");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={submit} className="w-full max-w-sm space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div>
          <h1 className="text-xl font-semibold">Veritas Equity Research</h1>
          <p className="text-sm text-slate-500">Evidence-audited research on Indian equities.</p>
        </div>
        {mode === "register" && (
          <label className="block text-sm">Full Name
            <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2" type="text" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </label>
        )}
        <label className="block text-sm">Email
          <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="block text-sm">Password
          <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {mode === "register" && (
          <label className="block text-sm">Confirm Password
            <input className="mt-1 w-full rounded border border-slate-300 px-3 py-2" type="password" required minLength={8} value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </label>
        )}
        {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
        <button disabled={busy} className="w-full rounded bg-slate-900 py-2 text-sm font-medium text-white disabled:opacity-60">{mode === "login" ? "Sign in" : "Create account"}</button>
        <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(null); }} className="w-full text-sm text-slate-600 underline">
          {mode === "login" ? "New here? Create an account" : "Have an account? Sign in"}
        </button>
      </form>
    </div>
  );
}
