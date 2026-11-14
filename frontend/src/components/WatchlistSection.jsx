import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import {
  Bookmark,
  Search,
  Plus,
  Trash2,
  TrendingUp,
  AlertCircle,
  ExternalLink,
  Loader2,
  RefreshCw,
} from "lucide-react";

export default function WatchlistSection({ onLaunchResearch, refreshTrigger }) {
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [actionError, setActionError] = useState("");
  const [addingTicker, setAddingTicker] = useState("");

  const loadWatchlist = async () => {
    try {
      setLoading(true);
      const data = await api.getWatchlist();
      setWatchlist(data || []);
      setActionError("");
    } catch (err) {
      setActionError(err.message || "Failed to load watchlist");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWatchlist();
  }, [refreshTrigger]);

  // Real-time stock search debounced
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsSearching(true);
        const data = await api.searchStocks(searchQuery, user?.preferences?.market);
        setSearchResults(data?.results || []);
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery, user?.preferences?.market]);

  const handleAddStock = async (stock) => {
    setActionError("");
    setAddingTicker(stock.ticker);
    try {
      await api.addToWatchlist({
        ticker: stock.ticker,
        company_name: stock.company_name,
        market: stock.market,
      });
      setSearchQuery("");
      setSearchResults([]);
      await loadWatchlist();
    } catch (err) {
      setActionError(err.message || "Failed to add to watchlist");
    } finally {
      setAddingTicker("");
    }
  };

  const handleCustomAdd = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    handleAddStock({
      ticker: searchQuery.trim().toUpperCase(),
      market: user?.preferences?.market || "NASDAQ",
    });
  };

  const handleRemove = async (stockId) => {
    try {
      await api.removeFromWatchlist(stockId);
      setWatchlist((prev) => prev.filter((s) => s.saved_stock_id !== stockId));
    } catch (err) {
      setActionError(err.message || "Failed to remove stock");
    }
  };

  return (
    <div className="card workspace-card">
      <div className="card-header">
        <div className="card-title-group">
          <Bookmark className="card-icon" size={20} />
          <div>
            <h2 className="card-title">Saved Stocks & Watchlist</h2>
            <p className="card-subtitle">
              Monitor key assets and trigger multi-agent analysis directly
            </p>
          </div>
        </div>
        <button
          className="btn-icon"
          onClick={loadWatchlist}
          title="Refresh Watchlist"
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? "spin" : ""} />
        </button>
      </div>

      <div className="card-body">
        {/* Stock Search Box */}
        <div className="search-wrapper">
          <form onSubmit={handleCustomAdd} className="search-form">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder={`Search ticker or company (e.g. AAPL, TSLA, NVDA, RELIANCE, TCS)...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            {searchQuery && (
              <button
                type="submit"
                className="btn btn-sm btn-primary add-search-btn"
                disabled={!!addingTicker}
              >
                <Plus size={14} /> Add
              </button>
            )}
          </form>

          {/* Autocomplete Dropdown */}
          {searchResults.length > 0 && (
            <div className="search-dropdown">
              <div className="dropdown-label">Matching Equities</div>
              {searchResults.map((stock) => (
                <div
                  key={stock.ticker}
                  className="dropdown-item"
                  onClick={() => handleAddStock(stock)}
                >
                  <div className="stock-info-col">
                    <span className="stock-ticker">{stock.ticker}</span>
                    <span className="stock-name">{stock.company_name}</span>
                  </div>
                  <div className="stock-meta-col">
                    <span className="market-badge">{stock.market}</span>
                    <button
                      className="btn btn-xs btn-outline"
                      disabled={addingTicker === stock.ticker}
                    >
                      {addingTicker === stock.ticker ? "Adding..." : "+ Add"}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {actionError && (
          <div className="alert alert-error my-3">
            <AlertCircle size={16} />
            <span>{actionError}</span>
          </div>
        )}

        {/* Watchlist Table */}
        <div className="table-responsive">
          {loading ? (
            <div className="loading-state">
              <Loader2 size={24} className="spin" />
              <span>Loading saved stocks...</span>
            </div>
          ) : watchlist.length === 0 ? (
            <div className="empty-state">
              <TrendingUp size={36} className="empty-icon" />
              <p className="empty-title">Your Watchlist is Empty</p>
              <p className="empty-desc">
                Search for any stock above (e.g. <b>AAPL</b>, <b>TSLA</b>, <b>NVDA</b>, <b>RELIANCE</b>) to save it here.
              </p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Company Name</th>
                  <th>Market</th>
                  <th>Saved Date</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {watchlist.map((stock) => (
                  <tr key={stock.saved_stock_id}>
                    <td>
                      <span className="ticker-pill">{stock.ticker}</span>
                    </td>
                    <td className="font-medium">{stock.company_name}</td>
                    <td>
                      <span className="market-tag">{stock.market}</span>
                    </td>
                    <td className="text-muted">
                      {new Date(stock.created_at).toLocaleDateString(undefined, {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </td>
                    <td className="text-right action-cell">
                      <button
                        className="btn btn-xs btn-primary launch-research-btn"
                        onClick={() =>
                          onLaunchResearch({
                            ticker: stock.ticker,
                            company_name: stock.company_name,
                            market: stock.market,
                          })
                        }
                        title="Start Multi-Agent Research Task"
                      >
                        <TrendingUp size={12} /> Research
                      </button>
                      <button
                        className="btn-icon btn-danger-icon"
                        onClick={() => handleRemove(stock.saved_stock_id)}
                        title="Remove from Watchlist"
                      >
                        <Trash2 size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
