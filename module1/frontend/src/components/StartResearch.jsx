import { useEffect, useState } from "react";
import { api } from "../api.js";

export default function StartResearch({ options, prefs, onStarted }) {
  const [ticker, setTicker] = useState("");
  const [market, setMarket] = useState(prefs.market);
  const [period, setPeriod] = useState(prefs.analysis_period);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  // follow the saved preferences whenever they change
  useEffect(() => { setMarket(prefs.market); setPeriod(prefs.analysis_period); }, [prefs]);

  async function submit(e) {
    e.preventDefault();
    if (!ticker.trim()) return setMsg({ ok: false, text: "Enter a ticker symbol, e.g. AAPL or RELIANCE." });
    setBusy(true); setMsg(null);
    try {
      const t = await api("/research", { method: "POST", body: { ticker: ticker.trim(), market, analysis_period: period } });
      setMsg({ ok: true, text: `Research started for ${t.company_name} (${t.ticker}).` });
      setTicker("");
      onStarted();
    } catch (err) { setMsg({ ok: false, text: err.message }); }
    finally { setBusy(false); }
  }

  return (
    <section className="card">
      <h2 className="mb-3 text-lg font-semibold">Start new research</h2>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="label" htmlFor="rs-ticker">Ticker symbol</label>
          <input id="rs-ticker" className="input" placeholder="e.g. AAPL, TCS" value={ticker} onChange={(e) => setTicker(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label" htmlFor="rs-market">Market</label>
            <select id="rs-market" className="input" value={market} onChange={(e) => setMarket(e.target.value)}>
              {options.markets.map((m) => <option key={m.code} value={m.code}>{m.code}</option>)}
            </select>
          </div>
          <div>
            <label className="label" htmlFor="rs-period">Period</label>
            <select id="rs-period" className="input" value={period} onChange={(e) => setPeriod(e.target.value)}>
              {options.periods.map((p) => <option key={p.code} value={p.code}>{p.label}</option>)}
            </select>
          </div>
        </div>
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Starting…" : "Start research"}</button>
        {msg && <p className={`text-sm ${msg.ok ? "text-green-700" : "text-red-600"}`} role="status">{msg.text}</p>}
      </form>
    </section>
  );
}
