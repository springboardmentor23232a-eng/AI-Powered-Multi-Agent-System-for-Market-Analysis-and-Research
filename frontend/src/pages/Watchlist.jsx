import { useEffect, useState } from "react";
import { api } from "../api";

export default function Watchlist({ onResearchStarted }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [saved, setSaved] = useState([]);
  const [msg, setMsg] = useState("");

  const load = () => api("/watchlist").then(setSaved).catch((e) => setMsg(e.message));
  useEffect(() => { load(); }, []);

  const search = async (e) => {
    e.preventDefault();
    setMsg("");
    try { setResults(await api(`/stocks/search?q=${encodeURIComponent(q)}`)); }
    catch (err) { setMsg(err.message); }
  };

  const add = async (s) => {
    try {
      await api("/watchlist", { method: "POST", body: JSON.stringify(s) });
      setMsg(`${s.ticker} added ✓`);
      load();
    } catch (err) { setMsg(err.message); }
  };

  const remove = async (id) => {
    try { await api(`/watchlist/${id}`, { method: "DELETE" }); load(); }
    catch (err) { setMsg(err.message); }
  };

  const research = async (s) => {
    try {
      await api("/research", {
        method: "POST",
        body: JSON.stringify({ ticker: s.ticker, company_name: s.company_name, market: s.market }),
      });
      onResearchStarted?.();
    } catch (err) { setMsg(err.message); }
  };

  return (
    <section>
      <h3>Watchlist</h3>
      <form onSubmit={search}>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Company name or ticker" required />{" "}
        <button>Search</button>
      </form>
      {msg && <p>{msg}</p>}

      {results.length > 0 && (
        <ul>
          {results.map((r) => (
            <li key={r.ticker}>
              {r.ticker} — {r.company_name} ({r.market}){" "}
              <button onClick={() => add(r)}>Add to Watchlist</button>
            </li>
          ))}
        </ul>
      )}

      <h4>Saved stocks</h4>
      {saved.length === 0 ? <p>No saved stocks yet.</p> : (
        <ul>
          {saved.map((s) => (
            <li key={s.saved_stock_id}>
              {s.ticker} — {s.company_name} ({s.market}){" "}
              <button onClick={() => research(s)}>Research</button>{" "}
              <button onClick={() => remove(s.saved_stock_id)}>Remove</button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}