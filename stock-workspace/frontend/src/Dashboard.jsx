import React, { useCallback, useEffect, useRef, useState } from "react";
import { api, MARKETS, PERIODS, periodLabel } from "./api.js";
import { ReportView, Spinner, StatusBadge, fmtDate, useToast } from "./ui.jsx";

const TABS = [
  { id: "overview", icon: "🏠", label: "Overview" },
  { id: "research", icon: "🔬", label: "Research History" },
  { id: "watchlist", icon: "⭐", label: "Watchlist" },
  { id: "prefs", icon: "⚙️", label: "Preferences" },
];
const active = (t) => t.status === "Pending" || t.status === "Processing";

/* ---------- Debounced stock search ---------- */
function StockSearch({ market, onPick, actionLabel, placeholder }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!q.trim()) { setResults([]); return; }
    setLoading(true);
    const t = setTimeout(() => {
      api.search(q, market).then(setResults).catch(() => setResults([])).finally(() => setLoading(false));
    }, 250);
    return () => clearTimeout(t);
  }, [q, market]);

  return (
    <div>
      <div className="relative">
        <input className="input" value={q} onChange={(e) => setQ(e.target.value)} placeholder={placeholder || `Search ${market} by name or ticker…`} />
        {loading && <span className="absolute right-3 top-2.5 text-indigo-600"><Spinner /></span>}
      </div>
      {q.trim() && !loading && results.length === 0 && <p className="mt-2 text-sm text-slate-500">No {market} matches for “{q}”.</p>}
      <ul className="mt-2 space-y-2">
        {results.map((s) => (
          <li key={s.ticker} className="animate-pop flex items-center justify-between rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-800">
            <div><span className="font-semibold">{s.ticker}</span> <span className="text-sm text-slate-500">{s.company_name}</span></div>
            <button className="btn !py-1" onClick={() => { onPick(s); }}>{actionLabel}</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

/* ---------- Research table ---------- */
function TaskTable({ tasks, onOpen, empty }) {
  if (!tasks.length) return <p className="py-8 text-center text-sm text-slate-500">{empty}</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr>{["Company", "Market", "Period", "Date", "Status", ""].map((h) => <th key={h} className="px-3 py-2 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody>
          {tasks.map((t) => (
            <tr key={t.task_id} className="animate-pop border-t border-slate-100 dark:border-slate-800">
              <td className="px-3 py-3"><div className="font-medium">{t.company_name}</div><div className="text-xs text-slate-500">{t.ticker}</div></td>
              <td className="px-3 py-3">{t.market}</td>
              <td className="px-3 py-3">{periodLabel(t.analysis_period)}</td>
              <td className="whitespace-nowrap px-3 py-3">{fmtDate(t.created_at)}</td>
              <td className="px-3 py-3"><StatusBadge status={t.status} /></td>
              <td className="px-3 py-3 text-right">
                <button className="btn-ghost" disabled={t.status === "Pending" || t.status === "Processing"} onClick={() => onOpen(t)}>
                  {t.status === "Failed" ? "Details" : "Open report"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function Dashboard({ user, setUser, onLogout, dark, toggleTheme }) {
  const toast = useToast();
  const [tab, setTab] = useState("overview");
  const [tasks, setTasks] = useState([]);
  const [watch, setWatch] = useState([]);
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState(null);
  const [filter, setFilter] = useState("All");
  const [prefs, setPrefs] = useState({ market: user.market, analysis_period: user.analysis_period });
  const [savingPrefs, setSavingPrefs] = useState(false);
  const prev = useRef({});

  const loadTasks = useCallback(async () => {
    const list = await api.tasks();
    list.forEach((t) => {
      const before = prev.current[t.task_id];
      if (before && active({ status: before }) && !active(t)) {
        toast(t.status === "Completed" ? `${t.ticker} report is ready` : `${t.ticker} research failed`, t.status === "Completed" ? "success" : "error");
      }
      prev.current[t.task_id] = t.status;
    });
    setTasks(list);
  }, [toast]);

  useEffect(() => {
    Promise.all([loadTasks(), api.watchlist().then(setWatch)]).finally(() => setLoading(false));
  }, [loadTasks]);

  // Live updates: poll while any task is still running.
  const running = tasks.some(active);
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => loadTasks().catch(() => {}), 2000);
    return () => clearInterval(id);
  }, [running, loadTasks]);

  const guard = async (fn) => {
    try { return await fn(); }
    catch (e) {
      if (e.status === 401) { toast("Session expired. Please sign in again.", "error"); onLogout(); }
      else toast(e.message, "error");
    }
  };

  const startResearch = (ticker, market) => guard(async () => {
    const t = await api.startResearch({ ticker, market, analysis_period: user.analysis_period });
    prev.current[t.task_id] = t.status;
    setTasks((s) => [t, ...s]);
    toast(`Research started for ${t.ticker}`);
    setTab("research");
  });

  const addWatch = (s) => guard(async () => {
    const item = await api.addWatch({ ticker: s.ticker, market: s.market });
    setWatch((w) => [item, ...w]);
    toast(`${item.ticker} added to watchlist`);
  });

  const removeWatch = (item) => guard(async () => {
    await api.removeWatch(item.saved_stock_id);
    setWatch((w) => w.filter((x) => x.saved_stock_id !== item.saved_stock_id));
    toast(`${item.ticker} removed`);
  });

  const openReport = (t) => guard(async () => setReport(await api.task(t.task_id)));

  const savePrefs = () => guard(async () => {
    setSavingPrefs(true);
    try { setUser(await api.savePrefs(prefs)); toast("Preferences saved"); }
    finally { setSavingPrefs(false); }
  });

  const counts = {
    total: tasks.length, done: tasks.filter((t) => t.status === "Completed").length,
    running: tasks.filter(active).length, saved: watch.length,
  };
  const shownTasks = filter === "All" ? tasks : tasks.filter((t) => t.status === filter);
  const hour = new Date().getHours();
  const greet = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const dirty = prefs.market !== user.market || prefs.analysis_period !== user.analysis_period;

  return (
    <div className="min-h-screen md:flex">
      {/* Sidebar / mobile top bar */}
      <aside className="border-b border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-900 md:min-h-screen md:w-60 md:border-b-0 md:border-r md:p-4">
        <div className="mb-3 flex items-center gap-2 px-2 text-lg font-bold md:mb-6"><span>📈</span> Research Desk</div>
        <nav className="flex gap-1 overflow-x-auto md:flex-col">
          {TABS.map((t) => (
            <button key={t.id} onClick={() => setTab(t.id)} className={`flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium transition ${tab === t.id ? "bg-indigo-600 text-white" : "hover:bg-slate-100 dark:hover:bg-slate-800"}`}>
              <span>{t.icon}</span>{t.label}
              {t.id === "research" && counts.running > 0 && <span className="ml-auto rounded-full bg-amber-400 px-1.5 text-xs text-slate-900">{counts.running}</span>}
            </button>
          ))}
        </nav>
      </aside>

      <main className="flex-1 p-4 md:p-8">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">{greet}, {user.full_name.split(" ")[0]} 👋</h1>
            <p className="text-sm text-slate-500">{user.email} · {user.market} · {periodLabel(user.analysis_period)}</p>
          </div>
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={toggleTheme}>{dark ? "☀️" : "🌙"}</button>
            <button className="btn-ghost" onClick={onLogout}>Sign out</button>
          </div>
        </header>

        {loading ? (
          <div className="flex justify-center py-20 text-indigo-600"><Spinner className="h-8 w-8" /></div>
        ) : (
          <div className="animate-pop space-y-6" key={tab}>
            {tab === "overview" && (
              <>
                <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                  {[["Research tasks", counts.total, "🧪"], ["Completed", counts.done, "✅"], ["In progress", counts.running, "⏳"], ["Saved stocks", counts.saved, "⭐"]].map(([k, v, i]) => (
                    <div key={k} className="card"><div className="text-2xl">{i}</div><div className="mt-2 text-3xl font-bold">{v}</div><div className="text-sm text-slate-500">{k}</div></div>
                  ))}
                </div>
                <div className="grid gap-6 lg:grid-cols-2">
                  <div className="card">
                    <h2 className="mb-1 font-semibold">Start new research</h2>
                    <p className="mb-3 text-sm text-slate-500">Searching {user.market} · {periodLabel(user.analysis_period)} (change in Preferences)</p>
                    <StockSearch market={user.market} actionLabel="Research" onPick={(s) => startResearch(s.ticker, user.market)} />
                  </div>
                  <div className="card">
                    <h2 className="mb-3 font-semibold">Recent research</h2>
                    <TaskTable tasks={tasks.slice(0, 4)} onOpen={openReport} empty="No research yet — search a stock to begin." />
                  </div>
                </div>
              </>
            )}

            {tab === "research" && (
              <div className="card">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <h2 className="font-semibold">Research history</h2>
                  <div className="flex gap-1 rounded-xl bg-slate-100 p-1 text-xs dark:bg-slate-800">
                    {["All", "Pending", "Processing", "Completed", "Failed"].map((s) => (
                      <button key={s} onClick={() => setFilter(s)} className={`rounded-lg px-2.5 py-1 ${filter === s ? "bg-white shadow dark:bg-slate-700" : "text-slate-500"}`}>{s}</button>
                    ))}
                  </div>
                </div>
                <TaskTable tasks={shownTasks} onOpen={openReport} empty="Nothing here yet." />
              </div>
            )}

            {tab === "watchlist" && (
              <div className="grid gap-6 lg:grid-cols-2">
                <div className="card">
                  <h2 className="mb-3 font-semibold">Find a stock</h2>
                  <div className="mb-3 flex gap-1 rounded-xl bg-slate-100 p-1 text-xs dark:bg-slate-800">
                    {MARKETS.map((m) => (
                      <button key={m.id} onClick={() => setPrefs((p) => ({ ...p, market: m.id }))} className={`flex-1 rounded-lg py-1.5 ${prefs.market === m.id ? "bg-white shadow dark:bg-slate-700" : "text-slate-500"}`}>{m.label}</button>
                    ))}
                  </div>
                  <StockSearch market={prefs.market} actionLabel="＋ Add" onPick={addWatch} />
                </div>
                <div className="card">
                  <h2 className="mb-3 font-semibold">Saved stocks ({watch.length})</h2>
                  {watch.length === 0 && <p className="py-6 text-center text-sm text-slate-500">Your watchlist is empty.</p>}
                  <ul className="space-y-2">
                    {watch.map((w) => (
                      <li key={w.saved_stock_id} className="animate-pop flex items-center justify-between gap-2 rounded-xl border border-slate-200 px-3 py-2 dark:border-slate-800">
                        <div><div className="font-semibold">{w.ticker} <span className="text-xs font-normal text-slate-500">{w.market}</span></div><div className="text-sm text-slate-500">{w.company_name}</div></div>
                        <div className="flex gap-2">
                          <button className="btn !py-1" onClick={() => startResearch(w.ticker, w.market)}>Research</button>
                          <button className="btn-ghost !py-1 text-rose-600" onClick={() => removeWatch(w)}>Remove</button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {tab === "prefs" && (
              <div className="card max-w-2xl">
                <h2 className="mb-4 font-semibold">Research preferences</h2>
                <h3 className="mb-2 text-sm font-medium">Market</h3>
                <div className="mb-6 grid gap-2 sm:grid-cols-2">
                  {MARKETS.map((m) => (
                    <button key={m.id} onClick={() => setPrefs({ ...prefs, market: m.id })} className={`rounded-xl border p-3 text-left transition ${prefs.market === m.id ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-500/10" : "border-slate-200 hover:border-slate-300 dark:border-slate-700"}`}>
                      <div className="font-semibold">{m.label}</div><div className="text-xs text-slate-500">{m.desc}</div>
                    </button>
                  ))}
                </div>
                <h3 className="mb-2 text-sm font-medium">Analysis period</h3>
                <div className="mb-6 flex flex-wrap gap-2">
                  {PERIODS.map((p) => (
                    <button key={p.id} onClick={() => setPrefs({ ...prefs, analysis_period: p.id })} className={`rounded-full border px-4 py-1.5 text-sm transition ${prefs.analysis_period === p.id ? "border-indigo-600 bg-indigo-600 text-white" : "border-slate-300 dark:border-slate-700"}`}>{p.label}</button>
                  ))}
                </div>
                <button className="btn" disabled={!dirty || savingPrefs} onClick={savePrefs}>{savingPrefs && <Spinner />}Save preferences</button>
              </div>
            )}
          </div>
        )}
      </main>
      {report && <ReportView task={report} onClose={() => setReport(null)} />}
    </div>
  );
}
