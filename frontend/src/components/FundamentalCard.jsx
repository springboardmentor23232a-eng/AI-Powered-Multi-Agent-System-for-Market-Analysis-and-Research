import { useState } from "react";
import { useApi } from "../hooks";
import { compact, dateTimeOf } from "../format";
import "./fundamental.css";

const fp = (v) => (v == null ? "—" : `${(v * 100).toFixed(1)}%`);
const fx = (v, d = 2) => (v == null ? "—" : `${Number(v).toFixed(d)}x`);

const SECTIONS = [
  ["revenue_earnings", "Revenue and earnings"],
  ["profitability", "Profitability"],
  ["financial_stability", "Debt and financial stability"],
  ["valuation", "Valuation"],
];

// Rows of the history table: [label, key, formatter]. Money rows get the currency.
const HISTORY_ROWS = (cur) => [
  ["Revenue", "revenue", (v) => compact(v, cur)],
  ["Revenue growth", "revenue_growth", fp],
  ["Net income", "net_income", (v) => compact(v, cur)],
  ["Net income growth", "net_income_growth", fp],
  ["Gross margin", "gross_margin", fp],
  ["Operating margin", "operating_margin", fp],
  ["Net margin", "net_margin", fp],
  ["ROE", "roe", fp],
  ["Debt to equity", "debt_to_equity", fx],
  ["Current ratio", "current_ratio", fx],
  ["Interest coverage", "interest_coverage", (v) => fx(v, 1)],
  ["Free cash flow", "free_cash_flow", (v) => compact(v, cur)],
];

function Provider({ mine, theirs, fmt }) {
  if (theirs == null) return <div className="fa-fund-sub">Provider: not reported</div>;
  return <div className="fa-fund-sub">Provider: {fmt(theirs)}</div>;
}

export default function FundamentalCard({ ticker, market, currency }) {
  const [peerInput, setPeerInput] = useState("");
  const [peers, setPeers] = useState("");
  const [nonce, setNonce] = useState(0);
  const path = `/market/${encodeURIComponent(ticker)}/fundamental?market=${market}` +
    (peers ? `&peers=${encodeURIComponent(peers)}` : "");
  const res = useApi(path, nonce);
  const d = res.data;
  const cur = d?.currency || currency;

  const head = (sub, badge) => (
    <div className="panel-head">
      <div>
        <h2 className="panel-title">Fundamental analysis</h2>
        <p className="panel-sub">{sub}</p>
      </div>
      {badge}
    </div>
  );

  if (res.loading) {
    return <section className="panel">{head("Analysing annual statements")}<div className="skeleton" style={{ height: 220, borderRadius: 12 }} /></section>;
  }
  if (res.error) {
    return <section className="panel">{head("Not available")}<div className="notice notice-warn">Fundamental analysis unavailable: {res.error}</div></section>;
  }

  const q = d.data_quality;
  const val = d.valuation;
  const prov = val.provider;
  const rows = HISTORY_ROWS(cur);

  return (
    <section className="panel">
      {head(
        `Calculated from annual statements, ${d.fiscal_year}, retrieved ${dateTimeOf(d.meta.retrieved_at)}`,
        <span className={`badge fa-conf-${q.confidence}`}>Data confidence: {q.confidence}</span>
      )}

      <p className="fa-summary">{d.assessment.overall}</p>

      <div className="fund-grid">
        <div className="fund-item">
          <span className="stat-label">P/E (latest annual EPS)</span>
          <div className="stat-value display">{fx(val.pe, 1)}</div>
          <Provider theirs={prov.pe} fmt={(v) => Number(v).toFixed(1)} />
        </div>
        <div className="fund-item">
          <span className="stat-label">Price to book</span>
          <div className="stat-value display">{fx(val.pb)}</div>
          <Provider theirs={prov.pb} fmt={(v) => Number(v).toFixed(2)} />
        </div>
        <div className="fund-item">
          <span className="stat-label">Return on equity</span>
          <div className="stat-value display">{fp(val.roe)}</div>
          <Provider theirs={prov.roe} fmt={fp} />
        </div>
      </div>
      <p className="hint">Calculated by the agent from the statements. The provider's own figures are shown for comparison.</p>

      <div className="fa-sections">
        {SECTIONS.map(([key, title]) => {
          const s = d.assessment.sections[key];
          return (
            <div className="fa-section" key={key}>
              <h3><span className={`fa-dot ${s.rating}`} />{title}</h3>
              <p className="fa-head">{s.headline}</p>
              {s.points.length > 0 && <ul>{s.points.map((p, i) => <li key={i}>{p}</li>)}</ul>}
            </div>
          );
        })}
      </div>

      <h3 className="fa-sub">Historical comparison</h3>
      <div className="table-wrap">
        <table className="fin-table">
          <thead>
            <tr><th>Metric</th>{d.history.map((y) => <th key={y.date}>{y.label}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map(([label, key, fmt]) => (
              <tr key={key}>
                <td>{label}</td>
                {d.history.map((y) => (
                  <td key={y.date} className={y[key] != null && y[key] < 0 ? "neg" : ""}>{fmt(y[key])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className="fa-sub">Peer comparison</h3>
      <form className="fa-peer-form" onSubmit={(e) => { e.preventDefault(); setPeers(peerInput.trim()); }}>
        <input className="input" value={peerInput} onChange={(e) => setPeerInput(e.target.value)}
          placeholder="Peer tickers, comma separated (up to 4), e.g. INFY, WIPRO" aria-label="Peer tickers" />
        <button className="btn btn-ghost btn-sm" type="submit">Compare</button>
        {peers && <button className="btn btn-ghost btn-sm" type="button" onClick={() => { setPeerInput(""); setPeers(""); }}>Clear</button>}
      </form>
      {!d.peers.available && <div className="notice">{d.peers.reason}</div>}
      {d.peers.available && (
        <div className="table-wrap">
          <table className="fin-table">
            <thead>
              <tr><th>Company</th><th>FY</th>{d.peers.metrics.map((m) => <th key={m.key}>{m.label}</th>)}</tr>
            </thead>
            <tbody>
              {d.peers.companies.map((c, i) => (
                <tr key={c.ticker}>
                  <td><strong>{c.ticker}</strong>{i === 0 ? " (this stock)" : ""}</td>
                  <td>{c.fiscal_year}</td>
                  {d.peers.metrics.map((m) => <td key={m.key}>{m.kind === "pct" ? fp(c[m.key]) : fx(c[m.key], 1)}</td>)}
                </tr>
              ))}
              <tr>
                <td><em>Peer median</em></td><td />
                {d.peers.metrics.map((m) => <td key={m.key}>{m.kind === "pct" ? fp(m.peer_median) : fx(m.peer_median, 1)}</td>)}
              </tr>
              <tr>
                <td><em>This stock is</em></td><td />
                {d.peers.metrics.map((m) => <td key={m.key}>{m.position ?? "—"}</td>)}
              </tr>
            </tbody>
          </table>
        </div>
      )}
      {d.peers.available && <p className="hint">{d.peers.note}</p>}
      {d.peers.unavailable?.length > 0 && (
        <div className="notice notice-warn" style={{ marginTop: 8 }}>
          No data for: {d.peers.unavailable.map((u) => u.ticker).join(", ")}.
        </div>
      )}
      {d.peers_invalid?.length > 0 && (
        <div className="notice notice-warn" style={{ marginTop: 8 }}>Ignored invalid tickers: {d.peers_invalid.join(", ")}.</div>
      )}

      <h3 className="fa-sub">Missing or inconsistent data</h3>
      {q.issues.length === 0 ? (
        <p className="hint">No problems found in the financial data.</p>
      ) : (
        <ul className="issue-list">
          {q.issues.map((i, k) => (
            <li key={k}>
              <span className={i.severity === "error" ? "down" : ""} style={i.severity === "warning" ? { color: "var(--eq-warn)" } : null}>●</span>
              <span>{i.message}</span>
            </li>
          ))}
        </ul>
      )}

      <p className="hint">{d.limitations.join(" ")}</p>
      <p className="hint">Source: {d.meta.provider}. <button className="chip" onClick={() => setNonce((n) => n + 1)}>Refresh</button></p>
    </section>
  );
}
