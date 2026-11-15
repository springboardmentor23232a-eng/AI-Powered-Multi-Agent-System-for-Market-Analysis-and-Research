import { useEffect, useState } from "react";
import API from "../services/api";
import "./MarketMovers.css";

const selectedStocks = [
  { symbol: "RELIANCE" },
  { symbol: "TCS" },
  { symbol: "INFY" },
  { symbol: "HDFCBANK" },
  { symbol: "ICICIBANK" },
  { symbol: "SBIN" },
  { symbol: "BHARTIARTL" },
  { symbol: "ITC" },
  { symbol: "HINDUNILVR" },
  { symbol: "LT" },
  { symbol: "AXISBANK" },
  { symbol: "KOTAKBANK" },
  { symbol: "BAJFINANCE" },
  { symbol: "MARUTI" },
  { symbol: "TATAMOTORS" },
  { symbol: "SUNPHARMA" },
  { symbol: "NTPC" },
  { symbol: "POWERGRID" },
  { symbol: "ONGC" },
  { symbol: "COALINDIA" },
  { symbol: "TRENT" },
  { symbol: "WIPRO" },
  { symbol: "HCLTECH" },
  { symbol: "TECHM" },
  { symbol: "TATASTEEL" },
  { symbol: "JSWSTEEL" },
  { symbol: "ADANIENT" },
  { symbol: "ADANIPORTS" },
  { symbol: "ASIANPAINT" },
  { symbol: "TITAN" },
];

function MarketMovers() {
  const [topGainers, setTopGainers] = useState([]);
  const [topLosers, setTopLosers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMarketMovers() {
      setLoading(true);
      setError("");

      try {
        const results = await Promise.allSettled(
          selectedStocks.map((stock) =>
            API.get(`/market-data/${stock.symbol}`, {
              params: { exchange: "NSI" },
            }),
          ),
        );

        const marketStocks = results
          .filter((result) => result.status === "fulfilled")
          .map((result) => result.value.data);

        if (marketStocks.length === 0) {
          throw new Error("Unable to fetch market data.");
        }

        const validStocks = marketStocks.filter(
          (stock) =>
            stock.percentage_change !== null &&
            stock.percentage_change !== undefined,
        );

        const sortedStocks = validStocks.sort(
          (a, b) => b.percentage_change - a.percentage_change,
        );

        setTopGainers(
          sortedStocks
            .filter((stock) => stock.percentage_change > 0)
            .slice(0, 4),
        );

        setTopLosers(
          sortedStocks
            .filter((stock) => stock.percentage_change < 0)
            .sort((a, b) => a.percentage_change - b.percentage_change)
            .slice(0, 4),
        );
      } catch (err) {
        setError("Unable to load market movers. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    fetchMarketMovers();
  }, []);

  return (
    <div className="market-movers">
      <div className="market-movers-header">
        <div>
          <h2>Market Gainers & Losers</h2>
          <p>Daily percentage movements of selected stocks</p>
        </div>

        <span className="market-demo-badge">Market Data</span>
      </div>

      {loading && <p>Loading market movers...</p>}

      {error && <p className="stock-search-error">{error}</p>}

      {!loading && !error && (
        <div className="market-movers-grid">
          <div className="movers-card">
            <h3 className="gainers-title">↑ Top Gainers</h3>

            {topGainers.length > 0 ? (
              topGainers.map((stock) => (
                <div className="mover-item" key={stock.ticker}>
                  <div>
                    <h4>{stock.ticker.replace(".NS", "")}</h4>
                    <p>{stock.company_name}</p>
                  </div>

                  <span className="gain-value">
                    +{stock.percentage_change.toFixed(2)}%
                  </span>
                </div>
              ))
            ) : (
              <p>No gainers in the selected stocks.</p>
            )}
          </div>

          <div className="movers-card">
            <h3 className="losers-title">↓ Top Losers</h3>

            {topLosers.length > 0 ? (
              topLosers.map((stock) => (
                <div className="mover-item" key={stock.ticker}>
                  <div>
                    <h4>{stock.ticker.replace(".NS", "")}</h4>
                    <p>{stock.company_name}</p>
                  </div>

                  <span className="loss-value">
                    {stock.percentage_change.toFixed(2)}%
                  </span>
                </div>
              ))
            ) : (
              <p>No losers in the selected stocks.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default MarketMovers;
