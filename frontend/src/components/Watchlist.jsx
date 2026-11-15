import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";

export default function Watchlist({ prefs, onResearchStarted }) {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [msg, setMsg] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => api("/watchlist").then(setItems).catch((e) => setMsg({ ok: false, text: e.message })).finally(() => setLoading(false)), []);
  useEffect(() => { load(); }, [load]);

  // Search by company name or ticker (debounced); limited to the preferred market first, then all markets
  useEffect(() => {
    if (!q.trim()) { setResults([]); return; }
    const id = setTimeout(() => {
      api(`/stocks/search?q=${encodeURIComponent(q.trim())}&limit=8`).then(setResults).catch(() => setResults([]));
    }, 250);
    return () => clearTimeout(id);
  }, [q]);

  const saved = new Set(items.map((i) => i.ticker));
  const sorted = [...results].sort((a, b) => (b.market === prefs.market) - (a.market === prefs.market));

  async function add(s) {
    setMsg(null);
    try {
      await api("/watchlist", { method: "POST", body: { ticker: s.ticker, market: s.market } });
      setMsg({ ok: true, text: `${s.ticker} added to your watchlist.` });
      setQ(""); setResults([]);
      load();
    } catch (e) { setMsg({ ok: false, text: e.message }); }
  }
  async function remove(item) {
    setMsg(null);
    try { await api(`/watchlist/${item.saved_stock_id}`, { method: "DELETE" }); setMsg({ ok: true, text: `${item.ticker} removed.` }); load(); }
    catch (e) { setMsg({ ok: false, text: e.message }); }
  }
  async function research(item) {
    setMsg(null);
    try { await api(`/watchlist/${item.saved_stock_id}/research`, { method: "POST" }); setMsg({ ok: true, text: `Research started for ${item.ticker}.` }); onResearchStarted(); }
    catch (e) { setMsg({ ok: false, text: e.message }); }
  }

  return (
    <section className="card">
      <h2 className="mb-3 text-lg font-semibold">Watchlist</h2>
      <label className="label" htmlFor="wl-search">Search company or ticker</label>
      <input id="wl-search" className="input" placeholder="Try “apple”, “TCS”, “reliance”…" value={q} onChange={(e) => setQ(e.target.value)} />
      {q.trim() && (
        <ul className="mt-2 divide-y divide-slate-100 rounded-lg border border-slate-200">
          {sorted.length === 0 && <li className="px-3 py-2 text-sm text-slate-500">No supported stocks match “{q}”.</li>}
          {sorted.map((s) => (
            <li key={s.market + s.ticker} className="flex items-center justify-between gap-2 px-3 py-2 text-sm">
              <span><b>{s.ticker}</b> <span className="text-slate-500">· {s.name} · {s.market}</span></span>
              {saved.has(s.ticker) ? <span className="text-xs text-slate-400">Saved</span> : <button className="btn-ghost !px-2 !py-1 text-xs" onClick={() => add(s)}>Add to Watchlist</button>}
            </li>
          ))}
        </ul>
      )}
      {msg && <p className={`mt-2 text-sm ${msg.ok ? "text-green-700" : "text-red-600"}`} role="status">{msg.text}</p>}

      <h3 className="mb-2 mt-5 text-sm font-semibold text-slate-600">Saved stocks ({items.length})</h3>
      {loading ? <p className="text-sm text-slate-500">Loading…</p> : items.length === 0 ? (
        <p className="text-sm text-slate-500">Nothing saved yet — search above and add a stock.</p>
      ) : (
        <ul className="divide-y divide-slate-100">
          {items.map((i) => (
            <li key={i.saved_stock_id} className="flex flex-wrap items-center justify-between gap-2 py-2">
              <div className="text-sm"><b>{i.ticker}</b><div className="text-xs text-slate-500">{i.company_name} · {i.market}</div></div>
              <div className="flex gap-2">
                <button className="btn-primary !px-2 !py-1 text-xs" onClick={() => research(i)}>Research</button>
                <button className="btn-danger !px-2 !py-1 text-xs" onClick={() => remove(i)}>Remove</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
