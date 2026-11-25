import { useState } from "react";
import { useApi } from "../hooks";
import { dateTimeOf, formatCell } from "../format";
import Icon from "./Icon";

const TABS = [
  { id: "income_statement", label: "Income statement" },
  { id: "balance_sheet", label: "Balance sheet" },
  { id: "cash_flow", label: "Cash flow" },
];

export default function Statements({ ticker, market, currency }) {
  const [tab, setTab] = useState("income_statement");
  const [freq, setFreq] = useState("annual");
  const [open, setOpen] = useState(true);
  const [nonce, setNonce] = useState(0);
  const res = useApi(
    `/market/${encodeURIComponent(ticker)}/statements?market=${market}&frequency=${freq}`,
    nonce
  );
  const table = res.data?.statements?.[tab];

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Financial statements</h2>
          <p className="panel-sub">
            {res.data
              ? `${freq === "annual" ? "Annual" : "Quarterly"} reports in ${currency}, retrieved ${dateTimeOf(res.data.meta.retrieved_at)}`
              : "Loading statements"}
          </p>
        </div>
        <div className="row">
          <button className="btn btn-ghost btn-sm" onClick={() => setNonce((n) => n + 1)}>
            <Icon name="refresh" size={14} /> Refresh
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => setOpen((o) => !o)} aria-expanded={open}>
            <Icon name={open ? "up" : "down"} size={14} /> {open ? "Collapse" : "Expand"}
          </button>
        </div>
      </div>

      {open && (
        <>
          <div className="statement-bar">
            <div className="tabs" role="tablist">
              {TABS.map((t) => (
                <button key={t.id} role="tab" aria-selected={tab === t.id}
                  className={`tab ${tab === t.id ? "is-on" : ""}`} onClick={() => setTab(t.id)}>
                  {t.label}
                </button>
              ))}
            </div>
            <div className="segmented" role="group" aria-label="Frequency">
              <button className={freq === "annual" ? "is-on" : ""} onClick={() => setFreq("annual")}>Annual</button>
              <button className={freq === "quarterly" ? "is-on" : ""} onClick={() => setFreq("quarterly")}>Quarterly</button>
            </div>
          </div>

          {res.loading && <div className="skeleton" style={{ height: 200, marginTop: 12, borderRadius: 10 }} />}
          {res.error && <div className="notice notice-warn" style={{ marginTop: 12 }}>Statements unavailable: {res.error}</div>}
          {table && table.rows.length === 0 && (
            <div className="empty-note" style={{ marginTop: 12 }}>The provider has no data for this statement.</div>
          )}
          {table && table.rows.length > 0 && (
            <div className="table-wrap">
              <table className="fin-table">
                <thead>
                  <tr>
                    <th>Line item</th>
                    {table.columns.map((c) => <th key={c}>{c}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {table.rows.map((r) => (
                    <tr key={r.item}>
                      <td>{r.item}</td>
                      {r.values.map((v, i) => (
                        <td key={i} className={v != null && v < 0 ? "neg" : ""}>{formatCell(r.item, v, currency)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}
