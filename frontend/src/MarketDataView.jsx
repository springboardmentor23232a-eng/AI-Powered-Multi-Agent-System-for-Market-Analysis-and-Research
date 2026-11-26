import { useState, useEffect, useMemo } from "react";
import { api } from "./api";

const QUICK_STOCKS = [
  { ticker: "TCS.NS", name: "Tata Consultancy Services", market: "NSE" },
  { ticker: "RELIANCE.NS", name: "Reliance Industries", market: "NSE" },
  { ticker: "INFY.NS", name: "Infosys Limited", market: "NSE" },
  { ticker: "AAPL", name: "Apple Inc.", market: "NASDAQ" },
  { ticker: "MSFT", name: "Microsoft Corporation", market: "NASDAQ" },
  { ticker: "NVDA", name: "NVIDIA Corporation", market: "NASDAQ" },
];

export function MarketDataView({
  onAddToWatchlist,
  onStartResearch,
  initialTicker = "AAPL",
  initialMarket = "NASDAQ",
  onError,
  onNotice,
}) {
  const [query, setQuery] = useState("");
  const [searchMarket, setSearchMarket] = useState("ALL");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const [selectedTicker, setSelectedTicker] = useState(initialTicker);
  const [selectedMarket, setSelectedMarket] = useState(initialMarket);
  const [companyName, setCompanyName] = useState("");

  const [period, setPeriod] = useState("1y");
  const [interval, setInterval] = useState("1d");

  const [activeTab, setActiveTab] = useState("ohlcv"); // 'ohlcv', 'profile', 'financials', 'records'
  const [finStatementType, setFinStatementType] = useState("income"); // 'income', 'balance', 'cashflow', 'ratios'

  const [loadingData, setLoadingData] = useState(false);
  const [recording, setRecording] = useState(false);
  const [stockError, setStockError] = useState("");

  const [ohlcvData, setOhlcvData] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [financialsData, setFinancialsData] = useState(null);

  const [records, setRecords] = useState([]);
  const [apiConfig, setApiConfig] = useState(null);

  // Load API config and initial stock data
  useEffect(() => {
    api.getMarketApiConfig().then(setApiConfig).catch(() => {});
    loadSavedRecords();
    loadStockData(selectedTicker, selectedMarket);
  }, []);

  async function loadSavedRecords() {
    try {
      const list = await api.getRecordedMarketData();
      setRecords(list);
    } catch (err) {
      // non-critical
    }
  }

  async function loadStockData(ticker, market, targetPeriod = period, targetInterval = interval) {
    if (!ticker) return;
    setLoadingData(true);
    setStockError("");
    try {
      const [hist, prof, fin] = await Promise.all([
        api.getHistoricalData(ticker, market, targetPeriod, targetInterval),
        api.getCompanyProfile(ticker, market).catch(() => null),
        api.getFinancialStatements(ticker, market).catch(() => null),
      ]);

      setOhlcvData(hist);
      setProfileData(prof);
      setFinancialsData(fin);
      setSelectedTicker(hist.ticker || ticker);
      setSelectedMarket(hist.market || market);
      setCompanyName(hist.company_name || prof?.company_name || ticker);
    } catch (err) {
      const msg = err.message || "Failed to load market data for stock.";
      setStockError(msg);
      setOhlcvData(null);
      setProfileData(null);
      setFinancialsData(null);
      onError?.(msg);
    } finally {
      setLoadingData(false);
    }
  }

  async function handleSearch(e) {
    e?.preventDefault();
    if (!query.trim()) return;
    setSearching(true);
    try {
      const results = await api.searchMarket(query.trim(), searchMarket);
      setSearchResults(results);
      if (results.length === 0) {
        onNotice?.("No matching stocks found for this search.");
      }
    } catch (err) {
      onError?.(err.message || "Search failed.");
    } finally {
      setSearching(false);
    }
  }

  function handleSelectStock(stock) {
    setSelectedTicker(stock.ticker);
    setSelectedMarket(stock.market || "NSE");
    setCompanyName(stock.company_name);
    setSearchResults([]);
    loadStockData(stock.ticker, stock.market || "NSE");
  }

  async function handlePeriodChange(newPeriod) {
    setPeriod(newPeriod);
    loadStockData(selectedTicker, selectedMarket, newPeriod, interval);
  }

  async function handleIntervalChange(newInterval) {
    setInterval(newInterval);
    loadStockData(selectedTicker, selectedMarket, period, newInterval);
  }

  async function handleRecordCollection() {
    setRecording(true);
    try {
      const saved = await api.collectMarketData({
        ticker: selectedTicker,
        company_name: companyName || selectedTicker,
        market: selectedMarket,
        period: period,
        interval: interval,
      });
      onNotice?.(`Market data snapshot for ${saved.ticker} recorded to database successfully!`);
      loadSavedRecords();
    } catch (err) {
      onError?.(err.message || "Failed to record market data.");
    } finally {
      setRecording(false);
    }
  }

  function handleExportCsv() {
    if (!ohlcvData || !ohlcvData.ohlcv?.length) return;
    const headers = ["Date", "Timestamp", "Open", "High", "Low", "Close", "Adj Close", "Volume"];
    const rows = ohlcvData.ohlcv.map((b) => [
      b.date,
      b.timestamp,
      b.open,
      b.high,
      b.low,
      b.close,
      b.adj_close,
      b.volume,
    ]);

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${selectedTicker}_OHLCV_${period}_${interval}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    onNotice?.(`Exported ${ohlcvData.ohlcv.length} OHLCV bars to CSV.`);
  }

  function handleLoadSavedRecord(rec) {
    api.getRecordedMarketDataDetail(rec.record_id)
      .then((detail) => {
        setSelectedTicker(detail.ticker);
        setSelectedMarket(detail.market);
        setCompanyName(detail.company_name);
        setPeriod(detail.period);
        setInterval(detail.interval);
        setOhlcvData({
          ticker: detail.ticker,
          company_name: detail.company_name,
          market: detail.market,
          period: detail.period,
          interval: detail.interval,
          currency: detail.currency || "USD",
          current_price: detail.latest_price,
          change: detail.change,
          change_percent: detail.change_percent,
          ohlcv: detail.ohlcv_data || [],
          data_source: detail.data_source,
          retrieval_timestamp: detail.retrieval_timestamp,
        });
        setProfileData(detail.profile_data || null);
        setFinancialsData(detail.financials_data || null);
        setActiveTab("ohlcv");
        onNotice?.(`Loaded saved snapshot for ${detail.ticker} (${new Date(detail.retrieval_timestamp).toLocaleString()})`);
      })
      .catch((err) => onError?.(err.message));
  }

  async function handleDeleteRecord(recordId, e) {
    e.stopPropagation();
    try {
      await api.deleteRecordedMarketData(recordId);
      setRecords((prev) => prev.filter((r) => r.record_id !== recordId));
      onNotice?.("Market data snapshot removed.");
    } catch (err) {
      onError?.(err.message);
    }
  }

  return (
    <section className="content">
      {/* Intro Header */}
      <div className="intro-block">
        <span className="kicker">REAL-TIME & HISTORICAL INTELLIGENCE</span>
        <h2>Stock Search & Market Data Collection</h2>
        <p className="muted">
          Search companies across Indian & US exchanges, retrieve OHLCV historical prices,
          examine company profiles and financial statements, and persist audit-tracked records.
        </p>
      </div>

      {/* API Configuration & Status Banner */}
      {apiConfig && (
        <div className="api-status-banner">
          <div>
            <strong>Market Data Provider: </strong>
            <span>{apiConfig.provider || "Yahoo Finance (via yfinance)"}</span>
            <span className="status-pill" style={{ marginLeft: 8, background: "#184236", color: "#92e5c8" }}>
              ✓ Direct yfinance Library Active (No API Key Required)
            </span>
          </div>
          <small className="muted">Direct Yahoo Finance integration • Live, verified provider responses</small>
        </div>
      )}

      {/* Search Bar */}
      <form className="search-panel" onSubmit={handleSearch}>
        <div className="search-input-wrap">
          <span>⌕</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by company name or ticker symbol (e.g. TCS, Apple, AAPL, Reliance)"
          />
        </div>
        <select value={searchMarket} onChange={(e) => setSearchMarket(e.target.value)}>
          <option value="ALL">All Markets</option>
          <option value="NSE">NSE (India)</option>
          <option value="BSE">BSE (India)</option>
          <option value="NASDAQ">NASDAQ (US)</option>
          <option value="NYSE">NYSE (US)</option>
        </select>
        <button className="btn primary" disabled={searching}>
          {searching ? "Searching…" : "Search Stock"}
        </button>
      </form>

      {/* Quick Picks */}
      <div className="quick-chips">
        <span className="chip-label">Quick Select:</span>
        {QUICK_STOCKS.map((stk) => (
          <button
            key={stk.ticker}
            className="quick-chip"
            onClick={() => handleSelectStock(stk)}
          >
            {stk.name} ({stk.ticker})
          </button>
        ))}
      </div>

      {/* Search Results Dropdown / Panel */}
      {searchResults.length > 0 && (
        <div className="results-panel">
          <div className="section-heading">
            <h3>Search Matches ({searchResults.length})</h3>
            <span className="muted">Click to view comprehensive market data</span>
          </div>
          {searchResults.map((stk) => (
            <div className="result-row" key={`${stk.ticker}-${stk.market}`}>
              <div>
                <strong>{stk.company_name}</strong>
                <span>
                  {stk.ticker} · {stk.exchange} · {stk.market} ({stk.currency})
                </span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="btn outline compact"
                  onClick={() => handleSelectStock(stk)}
                >
                  View Market Data →
                </button>
                {onAddToWatchlist && (
                  <button
                    className="btn outline compact"
                    onClick={() => onAddToWatchlist(stk)}
                  >
                    ＋ Watchlist
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Selected Stock Overview Header & Audit Stamp */}
      <div className="market-header-card" style={{ marginTop: 24 }}>
        <div className="welcome-row" style={{ marginBottom: 0 }}>
          <div>
            <span className="kicker">{selectedMarket} EQUITY</span>
            <h2 style={{ margin: "4px 0" }}>
              {companyName || selectedTicker} <span style={{ color: "var(--mint)" }}>({selectedTicker})</span>
            </h2>
            <p className="muted">
              {profileData?.sector ? `${profileData.sector} · ${profileData.industry}` : "Market Asset"}
            </p>
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            <button
              className="btn primary compact"
              onClick={handleRecordCollection}
              disabled={recording || loadingData}
            >
              {recording ? "Recording…" : "💾 Record to Database"}
            </button>
            <button
              className="btn outline compact"
              onClick={handleExportCsv}
              disabled={!ohlcvData?.ohlcv?.length}
            >
              📥 Export OHLCV (CSV)
            </button>
            {onStartResearch && (
              <button
                className="btn outline compact"
                onClick={() =>
                  onStartResearch({
                    ticker: selectedTicker,
                    company_name: companyName || selectedTicker,
                    market: selectedMarket,
                  })
                }
              >
                🔬 New Research Task
              </button>
            )}
          </div>
        </div>

        {/* Data Source & Retrieval Timestamp Audit Trail */}
        <div className="market-meta-bar">
          <div className="meta-badges">
            <span className="meta-badge source">
              🏷️ Data Source: {ohlcvData?.data_source || "Yahoo Finance via yfinance"}
            </span>
            <span className="meta-badge time">
              ⏱️ Retrieved: {ohlcvData?.retrieval_timestamp ? new Date(ohlcvData.retrieval_timestamp).toUTCString() : "Live"}
            </span>
            <span className="meta-badge" style={{ background: "#1c2b3d", color: "#92cbf5" }}>
              📡 Quote: {ohlcvData?.price_status || "Latest Available Market Price"}
            </span>
            <span className="meta-badge">
              Currency: {ohlcvData?.currency || "USD"}
            </span>
            <span className="meta-badge">
              Bars: {ohlcvData?.ohlcv?.length || 0}
            </span>
          </div>
          <span className="muted" style={{ fontSize: 10 }}>
            Strictly live data via official Yahoo Finance provider
          </span>
        </div>
      </div>

      {/* Sub-Tabs: OHLCV, Profile, Financials, Saved Records */}
      <div className="market-subtabs">
        <button
          className={`subtab-btn ${activeTab === "ohlcv" ? "active" : ""}`}
          onClick={() => setActiveTab("ohlcv")}
        >
          📈 Historical Prices & OHLCV
        </button>
        <button
          className={`subtab-btn ${activeTab === "profile" ? "active" : ""}`}
          onClick={() => setActiveTab("profile")}
        >
          🏢 Company Profile & Executives
        </button>
        <button
          className={`subtab-btn ${activeTab === "financials" ? "active" : ""}`}
          onClick={() => setActiveTab("financials")}
        >
          📑 Financial Statements & Ratios
        </button>
        <button
          className={`subtab-btn ${activeTab === "records" ? "active" : ""}`}
          onClick={() => {
            setActiveTab("records");
            loadSavedRecords();
          }}
        >
          🗂️ Recorded Collections ({records.length})
        </button>
      </div>

      {loadingData && (
        <div className="loading-screen" style={{ minHeight: 200 }}>
          <span className="spinner" /> Loading market data from Yahoo Finance via yfinance…
        </div>
      )}

      {/* Error / Unavailable Data State */}
      {!loadingData && stockError && (
        <div className="empty-state" style={{ marginTop: 24, padding: 36, border: "1px solid #4a2828" }}>
          <div className="empty-symbol">⚠️</div>
          <strong>Market Data Unavailable for {selectedTicker}</strong>
          <p className="muted" style={{ maxWidth: 460, margin: "8px auto" }}>
            {stockError}
          </p>
          <div style={{ display: "flex", gap: 10, justifyContent: "center", marginTop: 12 }}>
            <button
              className="btn primary compact"
              onClick={() => loadStockData(selectedTicker, selectedMarket)}
            >
              ↻ Try Again
            </button>
            <button
              className="btn outline compact"
              onClick={() => handleSelectStock({ ticker: "AAPL", market: "NASDAQ", company_name: "Apple Inc." })}
            >
              Load Sample Stock (AAPL)
            </button>
          </div>
        </div>
      )}

      {/* TAB 1: OHLCV & Historical Prices */}
      {!loadingData && !stockError && activeTab === "ohlcv" && ohlcvData && (
        <div>
          {/* Key Price Metric Cards */}
          <div className="price-overview-grid">
            <div className="price-card">
              <span>Current Price</span>
              <strong>
                {ohlcvData.currency === "INR" ? "₹" : "$"}
                {ohlcvData.current_price?.toLocaleString() || "—"}
              </strong>
              <small className={ohlcvData.change >= 0 ? "up" : "down"}>
                {ohlcvData.change >= 0 ? "▲ +" : "▼ "}
                {ohlcvData.change} ({ohlcvData.change_percent}%)
              </small>
              {ohlcvData.price_status && (
                <span style={{ fontSize: 9, color: "#8ea3b8", display: "block", marginTop: 4 }}>
                  Quote: {ohlcvData.price_status}
                </span>
              )}
            </div>

            <div className="price-card">
              <span>Previous Close</span>
              <strong>
                {ohlcvData.currency === "INR" ? "₹" : "$"}
                {ohlcvData.previous_close?.toLocaleString() || "—"}
              </strong>
              <small className="muted">Prior session</small>
            </div>

            <div className="price-card">
              <span>Day's Range</span>
              <strong style={{ fontSize: 18 }}>
                {ohlcvData.day_low ? `${ohlcvData.day_low} - ${ohlcvData.day_high}` : "—"}
              </strong>
              <small className="muted">Low — High</small>
            </div>

            <div className="price-card">
              <span>52-Week Range</span>
              <strong style={{ fontSize: 18 }}>
                {ohlcvData.fifty_two_week_low ? `${ohlcvData.fifty_two_week_low} - ${ohlcvData.fifty_two_week_high}` : "—"}
              </strong>
              <small className="muted">Annual range</small>
            </div>

            <div className="price-card">
              <span>Trading Volume</span>
              <strong>
                {ohlcvData.volume ? ohlcvData.volume.toLocaleString() : "—"}
              </strong>
              <small className="muted">
                Avg: {ohlcvData.average_volume?.toLocaleString() || "—"}
              </small>
            </div>
          </div>

          {/* Interactive Chart Container */}
          <div className="chart-panel">
            <div className="chart-controls">
              <div>
                <strong style={{ fontSize: 13, marginRight: 10 }}>Period:</strong>
                <div className="period-pill-group" style={{ display: "inline-flex" }}>
                  {["1mo", "3mo", "6mo", "1y", "5y", "max"].map((p) => (
                    <button
                      key={p}
                      className={`pill-btn ${period === p ? "active" : ""}`}
                      onClick={() => handlePeriodChange(p)}
                    >
                      {p.toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <strong style={{ fontSize: 13, marginRight: 10 }}>Interval:</strong>
                <div className="interval-pill-group" style={{ display: "inline-flex", flexWrap: "wrap", gap: 4 }}>
                  {[
                    { label: "1D", val: "1d" },
                    { label: "1W", val: "1wk" },
                    { label: "1M", val: "1mo" },
                    { label: "15m", val: "15m" },
                    { label: "5m", val: "5m" },
                    { label: "1m", val: "1m" },
                  ].map((inv) => (
                    <button
                      key={inv.val}
                      className={`pill-btn ${interval === inv.val ? "active" : ""}`}
                      onClick={() => handleIntervalChange(inv.val)}
                    >
                      {inv.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* SVG Visual Chart */}
            <InteractiveStockChart
              data={ohlcvData.ohlcv || []}
              currency={ohlcvData.currency === "INR" ? "₹" : "$"}
            />
          </div>

          {/* OHLCV Data Table */}
          <div className="section-heading">
            <div>
              <span className="kicker">COLLECTED OHLCV BARS</span>
              <h3>Open, High, Low, Close & Volume Table ({ohlcvData.ohlcv?.length || 0})</h3>
            </div>
            <button className="text-button" onClick={handleExportCsv}>
              Export to CSV →
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Open</th>
                  <th>High</th>
                  <th>Low</th>
                  <th>Close</th>
                  <th>Adj Close</th>
                  <th>Volume</th>
                </tr>
              </thead>
              <tbody>
                {ohlcvData.ohlcv?.slice(-50).reverse().map((b) => (
                  <tr key={b.timestamp}>
                    <td><strong>{b.date}</strong></td>
                    <td>{b.open}</td>
                    <td style={{ color: "#62d8aa" }}>{b.high}</td>
                    <td style={{ color: "#f1798b" }}>{b.low}</td>
                    <td><strong>{b.close}</strong></td>
                    <td>{b.adj_close}</td>
                    <td>{b.volume?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {ohlcvData.ohlcv?.length > 50 && (
            <p className="muted" style={{ textAlign: "right", marginTop: 8 }}>
              Showing latest 50 bars. Full dataset of {ohlcvData.ohlcv.length} bars available in CSV export.
            </p>
          )}
        </div>
      )}

      {/* TAB 2: Company Profile */}
      {!loadingData && activeTab === "profile" && !profileData && (
        <div className="empty-state" style={{ marginTop: 24, padding: 36 }}>
          <div className="empty-symbol">🏢</div>
          <strong>Company Profile Unavailable</strong>
          <p className="muted">No company profile or executive leadership data available for {selectedTicker}.</p>
        </div>
      )}

      {!loadingData && activeTab === "profile" && profileData && (
        <div>
          <div className="profile-grid">
            <div className="profile-card">
              <div>
                <span className="kicker">BUSINESS SUMMARY</span>
                <h3 style={{ margin: "6px 0 12px" }}>About {profileData.company_name}</h3>
                <p className="muted" style={{ lineHeight: 1.8 }}>
                  {profileData.summary}
                </p>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                <div>
                  <span className="kicker">HEADQUARTERS</span>
                  <p style={{ margin: "4px 0" }}>{profileData.city}, {profileData.country}</p>
                  <small className="muted">{profileData.address}</small>
                </div>
                <div>
                  <span className="kicker">WEBSITE & CONTACT</span>
                  <p style={{ margin: "4px 0" }}>
                    <a
                      href={profileData.website}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: "var(--mint)" }}
                    >
                      {profileData.website}
                    </a>
                  </p>
                  <small className="muted">Employees: {profileData.full_time_employees?.toLocaleString() || "N/A"}</small>
                </div>
              </div>
            </div>

            <div className="profile-card">
              <span className="kicker">VALUATION & KEY STATISTICS</span>
              <div className="profile-metrics-list">
                <div className="profile-metric-box">
                  <span>Market Cap</span>
                  <strong>{profileData.market_cap || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>Enterprise Val</span>
                  <strong>{profileData.enterprise_value || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>Trailing P/E</span>
                  <strong>{profileData.trailing_pe || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>Forward P/E</span>
                  <strong>{profileData.forward_pe || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>PEG Ratio</span>
                  <strong>{profileData.peg_ratio || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>Price / Book</span>
                  <strong>{profileData.price_to_book || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>Beta (5Y)</span>
                  <strong>{profileData.beta || "—"}</strong>
                </div>
                <div className="profile-metric-box">
                  <span>Dividend Yield</span>
                  <strong>
                    {profileData.dividend_yield
                      ? `${(profileData.dividend_yield * 100).toFixed(2)}%`
                      : "—"}
                  </strong>
                </div>
              </div>
            </div>
          </div>

          {/* Officers Table */}
          <div className="profile-card">
            <span className="kicker">EXECUTIVE LEADERSHIP</span>
            <h3>Company Officers & Management</h3>
            <div className="table-wrap">
              <table className="officers-table">
                <thead>
                  <tr>
                    <th>Executive Name</th>
                    <th>Title</th>
                    <th>Age</th>
                    <th>Total Pay</th>
                  </tr>
                </thead>
                <tbody>
                  {profileData.officers?.length ? (
                    profileData.officers.map((off, idx) => (
                      <tr key={idx}>
                        <td><strong>{off.name}</strong></td>
                        <td>{off.title}</td>
                        <td>{off.age || "—"}</td>
                        <td>{off.total_pay || "—"}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" className="muted">Officer data not available.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Financial Statements */}
      {!loadingData && activeTab === "financials" && !financialsData && (
        <div className="empty-state" style={{ marginTop: 24, padding: 36 }}>
          <div className="empty-symbol">📑</div>
          <strong>Financial Statements Unavailable</strong>
          <p className="muted">No statutory financial statements or SEC reports available for {selectedTicker}.</p>
        </div>
      )}

      {!loadingData && activeTab === "financials" && financialsData && (
        <div>
          <div className="financials-tab-nav">
            {[
              { id: "income", label: "Income Statement" },
              { id: "balance", label: "Balance Sheet" },
              { id: "cashflow", label: "Cash Flow" },
              { id: "ratios", label: "Key Financial Ratios" },
            ].map((st) => (
              <button
                key={st.id}
                className={`pill-btn ${finStatementType === st.id ? "active" : ""}`}
                onClick={() => setFinStatementType(st.id)}
              >
                {st.label}
              </button>
            ))}
          </div>

          {finStatementType === "income" && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Period Ending</th>
                    <th>Total Revenue</th>
                    <th>Cost of Revenue</th>
                    <th>Gross Profit</th>
                    <th>Operating Expenses</th>
                    <th>Operating Income</th>
                    <th>Net Income</th>
                    <th>EBITDA</th>
                    <th>Diluted EPS</th>
                  </tr>
                </thead>
                <tbody>
                  {financialsData.income_statement?.map((inc, i) => (
                    <tr key={i}>
                      <td><strong>{inc.period}</strong></td>
                      <td>{inc.total_revenue}</td>
                      <td>{inc.cost_of_revenue}</td>
                      <td style={{ color: "var(--mint)" }}>{inc.gross_profit}</td>
                      <td>{inc.operating_expenses}</td>
                      <td>{inc.operating_income}</td>
                      <td><strong>{inc.net_income}</strong></td>
                      <td>{inc.ebitda}</td>
                      <td>{inc.diluted_eps}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {finStatementType === "balance" && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Period Ending</th>
                    <th>Cash & Equivalents</th>
                    <th>Short-Term Inv.</th>
                    <th>Total Current Assets</th>
                    <th>Net PPE</th>
                    <th>Total Assets</th>
                    <th>Current Liabilities</th>
                    <th>Long-Term Debt</th>
                    <th>Total Liabilities</th>
                    <th>Total Equity</th>
                  </tr>
                </thead>
                <tbody>
                  {financialsData.balance_sheet?.map((bal, i) => (
                    <tr key={i}>
                      <td><strong>{bal.period}</strong></td>
                      <td>{bal.cash_and_equivalents}</td>
                      <td>{bal.short_term_investments}</td>
                      <td>{bal.total_current_assets}</td>
                      <td>{bal.net_ppe}</td>
                      <td><strong>{bal.total_assets}</strong></td>
                      <td>{bal.total_current_liabilities}</td>
                      <td>{bal.long_term_debt}</td>
                      <td>{bal.total_liabilities}</td>
                      <td style={{ color: "var(--mint)" }}>{bal.stockholders_equity}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {finStatementType === "cashflow" && (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Period Ending</th>
                    <th>Operating Cash Flow</th>
                    <th>Capital Expenditures</th>
                    <th>Free Cash Flow</th>
                    <th>Investing Cash Flow</th>
                    <th>Financing Cash Flow</th>
                    <th>Net Change in Cash</th>
                  </tr>
                </thead>
                <tbody>
                  {financialsData.cash_flow?.map((cf, i) => (
                    <tr key={i}>
                      <td><strong>{cf.period}</strong></td>
                      <td style={{ color: "#62d8aa" }}>{cf.operating_cash_flow}</td>
                      <td>{cf.capital_expenditures}</td>
                      <td style={{ color: "var(--mint)" }}><strong>{cf.free_cash_flow}</strong></td>
                      <td>{cf.investing_cash_flow}</td>
                      <td>{cf.financing_cash_flow}</td>
                      <td>{cf.net_change_in_cash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {finStatementType === "ratios" && financialsData.key_ratios && (
            <div className="ratios-grid">
              {Object.entries(financialsData.key_ratios).map(([k, val]) => (
                <div className="ratio-card" key={k}>
                  <span>{k.replace(/_/g, " ")}</span>
                  <strong>{val}</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: Recorded Collections History */}
      {!loadingData && activeTab === "records" && (
        <div>
          <div className="section-heading">
            <div>
              <span className="kicker">PERSISTED DATASETS</span>
              <h3>Recorded Market Snapshots ({records.length})</h3>
            </div>
            <button className="text-button" onClick={loadSavedRecords}>
              Refresh Records ↻
            </button>
          </div>

          {records.length ? (
            <div className="collection-history-grid">
              {records.map((rec) => (
                <article
                  className="collection-card"
                  key={rec.record_id}
                  onClick={() => handleLoadSavedRecord(rec)}
                  style={{ cursor: "pointer" }}
                >
                  <div className="collection-card-top">
                    <div>
                      <strong>{rec.company_name}</strong>
                      <span className="table-sub">{rec.ticker} · {rec.market}</span>
                    </div>
                    <button
                      className="icon-button"
                      title="Delete record"
                      onClick={(e) => handleDeleteRecord(rec.record_id, e)}
                    >
                      ×
                    </button>
                  </div>

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <span style={{ font: "750 20px Manrope" }}>
                      {rec.currency === "INR" ? "₹" : "$"}{rec.latest_price || "—"}
                    </span>
                    <span className="meta-badge" style={{ fontSize: 9 }}>
                      {rec.ohlcv_count} bars ({rec.period})
                    </span>
                  </div>

                  <div className="collection-card-bottom">
                    <span>{rec.data_source}</span>
                    <span>{new Date(rec.retrieval_timestamp).toLocaleDateString()}</span>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-symbol">💾</div>
              <strong>No saved market snapshots yet</strong>
              <p>Click "Record to Database" above to preserve market datasets with timestamps and source attribution.</p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

// ----------------------------------------------------
// Interactive Stock Chart (Pure SVG + Volume Histogram)
// ----------------------------------------------------
function InteractiveStockChart({ data, currency = "$" }) {
  const [hoverIndex, setHoverIndex] = useState(null);

  if (!data || data.length < 2) {
    return (
      <div style={{ padding: 40, textAlign: "center", color: "var(--muted)" }}>
        Insufficient historical data bars to render chart.
      </div>
    );
  }

  const width = 800;
  const height = 260;
  const priceHeight = 190;
  const volumeHeight = 50;

  const closes = data.map((d) => d.close);
  const volumes = data.map((d) => d.volume);

  const minPrice = Math.min(...closes) * 0.98;
  const maxPrice = Math.max(...closes) * 1.02;
  const priceRange = maxPrice - minPrice || 1;

  const maxVolume = Math.max(...volumes) || 1;

  const points = data.map((d, i) => {
    const x = (i / (data.length - 1)) * (width - 40) + 20;
    const y = priceHeight - ((d.close - minPrice) / priceRange) * (priceHeight - 30) - 10;
    return { x, y, data: d };
  });

  const pathD = points.reduce((acc, p, i) => `${acc} ${i === 0 ? "M" : "L"} ${p.x} ${p.y}`, "");
  const areaD = `${pathD} L ${points[points.length - 1].x} ${priceHeight} L ${points[0].x} ${priceHeight} Z`;

  const hoveredPoint = hoverIndex !== null ? points[hoverIndex] : points[points.length - 1];

  function handleMouseMove(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, mouseX / rect.width));
    const idx = Math.round(ratio * (data.length - 1));
    setHoverIndex(idx);
  }

  return (
    <div
      className="svg-chart-container"
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setHoverIndex(null)}
    >
      <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
        <defs>
          <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#8ee0c2" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#8ee0c2" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Volume Bars */}
        {data.map((d, i) => {
          const x = (i / (data.length - 1)) * (width - 40) + 18;
          const barH = (d.volume / maxVolume) * volumeHeight;
          const y = height - barH;
          const barW = Math.max(2, (width / data.length) * 0.65);
          const isUp = d.close >= d.open;
          return (
            <rect
              key={i}
              x={x}
              y={y}
              width={barW}
              height={barH}
              fill={isUp ? "rgba(98, 216, 170, 0.35)" : "rgba(241, 121, 139, 0.35)"}
            />
          );
        })}

        {/* Price Area Fill */}
        <path d={areaD} fill="url(#chartGradient)" />

        {/* Price Trend Line */}
        <path
          d={pathD}
          fill="none"
          stroke="#8ee0c2"
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Hover Crosshair & Point */}
        {hoveredPoint && (
          <g>
            <line
              x1={hoveredPoint.x}
              y1={10}
              x2={hoveredPoint.x}
              y2={height}
              stroke="#2e4863"
              strokeDasharray="3 3"
            />
            <circle
              cx={hoveredPoint.x}
              cy={hoveredPoint.y}
              r="5"
              fill="#8ee0c2"
              stroke="#0b1220"
              strokeWidth="2.5"
            />
          </g>
        )}
      </svg>

      {/* Tooltip Overlay */}
      {hoveredPoint && (
        <div className="chart-hover-box">
          <div>
            <span>Date:</span>
            <strong>{hoveredPoint.data.date}</strong>
          </div>
          <div>
            <span>Close:</span>
            <strong style={{ color: "var(--mint)" }}>
              {currency}{hoveredPoint.data.close}
            </strong>
          </div>
          <div>
            <span>Open / High / Low:</span>
            <span>
              {hoveredPoint.data.open} / {hoveredPoint.data.high} / {hoveredPoint.data.low}
            </span>
          </div>
          <div>
            <span>Volume:</span>
            <span>{hoveredPoint.data.volume?.toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
}
