import { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import api from "../api/client";

const MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"];
const PERIODS = ["1M", "3M", "6M", "1Y", "5Y"];
const POPULAR_TICKERS = {
  NSE: ["TCS", "RELIANCE", "INFY", "HDFCBANK", "WIPRO"],
  BSE: ["TCS", "RELIANCE", "INFY", "TATAMOTORS"],
  NASDAQ: ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"],
  NYSE: ["JPM", "V", "KO", "DIS", "WMT"],
};
const AGENTS = [
  { id: "fundamental", name: "Fundamental Analysis Agent", desc: "Evaluates revenue growth, margins, P/E valuation, and balance sheet health." },
  { id: "technical", name: "Technical Analysis Agent", desc: "Inspects SMA-20/SMA-50 crossovers, RSI-14 momentum, and OHLCV price trends." },
  { id: "sentiment", name: "News and Sentiment Analysis Agent", desc: "Scans recent headlines, earnings tone, and market sentiment signals." },
  { id: "risk", name: "Risk Analysis Agent", desc: "Measures annualized volatility, drawdown exposure, and concentration risk." },
];

function formatLocalTime(isoStr) {
  if (!isoStr) return "—";
  const hasTz = isoStr.endsWith("Z") || /[+-]\d{2}:\d{2}$/.test(isoStr);
  return new Date(hasTz ? isoStr : `${isoStr}Z`).toLocaleString();
}

export default function Dashboard({ user, onLogout }) {
  const [market, setMarket] = useState("NSE");
  const [period, setPeriod] = useState("1Y");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchMeta, setSearchMeta] = useState(null);
  const [searching, setSearching] = useState(false);
  const [watchlist, setWatchlist] = useState([]);
  const [history, setHistory] = useState([]);
  const [selectedTask, setSelectedTask] = useState(null);
  const [activeSection, setActiveSection] = useState("prices");
  const [statementTab, setStatementTab] = useState("income_statement");
  const [activeAgent, setActiveAgent] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [runningResearch, setRunningResearch] = useState(false);
  const [portfolio, setPortfolio] = useState([]);
  const [orders, setOrders] = useState([]);
  const [orderQty, setOrderQty] = useState(1);
  const [placingOrder, setPlacingOrder] = useState(false);

  const loadWorkspace = async () => {
    try {
      const [prefRes, watchRes, histRes, portRes, ordRes] = await Promise.all([
        api.get("/api/workspace/preferences"),
        api.get("/api/workspace/watchlist"),
        api.get("/api/workspace/research"),
        api.get("/api/workspace/portfolio"),
        api.get("/api/workspace/orders"),
      ]);
      setMarket(prefRes.data.market);
      setPeriod(prefRes.data.analysis_period);
      setWatchlist(watchRes.data);
      setHistory(histRes.data);
      setPortfolio(portRes.data);
      setOrders(ordRes.data);
      if (histRes.data.length > 0 && !selectedTask) {
        setSelectedTask(histRes.data[0]);
      }
    } catch {
      setErrorMsg("Failed to load workspace data.");
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    const trimmed = searchQuery.trim();
    if (trimmed.length < 2) {
      setSearchResults([]);
      setSearchMeta(null);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      setErrorMsg("");
      try {
        const res = await api.get("/api/workspace/stocks/search", {
          params: { query: trimmed, market },
        });
        setSearchResults(res.data.results || []);
        setSearchMeta({
          data_source: res.data.data_source,
          retrieved_at: res.data.retrieved_at,
        });
      } catch {
        setSearchResults([]);
        setSearchMeta(null);
      } finally {
        setSearching(false);
      }
    }, 450);

    return () => clearTimeout(timer);
  }, [searchQuery, market]);

  const savePreferences = async (newMarket, newPeriod) => {
    setMarket(newMarket);
    setPeriod(newPeriod);
    try {
      await api.put("/api/workspace/preferences", {
        market: newMarket,
        analysis_period: newPeriod,
      });
      setStatusMsg(`Preferences saved (${newMarket}, ${newPeriod}).`);
    } catch {
      setErrorMsg("Could not save preferences.");
    }
  };

  const addToWatchlist = async (item) => {
    setErrorMsg("");
    try {
      const res = await api.post("/api/workspace/watchlist", {
        ticker: item.ticker,
        company_name: item.company_name,
        market: item.market || market,
      });
      setWatchlist((prev) => [res.data, ...prev]);
      setStatusMsg(`Added ${res.data.ticker} to watchlist.`);
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Could not add stock to watchlist.");
    }
  };

  const removeFromWatchlist = async (savedStockId) => {
    try {
      await api.delete(`/api/workspace/watchlist/${savedStockId}`);
      setWatchlist((prev) => prev.filter((s) => s.saved_stock_id !== savedStockId));
    } catch {
      setErrorMsg("Could not remove stock.");
    }
  };

  const launchResearch = async (ticker, tickerMarket = market) => {
    setRunningResearch(true);
    setErrorMsg("");
    setStatusMsg(`Collecting Yahoo Finance data for ${ticker} (${tickerMarket}, ${period})...`);
    try {
      const res = await api.post("/api/workspace/research", {
        ticker,
        market: tickerMarket,
        analysis_period: period,
      });
      setHistory((prev) => [res.data, ...prev]);
      setSelectedTask(res.data);
      setSearchResults([]);
      setStatusMsg(
        res.data.status === "Completed"
          ? `Research completed for ${res.data.ticker}.`
          : `Research failed for ${res.data.ticker}: ${res.data.error_message || "Unknown error"}`
      );
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Research workflow failed.");
    } finally {
      setRunningResearch(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim() || runningResearch) return;
    const targetTicker = searchResults[0]?.ticker || searchQuery.trim().toUpperCase();
    const targetMarket = searchResults[0]?.market || market;
    launchResearch(targetTicker, targetMarket);
  };


  const placeOrder = async (side, ticker, tickerMarket = market) => {
    const qty = Number(orderQty);
    if (!ticker || !qty || qty <= 0) return;
    setPlacingOrder(true);
    setErrorMsg("");
    try {
      const res = await api.post("/api/workspace/orders", {
        ticker,
        market: tickerMarket,
        side,
        quantity: qty,
      });
      setOrders((prev) => [res.data, ...prev]);
      const portRes = await api.get("/api/workspace/portfolio");
      setPortfolio(portRes.data);
      setStatusMsg(
        `${side} order executed: ${res.data.quantity} ${res.data.ticker} @ ${res.data.price_per_share} ${res.data.currency} (Total: ${res.data.total_amount} ${res.data.currency}).`
      );
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || "Order execution failed.");
    } finally {
      setPlacingOrder(false);
    }
  };
const reportData = selectedTask?.report_data;
  const chartSeries = reportData?.series;
  const activeStatements = reportData?.financial_statements?.[statementTab] || [];

  const ohlcvRows = chartSeries
    ? chartSeries.dates
        .map((date, idx) => ({
          date,
          open: chartSeries.open?.[idx],
          high: chartSeries.high?.[idx],
          low: chartSeries.low?.[idx],
          close: chartSeries.close?.[idx],
          volume: chartSeries.volume?.[idx],
        }))
        .slice(-15)
        .reverse()
    : [];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Multi-Agent Stock Research Analyst</h1>
          <p className="text-xs text-slate-400">Welcome back, {user.full_name} ({user.email})</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={market}
            onChange={(e) => savePreferences(e.target.value, period)}
            className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-1.5 text-sm text-white"
          >
            {MARKETS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          <select
            value={period}
            onChange={(e) => savePreferences(market, e.target.value)}
            className="rounded-lg bg-slate-800 border border-slate-700 px-3 py-1.5 text-sm text-white"
          >
            {PERIODS.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>

          <button
            onClick={onLogout}
            className="rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 text-sm text-slate-200"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {statusMsg && (
          <div className="rounded-lg bg-indigo-950/70 border border-indigo-700 px-4 py-2 text-sm text-indigo-200">
            {statusMsg}
          </div>
        )}
        {errorMsg && (
          <div className="rounded-lg bg-rose-950/70 border border-rose-700 px-4 py-2 text-sm text-rose-200">
            {errorMsg}
          </div>
        )}

        {/* Auto-Search + Popular Quick-Pick Tickers + Run Research */}
        <section className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
          <form onSubmit={handleSearchSubmit} className="flex flex-wrap gap-3">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={`Type company name or ticker on ${market} (e.g., ${market === "NSE" ? "Tata Consultancy or TCS" : "Apple or AAPL"})`}
              className="flex-1 min-w-[240px] rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-white focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={!searchQuery.trim() || runningResearch}
              className="rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-5 py-2 text-sm font-medium text-white"
            >
              {runningResearch ? "Analyzing..." : "Run Research"}
            </button>
          </form>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400">Popular on {market}:</span>
            {(POPULAR_TICKERS[market] || []).map((sym) => (
              <button
                key={sym}
                type="button"
                disabled={runningResearch}
                onClick={() => {
                  setSearchQuery(sym);
                  launchResearch(sym, market);
                }}
                className="rounded-full bg-slate-800 hover:bg-indigo-600 border border-slate-700 px-3 py-1 text-slate-200 transition"
              >
                {sym}
              </button>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
              Specialized Research Agents
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {AGENTS.map((agent) => (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => {
                    setActiveAgent(agent);
                    const target = selectedTask?.ticker || searchQuery.trim().toUpperCase() || "selected stock";
                    setStatusMsg(`${agent.name} selected for ${target}.`);
                  }}
                  className={`text-left rounded-xl border px-3 py-2.5 text-sm font-medium transition ${
                    activeAgent?.id === agent.id
                      ? "bg-indigo-600/20 border-indigo-500 text-white"
                      : "bg-slate-800/70 hover:bg-slate-800 border-slate-700 text-slate-200"
                  }`}
                >
                  {agent.name}
                </button>
              ))}
            </div>
            {activeAgent && (
              <div className="mt-3 rounded-lg bg-slate-950/70 border border-slate-800 px-3 py-2 text-xs text-slate-300">
                <span className="font-semibold text-indigo-400">{activeAgent.name}:</span> {activeAgent.desc}
              </div>
            )}
          </div>

          {searching && (
            <div className="mt-2 text-xs text-slate-400">Searching Yahoo Finance ({market})...</div>
          )}

          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              {searchMeta && (
                <div className="text-xs text-slate-400">
                  Source: {searchMeta.data_source} · Retrieved: {formatLocalTime(searchMeta.retrieved_at)}
                </div>
              )}
              {searchResults.map((item) => (
                <div
                  key={item.yf_symbol}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-xl bg-slate-800/70 border border-slate-700 p-3"
                >
                  <div>
                    <div className="font-semibold text-white">
                      {item.company_name} ({item.yf_symbol})
                    </div>
                    <div className="text-xs text-slate-400">
                      Market: {item.market} · Exchange: {item.exchange}
                      {item.latest_price ? ` · Last Close: ${item.latest_price} ${item.currency}` : ""}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => addToWatchlist(item)}
                      className="rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-medium text-white"
                    >
                      + Add to Watchlist
                    </button>
                    <button
                      disabled={runningResearch}
                      onClick={() => launchResearch(item.ticker, item.market)}
                      className="rounded-lg bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 text-xs font-medium text-white"
                    >
                      Analyze Now
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Watchlist */}
          <section className="rounded-2xl bg-slate-900 border border-slate-800 p-5">
            <h2 className="text-lg font-semibold text-white mb-3">Saved Watchlist</h2>
            {watchlist.length === 0 ? (
              <p className="text-sm text-slate-400">No stocks saved yet. Type a company above to add it.</p>
            ) : (
              <ul className="space-y-2">
                {watchlist.map((item) => (
                  <li
                    key={item.saved_stock_id}
                    className="flex items-center justify-between gap-2 rounded-lg bg-slate-800/60 border border-slate-700/70 px-3 py-2"
                  >
                    <div>
                      <div className="font-medium text-white">{item.ticker}</div>
                      <div className="text-xs text-slate-400">
                        {item.company_name} · {item.market}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        disabled={runningResearch}
                        onClick={() => launchResearch(item.ticker, item.market)}
                        className="text-xs rounded bg-indigo-600 hover:bg-indigo-500 px-2.5 py-1 text-white"
                      >
                        Research
                      </button>
                      <button
                        onClick={() => removeFromWatchlist(item.saved_stock_id)}
                        className="text-xs rounded bg-slate-700 hover:bg-rose-600 px-2.5 py-1 text-slate-200"
                      >
                        Remove
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
{/* Separated Tabs: Historical Stock Prices | OHLCV Data | Company Profile | Financial Statements */}
          <section className="lg:col-span-2 rounded-2xl bg-slate-900 border border-slate-800 p-5">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <h2 className="text-lg font-semibold text-white">
                {selectedTask
                  ? `${selectedTask.company_name || selectedTask.ticker} (${selectedTask.market} · ${selectedTask.analysis_period})`
                  : "Research Report Viewer"}
              </h2>
              {selectedTask && selectedTask.status === "Completed" && (
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    value={orderQty}
                    onChange={(e) => setOrderQty(e.target.value)}
                    className="w-20 rounded-lg bg-slate-800 border border-slate-700 px-2.5 py-1 text-sm text-white"
                  />
                  <button
                    type="button"
                    disabled={placingOrder}
                    onClick={() => placeOrder("BUY", selectedTask.ticker, selectedTask.market)}
                    className="rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-3 py-1.5 text-xs font-semibold text-white"
                  >
                    {placingOrder ? "..." : "Buy Stock"}
                  </button>
                  <button
                    type="button"
                    disabled={placingOrder}
                    onClick={() => placeOrder("SELL", selectedTask.ticker, selectedTask.market)}
                    className="rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-50 px-3 py-1.5 text-xs font-semibold text-white"
                  >
                    Sell Stock
                  </button>
                </div>
              )}
            </div>

            {!selectedTask ? (
              <p className="text-sm text-slate-400">Run a research task or select one from your history below.</p>
            ) : selectedTask.status === "Failed" ? (
              <div className="rounded-lg bg-rose-950/70 border border-rose-700 p-4 text-sm text-rose-200 flex flex-wrap items-center justify-between gap-3">
                <span>Task Failed: {selectedTask.error_message}</span>
                <button
                  disabled={runningResearch}
                  onClick={() => launchResearch(selectedTask.ticker, selectedTask.market)}
                  className="rounded-lg bg-rose-700 hover:bg-rose-600 px-3 py-1.5 text-xs font-medium text-white"
                >
                  Retry
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {reportData?.data_source && (
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-slate-950/70 border border-slate-800 px-3 py-2 text-xs text-slate-400">
                    <span>
                      Source:{" "}
                      <a
                        href={reportData.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:underline"
                      >
                        {reportData.data_source}
                      </a>
                    </span>
                    <span>Retrieved: {formatLocalTime(reportData.retrieved_at)}</span>
                  </div>
                )}

                {reportData?.data_quality && (
                  <div className="flex flex-wrap items-center gap-3 rounded-lg bg-emerald-950/40 border border-emerald-800/70 px-3 py-2 text-xs text-emerald-200">
                    <span className="font-semibold">Validation: {reportData.data_quality.validation_status}</span>
                    <span>Valid Rows: {reportData.data_quality.total_valid_rows}</span>
                    <span>Duplicates Removed: {reportData.data_quality.duplicate_dates_removed}</span>
                    <span>Missing Handled: {reportData.data_quality.missing_values_handled}</span>
                    <span>Inconsistent Fixed: {reportData.data_quality.inconsistent_rows_fixed}</span>
                  </div>
                )}

                {/* Separate Tabs */}
                <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2 text-xs font-medium">
                  {[
                    ["prices", "Historical Stock Prices"],
                    ["ohlcv", "OHLCV Data"],
                    ["profile", "Company Profile"],
                    ["financials", "Financial Statements"],
                  ].map(([key, label]) => (
                    <button
                      key={key}
                      onClick={() => setActiveSection(key)}
                      className={`px-3 py-1.5 rounded-lg transition ${
                        activeSection === key
                          ? "bg-indigo-600 text-white"
                          : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>

                {/* Tab 1: Historical Stock Prices */}
                {activeSection === "prices" && chartSeries && (
                  <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                    <Plot
                      data={[
                        {
                          x: chartSeries.dates,
                          y: chartSeries.close,
                          type: "scatter",
                          mode: "lines",
                          name: "Close Price",
                          line: { color: "#6366f1", width: 2 },
                        },
                        {
                          x: chartSeries.dates,
                          y: chartSeries.sma_20,
                          type: "scatter",
                          mode: "lines",
                          name: "SMA 20",
                          line: { color: "#10b981", width: 1.5, dash: "dot" },
                        },
                        {
                          x: chartSeries.dates,
                          y: chartSeries.sma_50,
                          type: "scatter",
                          mode: "lines",
                          name: "SMA 50",
                          line: { color: "#f59e0b", width: 1.5, dash: "dash" },
                        },
                      ]}
                      layout={{
                        autosize: true,
                        height: 320,
                        margin: { t: 24, r: 20, b: 40, l: 50 },
                        paper_bgcolor: "#020617",
                        plot_bgcolor: "#020617",
                        font: { color: "#cbd5e1" },
                        legend: { orientation: "h", y: 1.12 },
                      }}
                      useResizeHandler
                      style={{ width: "100%" }}
                    />
                  </div>
                )}

                {/* Tab 2: OHLCV Data (Candlestick + Table) */}
                {activeSection === "ohlcv" && chartSeries && (
                  <div className="space-y-4">
                    <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                      <Plot
                        data={[
                          {
                            x: chartSeries.dates,
                            open: chartSeries.open,
                            high: chartSeries.high,
                            low: chartSeries.low,
                            close: chartSeries.close,
                            type: "candlestick",
                            name: "OHLC",
                          },
                        ]}
                        layout={{
                          autosize: true,
                          height: 300,
                          margin: { t: 24, r: 20, b: 40, l: 50 },
                          paper_bgcolor: "#020617",
                          plot_bgcolor: "#020617",
                          font: { color: "#cbd5e1" },
                          xaxis: { rangeslider: { visible: false } },
                        }}
                        useResizeHandler
                        style={{ width: "100%" }}
                      />
                    </div>
                    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3 overflow-x-auto">
                      <div className="text-xs font-semibold uppercase text-slate-400 mb-2">
                        OHLCV Table (Open, High, Low, Close, Volume — Latest 15 Trading Days)
                      </div>
                      <table className="w-full text-xs text-left">
                        <thead className="text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="py-1 pr-3">Date</th>
                            <th className="py-1 pr-3 text-right">Open</th>
                            <th className="py-1 pr-3 text-right">High</th>
                            <th className="py-1 pr-3 text-right">Low</th>
                            <th className="py-1 pr-3 text-right">Close</th>
                            <th className="py-1 text-right">Volume</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {ohlcvRows.map((row) => (
                            <tr key={row.date}>
                              <td className="py-1 pr-3 text-slate-200">{row.date}</td>
                              <td className="py-1 pr-3 text-right text-slate-300">{row.open}</td>
                              <td className="py-1 pr-3 text-right text-slate-300">{row.high}</td>
                              <td className="py-1 pr-3 text-right text-slate-300">{row.low}</td>
                              <td className="py-1 pr-3 text-right font-medium text-white">{row.close}</td>
                              <td className="py-1 text-right text-slate-300">
                                {Number(row.volume).toLocaleString()}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Tab 3: Company Profile */}
                {activeSection === "profile" && reportData && (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div className="rounded-lg bg-slate-950/70 border border-slate-800 p-2.5">
                        <div className="text-slate-400">Sector</div>
                        <div className="font-medium text-white truncate">{reportData.sector || "N/A"}</div>
                      </div>
                      <div className="rounded-lg bg-slate-950/70 border border-slate-800 p-2.5">
                        <div className="text-slate-400">Industry</div>
                        <div className="font-medium text-white truncate">{reportData.industry || "N/A"}</div>
                      </div>
                      <div className="rounded-lg bg-slate-950/70 border border-slate-800 p-2.5">
                        <div className="text-slate-400">Market Cap</div>
                        <div className="font-medium text-white">
                          {reportData.market_cap ? Number(reportData.market_cap).toLocaleString() : "N/A"}
                        </div>
                      </div>
                      <div className="rounded-lg bg-slate-950/70 border border-slate-800 p-2.5">
                        <div className="text-slate-400">P/E Ratio</div>
                        <div className="font-medium text-white">
                          {reportData.pe_ratio ? Number(reportData.pe_ratio).toFixed(2) : "N/A"}
                        </div>
                      </div>
                    </div>
                    {reportData.website && (
                      <div className="text-xs text-slate-400">
                        Website:{" "}
                        <a href={reportData.website} target="_blank" rel="noreferrer" className="text-indigo-400 hover:underline">
                          {reportData.website}
                        </a>
                      </div>
                    )}
                    <p className="text-xs text-slate-300 bg-slate-950/50 border border-slate-800 rounded-lg p-3 leading-relaxed">
                      {reportData.business_summary || "Company business summary unavailable."}
                    </p>
                  </div>
                )}
{/* Tab 4: Financial Statements */}
                {activeSection === "financials" && reportData?.financial_statements && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3 overflow-x-auto">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                      <span className="text-xs font-semibold uppercase text-slate-400">
                        Financial Statements
                      </span>
                      <div className="flex gap-1.5 text-xs">
                        {[
                          ["income_statement", "Income"],
                          ["balance_sheet", "Balance Sheet"],
                          ["cash_flow", "Cash Flow"],
                        ].map(([key, label]) => (
                          <button
                            key={key}
                            onClick={() => setStatementTab(key)}
                            className={`px-2 py-0.5 rounded ${
                              statementTab === key ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300"
                            }`}
                          >
                            {label}
                          </button>
                        ))}
                      </div>
                    </div>
                    {activeStatements.length === 0 ? (
                      <div className="text-xs text-slate-500">No statement data available.</div>
                    ) : (
                      <table className="w-full text-xs text-left">
                        <thead className="text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="py-1 pr-3">Metric</th>
                            {Object.keys(activeStatements[0].values).map((d) => (
                              <th key={d} className="py-1 pr-3 text-right">{d}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {activeStatements.slice(0, 8).map((row) => (
                            <tr key={row.metric}>
                              <td className="py-1 pr-3 text-slate-200">{row.metric}</td>
                              {Object.values(row.values).map((v, idx) => (
                                <td key={idx} className="py-1 pr-3 text-right text-slate-300">
                                  {v === null ? "—" : Number(v).toLocaleString()}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                )}

                <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-200 bg-slate-950/70 border border-slate-800 rounded-xl p-4">
                  {selectedTask.summary_markdown}
                </pre>
              </div>
            )}
          </section>
        </div>

        {/* Portfolio Holdings & Buy/Sell Orders */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <section className="rounded-2xl bg-slate-900 border border-slate-800 p-5 overflow-x-auto">
            <h2 className="text-lg font-semibold text-white mb-3">My Portfolio Holdings</h2>
            {portfolio.length === 0 ? (
              <p className="text-sm text-slate-400">No shares owned yet. Select any stock and click Buy Stock.</p>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2 pr-3">Ticker</th>
                    <th className="py-2 pr-3">Market</th>
                    <th className="py-2 pr-3 text-right">Qty</th>
                    <th className="py-2 text-right">Avg Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  {portfolio.map((h) => (
                    <tr key={h.holding_id}>
                      <td className="py-2 pr-3 font-medium text-white">{h.company_name || h.ticker} ({h.ticker})</td>
                      <td className="py-2 pr-3">{h.market}</td>
                      <td className="py-2 pr-3 text-right text-emerald-300 font-semibold">{h.quantity}</td>
                      <td className="py-2 text-right text-slate-300">{h.average_price} {h.currency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          <section className="rounded-2xl bg-slate-900 border border-slate-800 p-5 overflow-x-auto">
            <h2 className="text-lg font-semibold text-white mb-3">Buy / Sell Order History</h2>
            {orders.length === 0 ? (
              <p className="text-sm text-slate-400">No orders placed yet.</p>
            ) : (
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2 pr-3">Side</th>
                    <th className="py-2 pr-3">Ticker</th>
                    <th className="py-2 pr-3 text-right">Qty</th>
                    <th className="py-2 pr-3 text-right">Total</th>
                    <th className="py-2">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/70">
                  {orders.map((o) => (
                    <tr key={o.order_id}>
                      <td className="py-2 pr-3">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${o.side === "BUY" ? "bg-emerald-950 text-emerald-300" : "bg-rose-950 text-rose-300"}`}>
                          {o.side}
                        </span>
                      </td>
                      <td className="py-2 pr-3 font-medium text-white">{o.ticker} ({o.market})</td>
                      <td className="py-2 pr-3 text-right">{o.quantity}</td>
                      <td className="py-2 pr-3 text-right text-slate-300">{o.total_amount} {o.currency}</td>
                      <td className="py-2 text-slate-400 text-xs">{formatLocalTime(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>

        {/* Research History */}
        <section className="rounded-2xl bg-slate-900 border border-slate-800 p-5 overflow-x-auto">
          <h2 className="text-lg font-semibold text-white mb-3">Research History</h2>
          {history.length === 0 ? (
            <p className="text-sm text-slate-400">No research tasks yet.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2 pr-4">Company / Ticker</th>
                  <th className="py-2 pr-4">Market</th>
                  <th className="py-2 pr-4">Period</th>
                  <th className="py-2 pr-4">Date</th>
                  <th className="py-2 pr-4">Status</th>
                  <th className="py-2">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {history.map((task) => (
                  <tr key={task.task_id}>
                    <td className="py-2.5 pr-4 font-medium text-white">
                      {task.company_name || task.ticker} ({task.ticker})
                    </td>
                    <td className="py-2.5 pr-4">{task.market}</td>
                    <td className="py-2.5 pr-4">{task.analysis_period}</td>
                    <td className="py-2.5 pr-4 text-slate-400">
                      {formatLocalTime(task.created_at)}
                    </td>
                    <td className="py-2.5 pr-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs ${
                          task.status === "Completed"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-700"
                            : task.status === "Failed"
                            ? "bg-rose-950 text-rose-300 border border-rose-700"
                            : "bg-amber-950 text-amber-300 border border-amber-700"
                        }`}
                      >
                        {task.status}
                      </span>
                    </td>
                    <td className="py-2.5">
                      <button
                        onClick={() => setSelectedTask(task)}
                        className="text-indigo-400 hover:underline"
                      >
                        Open Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </main>
    </div>
  );
}                            