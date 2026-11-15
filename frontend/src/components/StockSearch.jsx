import { useEffect, useState } from "react";
import API from "../services/api";

function StockSearch() {
  const [symbol, setSymbol] = useState("");
  const [stock, setStock] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingStock, setLoadingStock] = useState(false);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [selectedMarket, setSelectedMarket] = useState("");
  const [researchPeriod, setResearchPeriod] = useState("1y");
  const [startingResearch, setStartingResearch] = useState(false);
  const [researchMessage, setResearchMessage] = useState("");

  useEffect(() => {
    async function fetchPreferences() {
      try {
        const response = await API.get("/preferences/");
        setSelectedMarket(response.data.market);
        setResearchPeriod(response.data.analysis_period);
      } catch (error) {
        console.error(
          "Failed to load stock research preferences:",
          error.response?.data,
        );
      }
    }

    function handlePreferencesUpdate(event) {
      setSelectedMarket(event.detail.market);
      setResearchPeriod(event.detail.analysis_period);
    }

    fetchPreferences();

    window.addEventListener("preferencesUpdated", handlePreferencesUpdate);

    return () => {
      window.removeEventListener("preferencesUpdated", handlePreferencesUpdate);
    };
  }, []);

  async function searchStock(event) {
    event.preventDefault();

    const query = symbol.trim();

    if (!query) {
      setError("Please enter a company name or ticker symbol.");
      return;
    }

    setLoading(true);
    setError("");
    setStock(null);
    setSearchResults([]);
    setSuccessMessage("");

    try {
      const response = await API.get("/market-data/search/company", {
        params: { q: query },
      });

      setSearchResults(response.data.results);

      if (response.data.results.length === 0) {
        setError("No matching companies found.");
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to search for companies. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function selectCompany(ticker, exchange) {
    setLoadingStock(true);
    setError("");
    setStock(null);
    setSuccessMessage("");
    setSelectedMarket(exchange || "Unknown");
    setResearchMessage("");

    try {
      const response = await API.get(`/market-data/${ticker}`, {
        params: { exchange },
      });
      setStock(response.data);
      setSearchResults([]);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to fetch stock data.");
    } finally {
      setLoadingStock(false);
    }
  }

  async function addToWatchlist() {
    if (!stock) return;

    setAdding(true);
    setSuccessMessage("");

    try {
      await API.post("/watchlist/", {
        ticker: stock.ticker,
        market: selectedMarket,
      });

      window.dispatchEvent(new Event("watchlistUpdated"));

      setSuccessMessage(`${stock.ticker} added to your watchlist!`);
    } catch (error) {
      console.log("Watchlist error:", error.response?.data);
      console.log("HTTP status:", error.response?.status);

      if (error.response?.status === 409) {
        setSuccessMessage("This stock is already in your watchlist.");
      } else {
        setSuccessMessage(
          error.response?.data?.detail || "Unable to add stock.",
        );
      }
    } finally {
      setAdding(false);
    }
  }

  async function startResearch() {
    if (!stock) return;

    setStartingResearch(true);
    setResearchMessage("");

    try {
      await API.post("/research/tasks", {
        company_name: stock.company_name,
        ticker: stock.ticker,
        market: selectedMarket,
        analysis_period: researchPeriod,
      });

      setResearchMessage(
        `Research task created successfully for ${stock.ticker}!`,
      );

      window.dispatchEvent(new Event("researchHistoryUpdated"));
    } catch (error) {
      console.error("Research creation error:", error.response?.data);

      setResearchMessage(
        error.response?.data?.detail || "Unable to start research.",
      );
    } finally {
      setStartingResearch(false);
    }
  }

  const currency = ["NMS", "NASDAQ"].includes(selectedMarket) ? "$" : "₹";

  return (
    <div className="stock-search-container">
      <h2>Search Stocks</h2>

      <form onSubmit={searchStock} className="stock-search-form">
        <input
          type="text"
          placeholder="Enter company name or ticker (e.g. TCS)"
          value={symbol}
          onChange={(event) => setSymbol(event.target.value)}
        />

        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {error && <p className="stock-search-error">{error}</p>}

      {searchResults.length > 0 && (
        <div className="stock-search-result">
          <h3>Matching Companies</h3>

          {searchResults.map((company) => (
            <div
              className="company-search-item"
              key={`${company.ticker}-${company.exchange}`}
            >
              <div>
                <h4>{company.company_name}</h4>
                <p>
                  {company.ticker} ({company.exchange})
                </p>
              </div>

              <button
                type="button"
                onClick={() => selectCompany(company.ticker, company.exchange)}
                disabled={loadingStock}
              >
                Select
              </button>
            </div>
          ))}
        </div>
      )}

      {loadingStock && <p>Loading stock details...</p>}

      {stock && (
        <div className="stock-search-result">
          <h3>{stock.company_name}</h3>
          <p>Symbol: {stock.ticker}</p>
          <p>Exchange: {selectedMarket}</p>
          <p>
            Current Price: {currency}
            {stock.current_price}
          </p>
          <p>
            Previous Close: {currency}
            {stock.previous_close}
          </p>

          <p
            className={
              stock.percentage_change >= 0 ? "stock-positive" : "stock-negative"
            }
          >
            {stock.percentage_change >= 0 ? "▲" : "▼"}{" "}
            {Math.abs(stock.percentage_change)}% Today
          </p>

          <button
            className="add-watchlist-button"
            onClick={addToWatchlist}
            disabled={adding}
          >
            {adding ? "Adding..." : "Add to Watchlist"}
          </button>

          <div className="research-controls">
            <label htmlFor="research-period">Research Period:</label>

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

            <button
              type="button"
              className="start-research-button"
              onClick={startResearch}
              disabled={startingResearch}
            >
              {startingResearch ? "Starting..." : "Start Research"}
            </button>

            {researchMessage && (
              <p className="research-message">{researchMessage}</p>
            )}
          </div>
          {successMessage && (
            <p className="watchlist-success-message">{successMessage}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default StockSearch;
