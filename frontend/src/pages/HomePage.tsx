import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Preferences, SearchHit, TaskSummary, WatchItem } from "../api/types";
import { StatusPill } from "../components/Badges";
import { shortDate } from "../lib/format";

const PERIODS = ["1mo", "3mo", "6mo", "1y", "5y"];

export default function HomePage() {
  const nav = useNavigate();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [asOf, setAsOf] = useState("");
  const [history, setHistory] = useState<TaskSummary[]>([]);
  const [watch, setWatch] = useState<WatchItem[]>([]);
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [h, w, p] = await Promise.all([api.history(), api.watchlist(), api.preferences()]);
    setHistory(h); setWatch(w); setPrefs(p);
  }, []);

  useEffect(() => { refresh().catch(() => setError("Could not load your workspace")); }, [refresh]);

  useEffect(() => {
    if (!query.trim()) { setHits([]); return; }
    const t = setTimeout(() => api.search(query).then((r) => setHits(r.results)).catch(() => setHits([])), 250);
    return () => clearTimeout(t);
  }, [query]);

  const run = async (fn: () => Promise<unknown>) => {
    setError(null);
    try { await fn(); } catch (e) { setError(e instanceof ApiError ? e.message : "Request failed"); }
  };

  const start = (ticker: string) => run(async () => nav(`/research/${(await api.startResearch(ticker, asOf || undefined)).task_id}`));
  const watching = new Set(watch.map((w) => w.ticker));

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <section className="space-y-4 lg:col-span-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Research a stock</h2>
          <input aria-label="Search by company name or ticker" placeholder="Search NSE company or ticker, e.g. Infosys" value={query}
            onChange={(e) => setQuery(e.target.value)} className="w-full rounded border border-slate-300 px-3 py-2" />
          <details className="mt-2 text-sm"><summary className="cursor-pointer text-slate-600">Replay: research as of a past date</summary>
            <input type="date" aria-label="As-of date" value={asOf} max={new Date().toISOString().slice(0, 10)} onChange={(e) => setAsOf(e.target.value)} className="mt-2 rounded border border-slate-300 px-2 py-1" />
            <p className="mt-1 text-xs text-slate-500">Uses prices up to that date. News is skipped; financials are the latest filings.</p></details>
          {error && <p role="alert" className="mt-2 text-sm text-red-700">{error}</p>}
          <ul className="mt-3 divide-y divide-slate-100">
            {hits.map((h) => (
              <li key={h.ticker} className="flex items-center justify-between py-2 text-sm">
                <span><span className="font-medium">{h.ticker}</span> <span className="text-slate-500">{h.name}</span></span>
                <span className="flex gap-2">
                  <button onClick={() => run(async () => { await (watching.has(h.ticker) ? api.unwatch(h.ticker) : api.watch(h.ticker)); await refresh(); })} className="rounded border border-slate-300 px-2 py-1 text-xs">{watching.has(h.ticker) ? "Unwatch" : "Watch"}</button>
                  <button onClick={() => start(h.ticker)} className="rounded bg-slate-900 px-3 py-1 text-xs font-medium text-white">Research</button>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Research history</h2>
          {history.length === 0 ? <p className="text-sm text-slate-500">No research yet. Search for a stock to begin.</p> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-500">
                    <th className="py-2">Stock</th>
                    <th className="hidden sm:table-cell">Market</th>
                    <th className="hidden md:table-cell">Period</th>
                    <th>Status</th>
                    <th className="text-right">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((t) => (
                    <tr key={t.task_id} className="border-t border-slate-100 first:border-0">
                      <td className="py-2 font-medium">
                        <Link className="text-blue-700 underline" to={`/research/${t.task_id}`}>{t.ticker}</Link>
                        {t.company_name && <span className="ml-2 hidden text-xs text-slate-500 sm:inline">{t.company_name}</span>}
                      </td>
                      <td className="hidden text-xs text-slate-500 sm:table-cell">{t.market}</td>
                      <td className="hidden text-xs text-slate-500 md:table-cell">{t.requested_period || "2y"}</td>
                      <td><StatusPill status={t.status} /></td>
                      <td className="text-right text-xs text-slate-500">{shortDate(t.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </section>

      <aside className="space-y-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Watchlist</h2>
          {watch.length === 0 ? <p className="text-sm text-slate-500">Nothing saved yet.</p> : (
            <ul className="space-y-1">
              {watch.map((w) => (
                <li key={w.ticker} className="flex items-center justify-between py-1 text-sm border-b border-slate-50 last:border-0">
                  <span>{w.ticker} <span className="text-xs text-slate-500">{w.name}</span></span>
                  <span className="flex items-center gap-2">
                    <button className="text-xs text-red-600 hover:text-red-800" title="Remove from watchlist" onClick={() => run(async () => { await api.unwatch(w.ticker); await refresh(); })}>Remove</button>
                    <button className="text-xs text-blue-700 underline" onClick={() => start(w.ticker)}>Research</button>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
        {prefs && (
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-2 text-sm font-semibold text-slate-700">Preferences</h2>
            <label className="block text-sm">Market
              <select value={prefs.market} onChange={(e) => run(async () => setPrefs(await api.setPreferences({ ...prefs, market: e.target.value })))}
                className="mt-1 block w-full rounded border border-slate-300 px-2 py-1">
                <option value="NSE">NSE (National Stock Exchange)</option>
                <option value="BSE">BSE (Bombay Stock Exchange)</option>
              </select>
            </label>
            <label className="mt-3 block text-sm">Default analysis period
              <select value={prefs.analysis_period} onChange={(e) => run(async () => setPrefs(await api.setPreferences({ ...prefs, analysis_period: e.target.value })))}
                className="mt-1 block w-full rounded border border-slate-300 px-2 py-1">
                {PERIODS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </label>
          </div>
        )}
      </aside>
    </div>
  );
}
