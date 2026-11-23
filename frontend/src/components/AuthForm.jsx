import { useState } from "react";
import api from "../api/client";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";
const SAVED_GOOGLE_ACCOUNTS_KEY = "saved_google_accounts";

function getSavedGoogleAccounts() {
  try {
    const raw = localStorage.getItem(SAVED_GOOGLE_ACCOUNTS_KEY);
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore storage errors
  }
  return [];
}

export default function AuthForm({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [googleChooserOpen, setGoogleChooserOpen] = useState(false);
  const [googleAddMode, setGoogleAddMode] = useState(false);
  const [googleRemoveMode, setGoogleRemoveMode] = useState(false);
  const [savedGoogleAccounts, setSavedGoogleAccounts] = useState(getSavedGoogleAccounts);
  const [appleModalOpen, setAppleModalOpen] = useState(false);
  const [oauthEmail, setOauthEmail] = useState("");
  const [oauthName, setOauthName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (mode === "register") {
        if (password !== confirmPassword) {
          setError("Passwords do not match.");
          setLoading(false);
          return;
        }
        await api.post("/api/auth/register", {
          full_name: fullName,
          email,
          password,
          confirm_password: confirmPassword,
        });
        setSuccess("Registration successful! You can now sign in.");
        setMode("login");
        setPassword("");
        setConfirmPassword("");
      } else {
        const res = await api.post("/api/auth/login", { email, password });
        localStorage.setItem("access_token", res.data.access_token);
        onAuthenticated(res.data.user);
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Authentication failed. Please check your inputs.");
    } finally {
      setLoading(false);
    }
  };

  const completeOAuthLogin = async (provider, accountEmail, accountName) => {
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/api/auth/oauth", {
        provider,
        email: accountEmail,
        full_name: accountName,
      });
      if (provider === "google") {
        const updated = [
          { email: accountEmail.toLowerCase(), full_name: accountName || accountEmail.split("@")[0] },
          ...savedGoogleAccounts.filter((a) => a.email !== accountEmail.toLowerCase()),
        ];
        localStorage.setItem(SAVED_GOOGLE_ACCOUNTS_KEY, JSON.stringify(updated));
        setSavedGoogleAccounts(updated);
      }
      localStorage.setItem("access_token", res.data.access_token);
      setGoogleChooserOpen(false);
      setAppleModalOpen(false);
      onAuthenticated(res.data.user);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : `${provider} sign-in failed.`);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleClick = () => {
    setError("");
    setSuccess("");
    if (GOOGLE_CLIENT_ID) {
      const redirectUri = encodeURIComponent(window.location.origin);
      const scope = encodeURIComponent("openid email profile");
      window.location.href = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${redirectUri}&response_type=token&scope=${scope}&prompt=select_account`;
      return;
    }
    setGoogleRemoveMode(false);
    setGoogleAddMode(savedGoogleAccounts.length === 0);
    setOauthEmail("");
    setOauthName("");
    setGoogleChooserOpen(true);
  };

  const removeGoogleAccount = (accountEmail) => {
    const updated = savedGoogleAccounts.filter((a) => a.email !== accountEmail);
    localStorage.setItem(SAVED_GOOGLE_ACCOUNTS_KEY, JSON.stringify(updated));
    setSavedGoogleAccounts(updated);
    if (updated.length === 0) {
      setGoogleRemoveMode(false);
      setGoogleAddMode(true);
    }
  };

  // Google-style "Choose an account" screen (when VITE_GOOGLE_CLIENT_ID is not set)
  if (googleChooserOpen) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f0f4f9] px-4 text-[#1f1f1f]">
        <div className="w-full max-w-3xl rounded-3xl bg-white p-8 md:p-10 shadow-sm border border-slate-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
            <div>
              <svg className="w-9 h-9 mb-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17Z" />
                <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.11-6.72-4.96H1.29v3.14C3.26 21.3 7.31 24 12 24Z" />
                <path fill="#FBBC05" d="M5.28 14.24c-.24-.72-.38-1.49-.38-2.24s.14-1.52.38-2.24V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.99-3.14Z" />
                <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.62l3.99 3.14c.95-2.85 3.6-4.96 6.72-4.96Z" />
              </svg>
              <h1 className="text-3xl font-normal text-[#1f1f1f] mb-2">
                {googleAddMode ? "Sign in" : "Choose an account"}
              </h1>
              <p className="text-sm text-[#444746]">
                to continue to <span className="font-medium text-[#0b57d0]">Stock Research Analyst</span>
              </p>
              {error && (
                <div className="mt-4 rounded-lg bg-rose-50 border border-rose-200 px-3 py-2 text-xs text-rose-700">
                  {error}
                </div>
              )}
            </div>

            <div>
              {!googleAddMode ? (
                <div className="divide-y divide-slate-200">
                  {savedGoogleAccounts.map((acc) => (
                    <div
                      key={acc.email}
                      onClick={() => !googleRemoveMode && completeOAuthLogin("google", acc.email, acc.full_name)}
                      className="flex items-center justify-between py-3 px-2 rounded-lg hover:bg-slate-100 cursor-pointer transition"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-[#0b57d0] text-white flex items-center justify-center text-sm font-medium">
                          {(acc.full_name || acc.email)[0].toUpperCase()}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-[#1f1f1f]">{acc.full_name}</div>
                          <div className="text-xs text-[#444746]">{acc.email}</div>
                        </div>
                      </div>
                      {googleRemoveMode && (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeGoogleAccount(acc.email);
                          }}
                          className="text-xs text-rose-600 hover:underline font-medium"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  ))}

                  <button
                    type="button"
                    onClick={() => setGoogleAddMode(true)}
                    className="w-full flex items-center gap-3 py-3 px-2 rounded-lg hover:bg-slate-100 text-left text-sm font-medium text-[#1f1f1f]"
                  >
                    <span className="w-8 h-8 rounded-full border border-slate-300 flex items-center justify-center text-slate-600">+</span>
                    <span>Use another account</span>
                  </button>

                  {savedGoogleAccounts.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setGoogleRemoveMode((prev) => !prev)}
                      className="w-full flex items-center gap-3 py-3 px-2 rounded-lg hover:bg-slate-100 text-left text-sm font-medium text-[#1f1f1f]"
                    >
                      <span className="w-8 h-8 rounded-full border border-slate-300 flex items-center justify-center text-slate-600">−</span>
                      <span>{googleRemoveMode ? "Done removing accounts" : "Remove an account"}</span>
                    </button>
                  )}
                </div>
              ) : (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    completeOAuthLogin("google", oauthEmail, oauthName);
                  }}
                  className="space-y-4"
                >
                  <div>
                    <label className="block text-xs font-medium text-[#444746] mb-1">Full Name</label>
                    <input
                      type="text"
                      required
                      value={oauthName}
                      onChange={(e) => setOauthName(e.target.value)}
                      placeholder="Your Name"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-[#1f1f1f] focus:outline-none focus:border-[#0b57d0]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#444746] mb-1">Email or phone (Gmail)</label>
                    <input
                      type="email"
                      required
                      value={oauthEmail}
                      onChange={(e) => setOauthEmail(e.target.value)}
                      placeholder="yourname@gmail.com"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-[#1f1f1f] focus:outline-none focus:border-[#0b57d0]"
                    />
                  </div>
                  <div className="flex items-center justify-between pt-2">
                    <button
                      type="button"
                      onClick={() => {
                        if (savedGoogleAccounts.length > 0) setGoogleAddMode(false);
                        else setGoogleChooserOpen(false);
                      }}
                      className="text-sm font-medium text-[#0b57d0] hover:underline"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="rounded-full bg-[#0b57d0] hover:bg-[#0842a0] px-6 py-2 text-sm font-medium text-white"
                    >
                      {loading ? "Signing in..." : "Next"}
                    </button>
                  </div>
                </form>
              )}

              <div className="mt-6 flex justify-end">
                <button
                  type="button"
                  onClick={() => setGoogleChooserOpen(false)}
                  className="text-xs text-[#444746] hover:underline"
                >
                  Back to Stock Research Analyst login
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-slate-950">
      <div className="w-full max-w-md rounded-2xl bg-slate-900 border border-slate-800 p-8 shadow-2xl">
        <h1 className="text-2xl font-bold text-white mb-1">Stock Research Analyst</h1>
        <p className="text-sm text-slate-400 mb-6">
          {mode === "login"
            ? "Sign in to access your research workspace"
            : "Create an account to save watchlists and research history"}
        </p>

        {error && (
          <div className="mb-4 rounded-lg bg-rose-950/70 border border-rose-700 px-3 py-2 text-sm text-rose-200">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 rounded-lg bg-emerald-950/70 border border-emerald-700 px-3 py-2 text-sm text-emerald-200">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {mode === "register" && (
            <div>
              <label className="block text-sm text-slate-300 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          <div>
            <label className="block text-sm text-slate-300 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-300 mb-1">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          {mode === "register" && (
            <div>
              <label className="block text-sm text-slate-300 mb-1">Confirm Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-2.5 font-medium text-white transition"
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-slate-800" />
          <span className="text-xs uppercase text-slate-500">or continue with</span>
          <div className="h-px flex-1 bg-slate-800" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={handleGoogleClick}
            className="flex items-center justify-center gap-2 rounded-lg bg-white hover:bg-slate-100 text-slate-900 font-medium py-2 px-3 text-sm transition"
          >
            <span>G</span>
            <span>{mode === "register" ? "Sign up with Google" : "Google"}</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setError("");
              setOauthEmail("");
              setOauthName("");
              setAppleModalOpen(true);
            }}
            className="flex items-center justify-center gap-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-medium py-2 px-3 text-sm transition"
          >
            <span></span>
            <span>{mode === "register" ? "Sign up with Apple" : "Apple"}</span>
          </button>
        </div>

        <div className="mt-6 text-center text-sm text-slate-400">
          {mode === "login" ? (
            <>
              New here?{" "}
              <button
                type="button"
                onClick={() => {
                  setMode("register");
                  setError("");
                }}
                className="text-indigo-400 hover:underline"
              >
                Create an account
              </button>
            </>
          ) : (
            <>
              Already registered?{" "}
              <button
                type="button"
                onClick={() => {
                  setMode("login");
                  setError("");
                }}
                className="text-indigo-400 hover:underline"
              >
                Sign in
              </button>
            </>
          )}
        </div>
      </div>

      {appleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-slate-900 border border-slate-700 p-6 shadow-2xl">
            <h2 className="text-lg font-semibold text-white mb-1">Continue with Apple</h2>
            <p className="text-xs text-slate-400 mb-4">Enter your Apple ID email to sign in or register.</p>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                completeOAuthLogin("apple", oauthEmail, oauthName);
              }}
              className="space-y-3"
            >
              <div>
                <label className="block text-xs text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={oauthName}
                  onChange={(e) => setOauthName(e.target.value)}
                  placeholder="Your Name"
                  className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-300 mb-1">Apple Email</label>
                <input
                  type="email"
                  required
                  value={oauthEmail}
                  onChange={(e) => setOauthEmail(e.target.value)}
                  placeholder="yourname@icloud.com"
                  className="w-full rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-white"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setAppleModalOpen(false)}
                  className="rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-sm text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-1.5 text-sm font-medium text-white"
                >
                  {loading ? "Signing in..." : "Continue"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}