import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import API from "../services/api";

function StockComparisonChart() {
  const [stock1, setStock1] = useState("RELIANCE");
  const [stock2, setStock2] = useState("TCS");
  const [period, setPeriod] = useState("1y");
  const [exchange, setExchange] = useState("NSI");
  const [comparisonData, setComparisonData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const stock1Return = comparisonData.length
    ? comparisonData[comparisonData.length - 1].stock1 - 100
    : 0;

  const stock2Return = comparisonData.length
    ? comparisonData[comparisonData.length - 1].stock2 - 100
    : 0;

  const betterPerformer =
    stock1Return > stock2Return
      ? stock1.trim().toUpperCase()
      : stock2Return > stock1Return
        ? stock2.trim().toUpperCase()
        : "Both stocks performed equally";

  async function compareStocks(event) {
    event.preventDefault();

    const ticker1 = stock1.trim().toUpperCase();
    const ticker2 = stock2.trim().toUpperCase();

    if (!ticker1 || !ticker2) {
      setError("Please enter both stock symbols.");
      return;
    }

    if (ticker1 === ticker2) {
      setError("Please enter two different stocks.");
      return;
    }

    setLoading(true);
    setError("");
    setComparisonData([]);

    try {
      const [response1, response2] = await Promise.all([
        API.get(`/market-data/${ticker1}/history`, {
          params: { period, exchange },
        }),
        API.get(`/market-data/${ticker2}/history`, {
          params: { period, exchange },
        }),
      ]);

      const history1 = response1.data.history;
      const history2 = response2.data.history;

      if (!history1.length || !history2.length) {
        throw new Error("Insufficient historical data for comparison.");
      }

      const history2Map = new Map(
        history2.map((item) => [item.date, item.price]),
      );

      const commonHistory = history1.filter((item) =>
        history2Map.has(item.date),
      );

      if (!commonHistory.length) {
        throw new Error("No matching trading dates found.");
      }

      const firstPrice1 = commonHistory[0].price;
      const firstPrice2 = history2Map.get(commonHistory[0].date);

      const combinedData = commonHistory.map((item) => ({
        date: item.date,
        stock1: (item.price / firstPrice1) * 100,
        stock2: (history2Map.get(item.date) / firstPrice2) * 100,
      }));

      if (!combinedData.length) {
        throw new Error("No matching trading dates found.");
      }

      setComparisonData(combinedData);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          "Unable to compare stocks.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="stock-comparison-chart">
      <div className="comparison-header">
        <div>
          <h2>Live Stock Performance Comparison</h2>
          <p>Compare historical performance of two companies</p>
        </div>

        <span className="comparison-badge">Historical Data</span>
      </div>

      <form onSubmit={compareStocks} className="comparison-form">
        <input
          type="text"
          value={stock1}
          onChange={(event) => setStock1(event.target.value)}
          placeholder="First stock (e.g. RELIANCE)"
        />

        <input
          type="text"
          value={stock2}
          onChange={(event) => setStock2(event.target.value)}
          placeholder="Second stock (e.g. TCS)"
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
          {loading ? "Comparing..." : "Compare Stocks"}
        </button>
      </form>

      {error && <p className="stock-search-error">{error}</p>}

      {comparisonData.length > 0 && (
        <>
          <div className="comparison-statistics">
            <div className="comparison-stat-card">
              <p>{stock1.trim().toUpperCase()} Return</p>
              <h3
                className={
                  stock1Return >= 0 ? "stock-positive" : "stock-negative"
                }
              >
                {stock1Return >= 0 ? "+" : ""}
                {stock1Return.toFixed(2)}%
              </h3>
            </div>

            <div className="comparison-stat-card">
              <p>{stock2.trim().toUpperCase()} Return</p>
              <h3
                className={
                  stock2Return >= 0 ? "stock-positive" : "stock-negative"
                }
              >
                {stock2Return >= 0 ? "+" : ""}
                {stock2Return.toFixed(2)}%
              </h3>
            </div>

            <div className="comparison-stat-card">
              <p>Better Performer</p>
              <h3>{betterPerformer}</h3>
            </div>
          </div>

          <div className="comparison-line-chart">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={30} />
                <YAxis
                  domain={["auto", "auto"]}
                  tickFormatter={(value) => value.toFixed(0)}
                />
                <Tooltip
                  formatter={(value) => [
                    Number(value).toFixed(2),
                    "Performance (Base 100)",
                  ]}
                  labelFormatter={(label) => `Date: ${label}`}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="stock1"
                  name={stock1.trim().toUpperCase()}
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="stock2"
                  name={stock2.trim().toUpperCase()}
                  stroke="#0d9488"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}

export default StockComparisonChart;
