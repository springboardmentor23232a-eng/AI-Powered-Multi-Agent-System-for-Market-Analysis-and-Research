import { useEffect, useState } from "react";
import { api } from "../api";
import { MARKETS, PERIODS } from "../constants";

export default function Preferences() {
  const [pref, setPref] = useState({ market: "NSE", analysis_period: "1y" });
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api("/preferences").then(setPref).catch((e) => setMsg(e.message));
  }, []);

  const save = async () => {
    try {
      setPref(await api("/preferences", { method: "PUT", body: JSON.stringify(pref) }));
      setMsg("Saved ✓");
    } catch (e) { setMsg(e.message); }
  };

  return (
    <section>
      <h3>Preferences</h3>
      <select value={pref.market} onChange={(e) => setPref({ ...pref, market: e.target.value })}>
        {MARKETS.map((m) => <option key={m}>{m}</option>)}
      </select>{" "}
      <select value={pref.analysis_period} onChange={(e) => setPref({ ...pref, analysis_period: e.target.value })}>
        {PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
      </select>{" "}
      <button onClick={save}>Save</button> <span>{msg}</span>
    </section>
  );
}