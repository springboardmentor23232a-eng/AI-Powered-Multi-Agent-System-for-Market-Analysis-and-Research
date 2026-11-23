import { useState } from "react";
import API from "../services/api";

function StockOHLCV() {
  const [symbol, setSymbol] = useState("RELIANCE");
  const [period, setPeriod] = useState("1y");
  const [exchange, setExchange] = useState("NSI");
  const [ohlcvData, setOhlcvData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searchedStock, setSearchedStock] = useState("");
  const [retrievedAt, setRetrievedAt] = useState("");

  async function fetchOHLCV(event) {
    event.preventDefault();

    const ticker = symbol.trim().toUpperCase();

    if (!ticker) {
      setError("Please enter a stock symbol.");
      return;
    }

    setLoading(true);
    setError("");
    setOhlcvData([]);

    try {
      const response = await API.get(`/market-data/${ticker}/ohlcv`, {
        params: { period, exchange },
      });

      setOhlcvData(response.data.ohlcv_data);
      setSearchedStock(response.data.ticker);
      setRetrievedAt(response.data.retrieved_at);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to fetch OHLCV data.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ohlcv-container">
      <h2>Stock OHLCV Data</h2>

      <p>
        View Open, High, Low, Close and Volume data for your selected stock.
      </p>

      <form onSubmit={fetchOHLCV} className="history-form">
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
          {loading ? "Loading..." : "Get OHLCV Data"}
        </button>
      </form>

      {error && <p className="stock-search-error">{error}</p>}

      {ohlcvData.length > 0 && (
        <div className="ohlcv-results">
          <h3>{searchedStock} - OHLCV Records</h3>

          <p>Total Records: {ohlcvData.length}</p>

          <div className="ohlcv-table-wrapper">
            <table className="ohlcv-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Open</th>
                  <th>High</th>
                  <th>Low</th>
                  <th>Close</th>
                  <th>Volume</th>
                </tr>
              </thead>

              <tbody>
                {ohlcvData.map((item) => (
                  <tr key={item.date}>
                    <td>{item.date}</td>
                    <td>{Number(item.open).toFixed(2)}</td>
                    <td>{Number(item.high).toFixed(2)}</td>
                    <td>{Number(item.low).toFixed(2)}</td>
                    <td>{Number(item.close).toFixed(2)}</td>
                    <td>{Number(item.volume).toLocaleString("en-IN")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p>
            <strong>Data Source:</strong> Yahoo Finance (via yfinance)
          </p>

          <p>
            <strong>Retrieved At:</strong>{" "}
            {retrievedAt
              ? new Date(retrievedAt).toLocaleString()
              : "Not available"}
          </p>
        </div>
      )}
    </div>
  );
}

export default StockOHLCV;
