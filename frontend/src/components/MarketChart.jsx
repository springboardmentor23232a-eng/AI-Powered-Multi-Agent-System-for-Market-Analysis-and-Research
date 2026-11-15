import { useEffect, useState } from "react";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import API from "../services/api";

function MarketChart() {
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMarketData() {
      try {
        const response = await API.get("/market-data/^NSEI/history", {
          params: {
            period: "1mo",
            exchange: "NSI",
          },
        });

        setMarketData(response.data.history);
      } catch (err) {
        console.error("Failed to fetch NIFTY 50 data:", err);

        setError("Unable to load NIFTY 50 market data.");
      } finally {
        setLoading(false);
      }
    }

    fetchMarketData();
  }, []);

  if (loading) {
    return <p>Loading NIFTY 50 market data...</p>;
  }

  if (error) {
    return <p className="stock-search-error">{error}</p>;
  }

  if (marketData.length === 0) {
    return <p>No NIFTY 50 historical data available.</p>;
  }

  return (
    <div className="market-chart">
      <h2>NIFTY 50 – Monthly Performance</h2>

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={marketData}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={30} />

          <YAxis domain={["auto", "auto"]} />

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
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default MarketChart;
