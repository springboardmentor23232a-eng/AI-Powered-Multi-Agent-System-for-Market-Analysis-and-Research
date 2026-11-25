import PerformanceChart from "./PerformanceChart";
import IntegrityPanel from "./IntegrityPanel";

export default function ChartView({ active, data, range, onRange, onGoSearch }) {
  if (!active || !data) {
    return (
      <section className="panel empty-state">
        <h2>No stock selected</h2>
        <p>Open a stock from Stock search first. Its price chart will show up here.</p>
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={onGoSearch}>
          Go to stock search
        </button>
      </section>
    );
  }

  const { quote, history, profile } = data;
  const currency = quote.data?.currency || profile.data?.profile?.currency || "USD";
  const name = quote.data?.company_name || profile.data?.profile?.company_name;

  return (
    <div className="stack">
      <div className="stock-head">
        <div>
          <h2>{name || active.ticker}</h2>
          <p className="sub">{quote.data?.ticker || active.ticker} on {active.market}</p>
        </div>
      </div>
      <div className="chart-grid">
        <PerformanceChart history={history} range={range} onRange={onRange} currency={currency} />
        <IntegrityPanel history={history} quote={quote.data} />
      </div>
    </div>
  );
}
