import { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import API from "../services/api";

function StockHistoryChart() {
  const [symbol, setSymbol] = useState("RELIANCE");
  const [period, setPeriod] = useState("1y");
  const [exchange, setExchange] = useState("NSI");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchedStock, setSearchedStock] = useState("");
  const prices = history.map((item) => item.price);

  const highestPrice = prices.length ? Math.max(...prices) : 0;

  const lowestPrice = prices.length ? Math.min(...prices) : 0;

  const averagePrice = prices.length
    ? prices.reduce((total, price) => total + price, 0) / prices.length
    : 0;
  const firstPrice = prices.length ? prices[0] : 0;
  const latestPrice = prices.length ? prices[prices.length - 1] : 0;

  const absoluteChange = latestPrice - firstPrice;

  const percentageChange = firstPrice ? (absoluteChange / firstPrice) * 100 : 0;
  const performanceMessage =
    percentageChange > 0
      ? `${searchedStock} gained ${percentageChange.toFixed(2)}% during the selected period.`
      : percentageChange < 0
        ? `${searchedStock} declined by ${Math.abs(percentageChange).toFixed(2)}% during the selected period.`
        : `${searchedStock} showed no price change during the selected period.`;

  const marketTrend =
    percentageChange > 0.5
      ? "Bullish"
      : percentageChange < -0.5
        ? "Bearish"
        : "Neutral";

  async function fetchHistory(event) {
    event.preventDefault();

    const ticker = symbol.trim().toUpperCase();

    if (!ticker) {
      setError("Please enter a stock symbol.");
      return;
    }

    setLoading(true);
    setError("");
    setHistory([]);

    try {
      const response = await API.get(`/market-data/${ticker}/history`, {
        params: { period, exchange },
      });

      setHistory(response.data.history);
      setSearchedStock(response.data.ticker);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to fetch historical stock data.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="history-chart-container">
      <h2>Historical Stock Performance</h2>

      <form onSubmit={fetchHistory} className="history-form">
        <input
          type="text"
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
          placeholder="Enter stock symbol"
        />
        <select
          value={exchange}
          onChange={(event) => setExchange(event.target.value)}
        >
          <option value="NSI">NSE - India</option>
          <option value="BSE">BSE - India</option>
          <option value="NASDAQ">NASDAQ - USA</option>
          <option value="NYSE">NYSE - USA</option>
        </select>
        <select
          value={period}
          onChange={(event) => setPeriod(event.target.value)}
        >
          <option value="1mo">1 Month</option>
          <option value="3mo">3 Months</option>
          <option value="6mo">6 Months</option>
          <option value="1y">1 Year</option>
          <option value="5y">5 Years</option>
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "View History"}
        </button>
      </form>

      {error && <p className="stock-search-error">{error}</p>}

      {history.length > 0 && (
        <>
          <h3>
            {searchedStock} — {period} performance
          </h3>
          <div className="stock-statistics">
            <div className="stat-card">
              <p>Highest Price</p>
              <h3>₹{highestPrice.toFixed(2)}</h3>
            </div>

            <div className="stat-card">
              <p>Lowest Price</p>
              <h3>₹{lowestPrice.toFixed(2)}</h3>
            </div>

            <div className="stat-card">
              <p>Average Price</p>
              <h3>₹{averagePrice.toFixed(2)}</h3>
            </div>

            <div className="stat-card">
              <p>Absolute Price Change</p>
              <h3
                className={
                  absoluteChange >= 0 ? "stock-positive" : "stock-negative"
                }
              >
                {absoluteChange >= 0 ? "+" : "-"}₹
                {Math.abs(absoluteChange).toFixed(2)}
              </h3>
            </div>

            <div className="stat-card">
              <p>Period Change</p>
              <h3
                className={
                  percentageChange >= 0 ? "stock-positive" : "stock-negative"
                }
              >
                {percentageChange >= 0 ? "+" : ""}
                {percentageChange.toFixed(2)}%
              </h3>
            </div>
          </div>
          <div className="performance-summary">
            <h3>Performance Summary</h3>

            <p>{performanceMessage}</p>

            <p>Highest closing price: ₹{highestPrice.toFixed(2)}</p>

            <p>Lowest closing price: ₹{lowestPrice.toFixed(2)}</p>
          </div>
          <div className="market-trend-indicator">
            <h3>Market Trend</h3>

            <span
              className={
                marketTrend === "Bullish"
                  ? "trend-bullish"
                  : marketTrend === "Bearish"
                    ? "trend-bearish"
                    : "trend-neutral"
              }
            >
              {marketTrend}
            </span>
          </div>
          <div className="history-chart">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={30} />

                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={(value) => `₹${value}`}
                />

                <Tooltip
                  formatter={(value) => [
                    `₹${Number(value).toFixed(2)}`,
                    "Closing Price",
                  ]}
                  labelFormatter={(label) => `Date: ${label}`}
                />

                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

export default StockHistoryChart;
