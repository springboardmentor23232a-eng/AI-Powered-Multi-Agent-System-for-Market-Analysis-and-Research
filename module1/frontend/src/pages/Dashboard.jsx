import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../AuthContext.jsx";
import ThemeToggle from "../components/ThemeToggle.jsx";
import Preferences from "../components/Preferences.jsx";
import ResearchHistory from "../components/ResearchHistory.jsx";
import StockExplorer from "../components/StockExplorer.jsx";
import StartResearch from "../components/StartResearch.jsx";
import Watchlist from "../components/Watchlist.jsx";

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [options, setOptions] = useState(null);
  const [prefs, setPrefs] = useState(null);
  const [historyKey, setHistoryKey] = useState(0);
  const [error, setError] = useState("");
  const refreshHistory = useCallback(() => setHistoryKey((k) => k + 1), []);

  // Load the user's saved preferences (and dropdown options) when the dashboard opens
  useEffect(() => {
    Promise.all([api("/options"), api("/preferences")])
      .then(([o, p]) => { setOptions(o); setPrefs(p); })
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page-fade relative min-h-screen overflow-x-clip">
      <div className="blob-wrap" aria-hidden="true"><span className="blob blob-1" /><span className="blob blob-2" /><span className="blob blob-3" /></div>
      <header className="relative z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">📈</span>
            <span className="hidden font-semibold sm:inline">Stock Research Analyst</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-600">Hi, <b>{user.full_name}</b></span>
            <ThemeToggle />
            <button className="btn-ghost" onClick={logout}>Logout</button>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-7xl px-4 py-6">
        <h1 className="hero-title reveal mb-1 inline-block text-2xl font-semibold">Your research workspace</h1>
        <p className="reveal mb-6 text-sm text-slate-500" style={{ "--i": 1 }}>Manage preferences, keep a watchlist and revisit your research history.</p>
        {error && <div role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

        {options && prefs && <div className="reveal" style={{ "--i": 2 }}><StockExplorer options={options} prefs={prefs} /></div>}
        {options && prefs && (
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="reveal min-w-0 space-y-6 lg:col-span-1" style={{ "--i": 3 }}>
              <Preferences options={options} prefs={prefs} onSaved={setPrefs} />
              <StartResearch options={options} prefs={prefs} onStarted={refreshHistory} />
              <Watchlist prefs={prefs} onResearchStarted={refreshHistory} />
            </div>
            <div className="reveal min-w-0 lg:col-span-2" style={{ "--i": 4 }}>
              <ResearchHistory refreshKey={historyKey} />
            </div>
          </div>
        )}
        {!options && !error && (
          <div className="space-y-4" role="status" aria-label="Loading your workspace">
            <div className="skeleton h-40" /><div className="grid gap-4 lg:grid-cols-3"><div className="skeleton h-64" /><div className="skeleton h-64 lg:col-span-2" /></div>
          </div>
        )}
      </main>
    </div>
  );
}
