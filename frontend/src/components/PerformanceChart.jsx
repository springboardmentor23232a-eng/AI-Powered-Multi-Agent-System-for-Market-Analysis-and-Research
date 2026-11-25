import { useState } from "react";
import { PERIODS } from "../constants";
import { int, money } from "../format";
import PlotChart from "./PlotChart";

export default function PerformanceChart({ history, range, onRange, currency }) {
  const [mode, setMode] = useState("line");
  const [hover, setHover] = useState(null);
  const rows = history.data?.rows ?? [];
  const row = (hover != null ? rows[hover] : null) ?? rows[rows.length - 1];

  return (
    <section className="panel" id="chart">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Price performance</h2>
          <p className="panel-sub">
            {history.data
              ? `${history.data.count} trading days of daily prices, unadjusted`
              : "Loading price history"}
          </p>
        </div>
        <div className="controls">
          <div className="segmented" role="group" aria-label="Chart type">
            <button className={mode === "line" ? "is-on" : ""} onClick={() => setMode("line")}>Line</button>
            <button className={mode === "candles" ? "is-on" : ""} onClick={() => setMode("candles")}>Candles</button>
          </div>
          <div className="segmented" role="group" aria-label="Time range">
            {PERIODS.map((p) => (
              <button key={p.value} className={range === p.value ? "is-on" : ""} onClick={() => onRange(p.value)}>
                {p.short}
              </button>
            ))}
          </div>
        </div>
      </div>

      {history.error ? (
        <div className="notice notice-warn">Price history unavailable: {history.error}</div>
      ) : (
        <>
          {row && (
            <dl className="readout">
              <div><dt>Date</dt><dd>{row.date}</dd></div>
              <div><dt>Close</dt><dd>{money(row.close, currency)}</dd></div>
              <div><dt>Open</dt><dd>{money(row.open, currency)}</dd></div>
              <div><dt>High</dt><dd>{money(row.high, currency)}</dd></div>
              <div><dt>Low</dt><dd>{money(row.low, currency)}</dd></div>
              <div><dt>Volume</dt><dd>{int(row.volume)}</dd></div>
            </dl>
          )}
          <div className="plot-wrap">
            {history.loading && <div className="plot-loading">Loading chart…</div>}
            <PlotChart rows={rows} mode={mode} onHover={setHover} />
          </div>
        </>
      )}
    </section>
  );
}
