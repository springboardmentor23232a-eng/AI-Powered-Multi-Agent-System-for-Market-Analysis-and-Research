import { num, pct } from "../format";

const PLANNED = ["Revenue growth", "Profit margins", "Return on equity", "Debt to equity", "Current ratio", "Free cash flow", "Peer comparison"];

export default function FundamentalCard({ profile }) {
  const p = profile.data?.profile;
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Fundamental analysis</h2>
          <p className="panel-sub">Calculated ratios and a written assessment arrive with the Fundamental agent (Weeks 3 and 4)</p>
        </div>
        <span className="badge">Not built yet</span>
      </div>

      <div className="fund-grid">
        <div className="fund-item">
          <span className="stat-label">P/E, trailing</span>
          <div className="stat-value display">{num(p?.trailing_pe)}</div>
        </div>
        <div className="fund-item">
          <span className="stat-label">Price to book</span>
          <div className="stat-value display">{num(p?.price_to_book)}</div>
        </div>
        <div className="fund-item">
          <span className="stat-label">Return on equity</span>
          <div className="stat-value display">{p?.return_on_equity == null ? "—" : pct(p.return_on_equity * 100).replace("+", "")}</div>
        </div>
      </div>
      <p className="hint">These three figures are reported by the provider. The agent will calculate its own from the statements above and flag any mismatch.</p>

      <div className="planned">
        <span className="chips-label">Coming next</span>
        {PLANNED.map((t) => <span key={t} className="badge">{t}</span>)}
      </div>
    </section>
  );
}
