import Icon from "./Icon";
import QuoteCards from "./QuoteCards";
import PerformanceChart from "./PerformanceChart";
import IntegrityPanel from "./IntegrityPanel";
import ProfilePanel from "./ProfilePanel";
import Statements from "./Statements";
import FundamentalCard from "./FundamentalCard";

export default function StockView({ active, data, range, onRange, saved, onAddWatch, onResearch }) {
  const { ticker, market } = active;
  const { quote, history, profile } = data;

  const currency = quote.data?.currency || profile.data?.profile?.currency || "USD";
  const name = quote.data?.company_name || profile.data?.profile?.company_name;
  const symbol = quote.data?.ticker || ticker;
  const isSaved = saved.some((s) => s.ticker === ticker || s.ticker === symbol);

  if (quote.error && history.error) {
    return (
      <div className="notice notice-warn">
        No data found for {ticker} on {market}. {quote.error} Check that the market matches the ticker,
        for example TCS on NSE or AAPL on NASDAQ.
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="stock-head">
        <div>
          <h2>{name || ticker}</h2>
          <p className="sub">{symbol} on {market}</p>
        </div>
        <div className="row">
          <button
            className="btn btn-ghost"
            disabled={isSaved}
            onClick={() => onAddWatch({ ticker: symbol, company_name: name, market })}
          >
            <Icon name={isSaved ? "check" : "bookmark"} /> {isSaved ? "In watchlist" : "Add to watchlist"}
          </button>
          <button
            className="btn btn-primary"
            onClick={() => onResearch({ ticker: symbol, company_name: name, market, analysis_period: range })}
          >
            <Icon name="trend" /> Run research
          </button>
        </div>
      </div>

      <QuoteCards quote={quote} currency={currency} />

      <div className="chart-grid">
        <PerformanceChart history={history} range={range} onRange={onRange} currency={currency} />
        <IntegrityPanel history={history} quote={quote.data} />
      </div>

      <ProfilePanel profile={profile} />
      <Statements ticker={ticker} market={market} currency={currency} />
      <FundamentalCard ticker={ticker} market={market} currency={currency} />
    </div>
  );
}
