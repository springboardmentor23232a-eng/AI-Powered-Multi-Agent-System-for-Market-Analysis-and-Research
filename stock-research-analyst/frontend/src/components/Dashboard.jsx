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
const DUMMY_AGENTS = [
  {
    id: "fundamental",
    name: "Fundamental Analysis Agent",
    desc: "Evaluates revenue growth, margins, P/E valuation, and balance sheet health.",
  },
  {
    id: "technical",
    name: "Technical Analysis Agent",
    desc: "Inspects SMA-20/SMA-50 crossovers, RSI-14 momentum, and OHLCV price trends.",
  },
  {
    id: "sentiment",
    name: "News and Sentiment Analysis Agent",
    desc: "Scans recent headlines, earnings tone, and market sentiment signals.",
  },
  {
    id: "risk",
    name: "Risk Analysis Agent",
    desc: "Measures annualized volatility, drawdown exposure, and concentration risk.",
  },
];

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
  const [chartMode, setChartMode] = useState("candlestick");
  const [statementTab, setStatementTab] = useState("income_statement");
  const [activeDummyAgent, setActiveDummyAgent] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [runningResearch, setRunningResearch] = useState(false);

  const loadWorkspace = async () => {
    try {
      const [prefRes, watchRes, histRes] = await Promise.all([
        api.get("/api/workspace/preferences"),
        api.get("/api/workspace/watchlist"),
        api.get("/api/workspace/research"),
      ]);
      setMarket(prefRes.data.market);
      setPeriod(prefRes.data.analysis_period);
      setWatchlist(watchRes.data);
      setHistory(histRes.data);
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
    setStatusMsg(`Collecting Yahoo Finance OHLCV & financials for ${ticker} (${tickerMarket}, ${period})...`);
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

  const triggerDummyAgent = (agent) => {
    setActiveDummyAgent(agent);
    const target = selectedTask?.ticker || searchQuery.trim().toUpperCase() || "selected stock";
    setStatusMsg(`[Dummy Agent] ${agent.name} triggered for ${target}.`);
  };

  const reportData = selectedTask?.report_data;
  const chartSeries = reportData?.series;
  const activeStatements = reportData?.financial_statements?.[statementTab] || [];

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

        {/* Auto-Search + Quick-Pick Popular Tickers + Run Research */}
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

          {/* Popular Quick-Pick Chips */}
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

          {searching && (
            <div className="mt-2 text-xs text-slate-400">Searching Yahoo Finance ({market})...</div>
          )}

          {/* Dummy Agent Buttons */}
          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
              Specialized Research Agents (Dummy Preview)
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
              {DUMMY_AGENTS.map((agent) => (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => triggerDummyAgent(agent)}
                  className={`text-left rounded-xl border px-3 py-2.5 text-sm font-medium transition ${
                    activeDummyAgent?.id === agent.id
                      ? "bg-indigo-600/20 border-indigo-500 text-white"
                      : "bg-slate-800/70 hover:bg-slate-800 border-slate-700 text-slate-200"
                  }`}
                >
                  {agent.name}
                </button>
              ))}
            </div>
            {activeDummyAgent && (
              <div className="mt-3 rounded-lg bg-slate-950/70 border border-slate-800 px-3 py-2 text-xs text-slate-300">
                <span className="font-semibold text-indigo-400">{activeDummyAgent.name}:</span>{" "}
                {activeDummyAgent.desc} (Dummy placeholder ready for full agent wiring.)
              </div>
            )}
          </div>

          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              {searchMeta && (
                <div className="text-xs text-slate-400">
                  Source: {searchMeta.data_source} · Retrieved: {new Date(searchMeta.retrieved_at).toLocaleString()}
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

          {/* OHLCV Plotly Chart + Profile + Financials + Report */}
          <section className="lg:col-span-2 rounded-2xl bg-slate-900 border border-slate-800 p-5">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
              <h2 className="text-lg font-semibold text-white">
                {selectedTask
                  ? `${selectedTask.company_name || selectedTask.ticker} (${selectedTask.market} · ${selectedTask.analysis_period})`
                  : "Research Report Viewer"}
              </h2>
              {chartSeries && (
                <div className="flex gap-2 text-xs">
                  <button
                    onClick={() => setChartMode("candlestick")}
                    className={`px-2.5 py-1 rounded ${chartMode === "candlestick" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300"}`}
                  >
                    OHLC Candlestick
                  </button>
                  <button
                    onClick={() => setChartMode("line")}
                    className={`px-2.5 py-1 rounded ${chartMode === "line" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-300"}`}
                  >
                    Close + SMA
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
                    <span>Retrieved: {new Date(reportData.retrieved_at).toLocaleString()}</span>
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

                {reportData && (
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
                )}

                {chartSeries && (
                  <div className="rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
                    <Plot
                      data={
                        chartMode === "candlestick" && chartSeries.open
                          ? [
                              {
                                x: chartSeries.dates,
                                open: chartSeries.open,
                                high: chartSeries.high,
                                low: chartSeries.low,
                                close: chartSeries.close,
                                type: "candlestick",
                                name: "OHLC",
                              },
                              {
                                x: chartSeries.dates,
                                y: chartSeries.sma_20,
                                type: "scatter",
                                mode: "lines",
                                name: "SMA 20",
                                line: { color: "#10b981", width: 1.5 },
                              },
                            ]
                          : [
                              {
                                x: chartSeries.dates,
                                y: chartSeries.close,
                                type: "scatter",
                                mode: "lines",
                                name: "Close",
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
                            ]
                      }
                      layout={{
                        autosize: true,
                        height: 320,
                        margin: { t: 24, r: 20, b: 40, l: 50 },
                        paper_bgcolor: "#020617",
                        plot_bgcolor: "#020617",
                        font: { color: "#cbd5e1" },
                        xaxis: { rangeslider: { visible: false } },
                        legend: { orientation: "h", y: 1.12 },
                      }}
                      useResizeHandler
                      style={{ width: "100%" }}
                    />
                  </div>
                )}

                {reportData?.financial_statements && (
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
                          {activeStatements.slice(0, 6).map((row) => (
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
                      {new Date(task.created_at).toLocaleString()}
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
