import { useEffect, useState } from "react";
import API from "../services/api";

function Watchlist() {
  const [stocks, setStocks] = useState([]);
  const [symbol, setSymbol] = useState("");
  const [loading, setLoading] = useState(true);
  const [marketData, setMarketData] = useState({});
  const [refreshing, setRefreshing] = useState(false);
  const [researchingTicker, setResearchingTicker] = useState(null);
  const [researchPeriod, setResearchPeriod] = useState("1y");

  // Fetch saved stocks when the component loads
  useEffect(() => {
    fetchStocks();

    // Listen for newly added stocks
    window.addEventListener("watchlistUpdated", fetchStocks);

    // Clean up the event listener
    return () => {
      window.removeEventListener("watchlistUpdated", fetchStocks);
    };
  }, []);

  async function fetchStocks() {
    try {
      const response = await API.get("/watchlist/");
      setStocks(response.data);
      fetchMarketData(response.data);
    } catch (error) {
      console.error("Error fetching watchlist:", error);
      alert("Unable to load your watchlist.");
    } finally {
      setLoading(false);
    }
  }

  async function fetchMarketData(stockList) {
    const results = await Promise.all(
      stockList.map(async (stock) => {
        try {
          const exchange =
            stock.market ||
            (stock.ticker.endsWith(".NS")
              ? "NSI"
              : stock.ticker.endsWith(".BO")
                ? "BSE"
                : "NASDAQ");

          const response = await API.get(`/market-data/${stock.ticker}`, {
            params: { exchange },
          });

          return [stock.ticker, response.data];
        } catch (error) {
          console.error(`Error fetching ${stock.ticker}:`, error);

          return [stock.ticker, null];
        }
      }),
    );

    setMarketData(Object.fromEntries(results));
  }

  async function refreshMarketData() {
    setRefreshing(true);

    try {
      await fetchMarketData(stocks);
    } finally {
      setRefreshing(false);
    }
  }

  // Add a stock to PostgreSQL
  async function addStock(event) {
    event.preventDefault();

    const newSymbol = symbol.trim().toUpperCase();

    if (!newSymbol) return;

    try {
      const response = await API.post("/watchlist/", {
        ticker: newSymbol,
      });

      setStocks([...stocks, response.data]);
      fetchMarketData([...stocks, response.data]);
      setSymbol("");
    } catch (error) {
      if (error.response?.status === 409) {
        alert("This stock is already in your watchlist.");
      } else {
        alert("Unable to add stock. Please try again.");
      }
    }
  }

  // Remove a stock from PostgreSQL
  async function removeStock(stockSymbol) {
    try {
      await API.delete(`/watchlist/${stockSymbol}`);

      setStocks(stocks.filter((stock) => stock.ticker !== stockSymbol));
      setMarketData((prevData) => {
        const updatedData = { ...prevData };
        delete updatedData[stockSymbol];
        return updatedData;
      });
    } catch (error) {
      console.error("Error removing stock:", error);
      alert("Unable to remove stock.");
    }
  }

  async function startResearch(stock) {
    const stockData = marketData[stock.ticker];

    if (!stockData) {
      alert("Market data is not available for this stock.");
      return;
    }

    const market =
      stock.market ||
      (stock.ticker.endsWith(".NS")
        ? "NSI"
        : stock.ticker.endsWith(".BO")
          ? "BSE"
          : "NASDAQ");

    try {
      setResearchingTicker(stock.ticker);

      await API.post("/research/tasks", {
        company_name: stockData.company_name,
        ticker: stock.ticker,
        market: market,
        analysis_period: researchPeriod,
      });

      window.dispatchEvent(new Event("researchHistoryUpdated"));

      alert(`Research started for ${stock.ticker}!`);
    } catch (error) {
      console.error("Research creation error:", error.response?.data);

      alert(error.response?.data?.detail || "Unable to start research.");
    } finally {
      setResearchingTicker(null);
    }
  }

  if (loading) {
    return <p>Loading your watchlist...</p>;
  }

  return (
    <div className="watchlist-container">
      <div className="watchlist-header">
        <h2>My Stock Watchlist</h2>

        <button
          onClick={refreshMarketData}
          disabled={refreshing || stocks.length === 0}
        >
          {refreshing ? "Refreshing..." : "↻ Refresh Prices"}
        </button>
      </div>

      <form onSubmit={addStock} className="watchlist-form">
        <input
          type="text"
          placeholder="Enter stock symbol (e.g. WIPRO)"
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
        />

        <button type="submit">Add Stock</button>
      </form>

      <div className="watchlist-research-period">
        <label htmlFor="research-period">Research Analysis Period:</label>

        <select
          id="research-period"
          value={researchPeriod}
          onChange={(event) => setResearchPeriod(event.target.value)}
        >
          <option value="1mo">1 Month</option>
          <option value="3mo">3 Months</option>
          <option value="6mo">6 Months</option>
          <option value="1y">1 Year</option>
          <option value="5y">5 Years</option>
        </select>
      </div>
      <div className="watchlist-list">
        {stocks.length === 0 ? (
          <p>Your watchlist is empty. Add your first stock!</p>
        ) : (
          stocks.map((stock) => (
            <div key={stock.saved_stock_id} className="watchlist-item">
              <h3>{stock.ticker}</h3>

              <p>
                {marketData[stock.ticker]?.company_name ||
                  "Loading company name..."}
              </p>
              {marketData[stock.ticker] ? (
                <>
                  <p>
                    Price:{" "}
                    {marketData[stock.ticker].current_price != null
                      ? marketData[stock.ticker].current_price
                      : "N/A"}
                  </p>

                  <p>
                    Previous Close:{" "}
                    {marketData[stock.ticker].previous_close != null
                      ? marketData[stock.ticker].previous_close
                      : "N/A"}
                  </p>
                  {marketData[stock.ticker].percentage_change != null ? (
                    <div
                      style={{
                        color:
                          marketData[stock.ticker].percentage_change >= 0
                            ? "#16a34a"
                            : "#dc2626",
                        fontWeight: "bold",
                      }}
                    >
                      {marketData[stock.ticker].percentage_change >= 0
                        ? "▲"
                        : "▼"}{" "}
                      {Math.abs(
                        marketData[stock.ticker].percentage_change,
                      ).toFixed(2)}
                      %<span style={{ fontWeight: "normal" }}> Today</span>
                    </div>
                  ) : (
                    <p>Daily change unavailable</p>
                  )}
                </>
              ) : (
                <p>Loading market data...</p>
              )}
              <button
                className="start-research-button"
                onClick={() => startResearch(stock)}
                disabled={
                  researchingTicker === stock.ticker ||
                  !marketData[stock.ticker]
                }
              >
                {researchingTicker === stock.ticker
                  ? "Starting..."
                  : "Start Research"}
              </button>
              <button
                className="watchlist-remove"
                onClick={() => removeStock(stock.ticker)}
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Watchlist;
