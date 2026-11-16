import { useState } from "react";
import { api } from "../api.js";

export default function Preferences({ options, prefs, onSaved }) {
  const [market, setMarket] = useState(prefs.market);
  const [period, setPeriod] = useState(prefs.analysis_period);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  const dirty = market !== prefs.market || period !== prefs.analysis_period;
  const current = options.markets.find((m) => m.code === market);

  async function save() {
    setBusy(true); setMsg(null);
    try {
      const saved = await api("/preferences", { method: "PUT", body: { market, analysis_period: period } });
      onSaved(saved);
      setMsg({ ok: true, text: "Preferences saved." });
    } catch (e) { setMsg({ ok: false, text: e.message }); }
    finally { setBusy(false); }
  }

  return (
    <section className="card">
      <h2 className="mb-3 text-lg font-semibold">Preferences</h2>
      <div className="space-y-3">
        <div>
          <label className="label" htmlFor="pref-market">Market</label>
          <select id="pref-market" className="input" value={market} onChange={(e) => setMarket(e.target.value)}>
            {options.markets.map((m) => <option key={m.code} value={m.code}>{m.code} – {m.name}</option>)}
          </select>
          <p className="mt-1 text-xs text-slate-500">Example symbols: {current?.example}</p>
        </div>
        <div>
          <label className="label" htmlFor="pref-period">Analysis period</label>
          <select id="pref-period" className="input" value={period} onChange={(e) => setPeriod(e.target.value)}>
            {options.periods.map((p) => <option key={p.code} value={p.code}>{p.label}</option>)}
          </select>
        </div>
        <button className="btn-primary w-full" onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save preferences"}</button>
        {msg && <p className={`text-sm ${msg.ok ? "text-green-700" : "text-red-600"}`} role="status">{msg.text}</p>}
      </div>
    </section>
  );
}
