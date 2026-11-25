import { useEffect, useState } from "react";
import { MARKETS, PERIODS } from "../constants";

export default function PreferencesCard({ prefs, onSave }) {
  const [draft, setDraft] = useState(prefs);
  const [saving, setSaving] = useState(false);
  useEffect(() => setDraft(prefs), [prefs]);

  const dirty = draft.market !== prefs.market || draft.analysis_period !== prefs.analysis_period;
  const market = MARKETS.find((m) => m.id === draft.market);
  const period = PERIODS.find((p) => p.value === draft.analysis_period);
  const savedPeriod = PERIODS.find((p) => p.value === prefs.analysis_period);

  const save = async () => {
    setSaving(true);
    await onSave(draft);
    setSaving(false);
  };

  return (
    <section className="panel" id="preferences">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Research preferences</h2>
          <p className="panel-sub">Default market and history length for new research. Saved to your account.</p>
        </div>
        <div className="row">
          <span className="badge badge-brand">{prefs.market}</span>
          <span className="badge badge-brand">{savedPeriod?.label}</span>
        </div>
      </div>

      <div className="pref-grid">
        <div className="pref-box">
          <label htmlFor="pref-market">Market</label>
          <select
            id="pref-market"
            className="select"
            value={draft.market}
            onChange={(e) => setDraft({ ...draft, market: e.target.value })}
          >
            {MARKETS.map((m) => <option key={m.id} value={m.id}>{m.id}: {m.full}</option>)}
          </select>
          <span className="pref-note">Ticker format: {market?.hint}</span>
        </div>
        <div className="pref-box">
          <label htmlFor="pref-period">Analysis period</label>
          <select
            id="pref-period"
            className="select"
            value={draft.analysis_period}
            onChange={(e) => setDraft({ ...draft, analysis_period: e.target.value })}
          >
            {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}: {p.note}</option>)}
          </select>
          <span className="pref-note">
            About {period?.label.toLowerCase()} of daily prices, depending on what the provider has.
          </span>
        </div>
      </div>

      <div className="pref-actions">
        <button className="btn btn-ghost" disabled={!dirty || saving} onClick={() => setDraft(prefs)}>
          Reset
        </button>
        <button className="btn btn-primary" disabled={!dirty || saving} onClick={save}>
          {saving ? "Saving…" : "Save preferences"}
        </button>
      </div>
    </section>
  );
}
