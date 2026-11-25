import { int, money, num, pct } from "../format";

function Sparkline({ values, up }) {
  if (!values?.length) return null;
  const w = 96, h = 32;
  const min = Math.min(...values), max = Math.max(...values);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => `${(i / (values.length - 1)) * w},${h - 3 - ((v - min) / span) * (h - 6)}`)
    .join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} aria-label="Last 30 closes">
      <polyline points={pts} fill="none" stroke={up ? "var(--eq-up)" : "var(--eq-down)"} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

function RangeBar({ low, high, value }) {
  const p = high > low ? Math.min(100, Math.max(0, ((value - low) / (high - low)) * 100)) : 50;
  return (
    <div className="rangebar" role="img" aria-label={`Price is at ${p.toFixed(0)} percent of the range`}>
      <i style={{ left: `${p}%` }} />
    </div>
  );
}

export default function QuoteCards({ quote, currency }) {
  if (quote.loading || (!quote.data && !quote.error)) {
    return (
      <div className="quote-grid">
        {[0, 1, 2, 3].map((i) => <div key={i} className="panel stat skeleton" />)}
      </div>
    );
  }
  if (quote.error) return <div className="notice notice-warn">Quote unavailable: {quote.error}</div>;

  const q = quote.data;
  const up = q.change >= 0;
  return (
    <div className="quote-grid">
      <div className="panel stat">
        <div className="stat-top">
          <span className="stat-label">Last close, {q.as_of}</span>
          <span className={`pill ${up ? "pill-up" : "pill-down"}`}>{pct(q.change_pct)}</span>
        </div>
        <div className="stat-value display">{money(q.price, currency)}</div>
        <div className="stat-foot">
          <span>Previous {money(q.prev_close, currency)}</span>
          <Sparkline values={q.spark} up={up} />
        </div>
      </div>

      <div className="panel stat">
        <span className="stat-label">Day range</span>
        <div className="stat-value md display">{money(q.day_low, currency)} to {money(q.day_high, currency)}</div>
        <div className="stat-foot" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <RangeBar low={q.day_low} high={q.day_high} value={q.price} />
          <span>Latest trading day</span>
        </div>
      </div>

      <div className="panel stat">
        <span className="stat-label">52-week range</span>
        <div className="stat-value md display">{money(q.week52_low, currency)} to {money(q.week52_high, currency)}</div>
        <div className="stat-foot" style={{ flexDirection: "column", alignItems: "stretch" }}>
          <RangeBar low={q.week52_low} high={q.week52_high} value={q.price} />
          <div className="range-labels"><span>Low</span><span>High</span></div>
        </div>
      </div>

      <div className="panel stat">
        <div className="split">
          <div>
            <span className="stat-label">P/E ratio</span>
            <div className="stat-value md display">{q.pe_ratio == null ? "—" : num(q.pe_ratio)}</div>
          </div>
          <div>
            <span className="stat-label">Volume</span>
            <div className="stat-value md display">{int(q.volume)}</div>
          </div>
        </div>
        <div className="stat-foot"><span>P/E is provider-reported, trailing twelve months</span></div>
      </div>
    </div>
  );
}
