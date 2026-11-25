import { dateOf } from "../format";
import Icon from "./Icon";

export default function WatchlistCard({ saved, prefs, limit, onViewAll, onResearch, onRemove, onView }) {
  const shown = limit ? saved.slice(0, limit) : saved;
  return (
    <section className="panel" id="watchlist">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Watchlist</h2>
          <p className="panel-sub">{saved.length} saved stocks</p>
        </div>
        {onViewAll && saved.length > shown.length && (
          <button className="btn btn-ghost btn-sm" onClick={onViewAll}>View all</button>
        )}
      </div>

      {saved.length === 0 ? (
        <div className="empty-note">Nothing saved yet. Use the bookmark button on a search result.</div>
      ) : (
        <table className="wl-table">
          <thead>
            <tr><th>Ticker</th><th>Company</th><th>Market</th><th>Saved</th><th className="right">Actions</th></tr>
          </thead>
          <tbody>
            {shown.map((s) => (
              <tr key={s.saved_stock_id}>
                <td>
                  <button className="link-btn" onClick={() => onView({ ticker: s.ticker, market: s.market || prefs.market })}>
                    {s.ticker}
                  </button>
                </td>
                <td>{s.company_name || "—"}</td>
                <td>{s.market ? <span className="badge">{s.market}</span> : "—"}</td>
                <td>{dateOf(s.created_at)}</td>
                <td className="right">
                  <div className="row" style={{ justifyContent: "flex-end", flexWrap: "nowrap" }}>
                    <button
                      className="btn btn-primary btn-sm"
                      onClick={() => onResearch({ ticker: s.ticker, company_name: s.company_name, market: s.market || prefs.market, analysis_period: prefs.analysis_period })}
                    >
                      Research
                    </button>
                    <button className="icon-btn" aria-label={`Remove ${s.ticker}`} title="Remove" onClick={() => onRemove(s)}>
                      <Icon name="trash" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
