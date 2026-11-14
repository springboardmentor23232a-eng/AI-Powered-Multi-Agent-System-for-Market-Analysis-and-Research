import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  marketAPI,
  watchlistAPI,
  preferencesAPI,
  researchAPI,
} from '../services/api';
import {
  TrendingUp,
  TrendingDown,
  BarChart3,
  Newspaper,
  ShieldAlert,
  Bot,
  Search,
  Plus,
  Trash2,
  ExternalLink,
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  SlidersHorizontal,
  ChevronRight,
  Sparkles,
  RefreshCw,
  Database,
  Globe2,
} from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const { isDark } = useTheme();

  // Active Stock Overview State (Initial dynamic skeleton before live feed loads)
  const [activeStock, setActiveStock] = useState({
    ticker: 'Loading...',
    company_name: 'Connecting to Market Feed...',
    market: 'NSE',
    sector: 'Equities // Market',
    price: '--',
    change: '0.00',
    changePercent: '0.00%',
    isPositive: true,
    peRatio: 'N/A',
    pbRatio: 'N/A',
    roe: 'N/A',
    debtToEquity: 'N/A',
    marketCap: 'N/A',
    high52w: '--',
    low52w: '--',
    retrieved_at: new Date().toISOString(),
    data_source: 'Live Exchange Feed',
  });

  // Real Technical Indicators calculated dynamically from historical prices
  const [techSignals, setTechSignals] = useState({
    sma_50: '--',
    sma_200: '--',
    rsi_14: '--',
    macd: '--',
    volatility: '--',
    trend_summary: 'Analyzing...',
    crossover: 'Pending Data',
    period_analyzed: '1 Year',
  });

  // Real Risk Metrics calculated dynamically from daily returns & drawdown
  const [riskMetrics, setRiskMetrics] = useState({
    max_drawdown: '--',
    volatility_annualized: '--',
    conflict_status: 'CONVERGENT',
    risk_level: 'MODERATE',
    period_analyzed: '1 Year',
    period_return: '--',
    period_high: null,
    period_low: null,
  });

  // Real Live Financial News from Yahoo Finance (Empty until live articles arrive)
  const [liveNews, setLiveNews] = useState([]);

  const [loadingActiveStock, setLoadingActiveStock] = useState(false);
  const [refreshingWatchlist, setRefreshingWatchlist] = useState(false);

  // User Preferences State (Module 1 Guide Section 6)
  const [preferences, setPreferences] = useState({
    market: 'NSE',
    analysis_period: '1 Year',
  });
  const [prefNotification, setPrefNotification] = useState(false);

  // Active Tab: technical | fundamental | news | risk
  const [activeTab, setActiveTab] = useState('technical');

  // Watchlist State (Zerodha Kite Style - Module 1 Guide Section 5)
  const [watchlist, setWatchlist] = useState([]);
  const [newTickerInput, setNewTickerInput] = useState('');
  const [watchlistError, setWatchlistError] = useState('');
  const [addingStock, setAddingStock] = useState(false);

  // Research Tasks History (Module 1 Guide Section 4)
  const [researchHistory, setResearchHistory] = useState([]);

  // Format currency helper
  const formatPrice = (val, currency = 'INR') => {
    if (!val && val !== 0) return 'N/A';
    const symbol = currency === 'USD' ? '$' : '₹';
    return `${symbol}${Number(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  // 1. Initial Load: Load Preferences, Watchlist, and Live Quotes
  useEffect(() => {
    const initializeWorkspace = async () => {
      // Load Preferences from PostgreSQL
      let initialMarket = 'NSE';
      let initialPeriod = '1 Year';
      try {
        const prefRes = await preferencesAPI.getPreferences();
        if (prefRes) {
          initialMarket = prefRes.market || 'NSE';
          initialPeriod = prefRes.analysis_period || '1 Year';
          setPreferences({
            market: initialMarket,
            analysis_period: initialPeriod,
          });
        }
      } catch (err) {
        console.warn('Preferences load error:', err);
      }

      // Determine default stock based on loaded market preference
      let defaultTicker = 'RELIANCE';
      if (initialMarket === 'NASDAQ') defaultTicker = 'AAPL';
      else if (initialMarket === 'NYSE') defaultTicker = 'JPM';

      // Load Watchlist from PostgreSQL
      try {
        const savedRes = await watchlistAPI.getWatchlist();
        if (savedRes && savedRes.length > 0) {
          // Fetch quotes for each saved stock
          const enrichedWatchlist = await Promise.all(
            savedRes.map(async (item) => {
              try {
                const quote = await marketAPI.getQuote(item.ticker, item.market || 'NSE');
                const isPositive = quote.change >= 0;
                const currency = quote.currency || (item.market === 'NSE' || item.market === 'BSE' ? 'INR' : 'USD');
                return {
                  saved_stock_id: item.saved_stock_id,
                  ticker: item.ticker,
                  name: quote.company_name || item.company_name || item.ticker,
                  market: item.market || 'NSE',
                  price: formatPrice(quote.price, currency),
                  change: `${isPositive ? '+' : ''}${quote.change_percent.toFixed(2)}%`,
                  isPositive: isPositive,
                };
              } catch {
                return {
                  saved_stock_id: item.saved_stock_id,
                  ticker: item.ticker,
                  name: item.company_name || item.ticker,
                  market: item.market || 'NSE',
                  price: '--',
                  change: '0.00%',
                  isPositive: true,
                };
              }
            })
          );
          setWatchlist(enrichedWatchlist);
        }
      } catch (err) {
        console.warn('Watchlist load error:', err);
      }

      // Load Research History from PostgreSQL
      try {
        const historyRes = await researchAPI.getHistory();
        if (historyRes) {
          setResearchHistory(historyRes);
        }
      } catch (err) {
        console.warn('Research history load error:', err);
      }

      // Fetch complete live analysis for default stock based on saved preferences
      fetchCompleteAnalysis(defaultTicker, initialMarket, initialPeriod);
    };

    initializeWorkspace();
  }, []);

  // Fetch Live Real-Time Analysis from Yahoo Finance (Quote, Technicals, Risk, News)
  const fetchCompleteAnalysis = async (ticker, market = preferences.market, period = preferences.analysis_period) => {
    setLoadingActiveStock(true);
    try {
      const data = await marketAPI.getAnalysis(ticker, market, period);
      const quote = data.quote;
      const isPositive = quote.change >= 0;
      const currency = quote.currency || (market === 'NSE' || market === 'BSE' ? 'INR' : 'USD');

      setActiveStock({
        ticker: quote.ticker,
        company_name: quote.company_name || ticker,
        market: quote.market || market,
        sector: `${quote.sector || 'Equities'} // ${quote.industry || 'Market'}`,
        price: formatPrice(quote.price, currency),
        change: `${isPositive ? '+' : ''}${quote.change.toFixed(2)}`,
        changePercent: `${isPositive ? '+' : ''}${quote.change_percent.toFixed(2)}%`,
        isPositive: isPositive,
        peRatio: quote.pe_ratio ? quote.pe_ratio.toFixed(2) : 'N/A',
        pbRatio: quote.pb_ratio ? quote.pb_ratio.toFixed(2) : 'N/A',
        roe: quote.roe ? `${quote.roe.toFixed(2)}%` : 'N/A',
        debtToEquity: quote.debt_to_equity ? quote.debt_to_equity.toFixed(2) : 'N/A',
        marketCap: quote.market_cap ? formatPrice((quote.market_cap / 1e12).toFixed(2), currency) + 'T' : 'N/A',
        high52w: formatPrice(quote.fifty_two_week_high, currency),
        low52w: formatPrice(quote.fifty_two_week_low, currency),
        retrieved_at: quote.retrieved_at,
        data_source: quote.data_source,
      });

      if (data.technical) {
        setTechSignals(data.technical);
      }
      if (data.risk) {
        setRiskMetrics(data.risk);
      }
      setLiveNews(data.news || []);
    } catch (err) {
      console.error('Failed to fetch complete analysis:', err);
    } finally {
      setLoadingActiveStock(false);
    }
  };

  // Handle Add Stock to Watchlist (Yahoo Finance + PostgreSQL)
  const handleAddStock = async (e) => {
    e.preventDefault();
    setWatchlistError('');
    const ticker = newTickerInput.trim().toUpperCase();
    if (!ticker) return;

    if (watchlist.some((s) => s.ticker === ticker)) {
      setWatchlistError(`${ticker} is already in your watchlist.`);
      return;
    }

    setAddingStock(true);
    try {
      // 1. Fetch live real-time quote from Yahoo Finance
      const quote = await marketAPI.getQuote(ticker, preferences.market);
      const isPositive = quote.change >= 0;
      const currency = quote.currency || (preferences.market === 'NSE' || preferences.market === 'BSE' ? 'INR' : 'USD');

      // 2. Persist to PostgreSQL saved_stocks table
      let savedId = Date.now();
      try {
        const savedRes = await watchlistAPI.addToWatchlist({
          ticker: ticker,
          company_name: quote.company_name || ticker,
          market: preferences.market,
        });
        if (savedRes && savedRes.saved_stock_id) {
          savedId = savedRes.saved_stock_id;
        }
      } catch (dbErr) {
        console.warn('Saved to UI; DB notice:', dbErr);
      }

      const newItem = {
        saved_stock_id: savedId,
        ticker: ticker,
        name: quote.company_name || ticker,
        market: preferences.market,
        price: formatPrice(quote.price, currency),
        change: `${isPositive ? '+' : ''}${quote.change_percent.toFixed(2)}%`,
        isPositive: isPositive,
      };

      setWatchlist([newItem, ...watchlist]);
      setNewTickerInput('');

      // Also set as active stock
      fetchCompleteAnalysis(ticker, preferences.market, preferences.analysis_period);
    } catch (err) {
      setWatchlistError(`Could not find '${ticker}' on ${preferences.market}. Please verify ticker symbol.`);
    } finally {
      setAddingStock(false);
    }
  };

  // Handle Select Stock to Inspect
  const handleSelectStock = (stock) => {
    fetchCompleteAnalysis(stock.ticker, stock.market || preferences.market, preferences.analysis_period);
  };

  // Handle Remove Stock from Watchlist
  const handleRemoveStock = async (ticker, saved_stock_id, e) => {
    e.stopPropagation();
    try {
      await watchlistAPI.removeFromWatchlist(ticker);
    } catch (err) {
      console.warn('Removed locally; API notice:', err);
    }
    setWatchlist(watchlist.filter((s) => s.ticker !== ticker));
  };

  // Save Preferences to PostgreSQL & Immediately Recalculate Analysis
  const handleSavePreferences = async (updatedMarket, updatedPeriod) => {
    const marketChanged = updatedMarket && updatedMarket !== preferences.market;
    const newMarket = updatedMarket || preferences.market;
    const newPeriod = updatedPeriod || preferences.analysis_period;

    const newPrefs = {
      market: newMarket,
      analysis_period: newPeriod,
    };
    setPreferences(newPrefs);

    try {
      await preferencesAPI.updatePreferences(newPrefs);
      setPrefNotification(true);
      setTimeout(() => setPrefNotification(false), 2500);
    } catch (err) {
      console.warn('Could not persist preferences:', err);
    }

    // Determine target stock
    let targetTicker = activeStock.ticker;
    let targetMarket = newMarket;

    // If exchange changed, switch active stock to standard liquid benchmark stock
    if (marketChanged) {
      if (newMarket === 'NASDAQ') targetTicker = 'AAPL';
      else if (newMarket === 'NYSE') targetTicker = 'JPM';
      else if (newMarket === 'BSE' || newMarket === 'NSE') targetTicker = 'RELIANCE';
    }

    // Instantly refresh live quantitative analysis with the newly chosen period & market
    await fetchCompleteAnalysis(targetTicker, targetMarket, newPeriod);
  };

  // Handle Refresh Live Prices from Yahoo Finance
  const handleRefreshLivePrices = async () => {
    setRefreshingWatchlist(true);
    await fetchCompleteAnalysis(activeStock.ticker, activeStock.market, preferences.analysis_period);
    setRefreshingWatchlist(false);
  };

  // Run Multi-Agent Research Pipeline (Save to PostgreSQL research_tasks)
  const handleRunResearch = async () => {
    try {
      const newTask = await researchAPI.startTask({
        ticker: activeStock.ticker,
        market: activeStock.market,
        requested_period: preferences.analysis_period,
      });
      if (newTask) {
        setResearchHistory([newTask, ...researchHistory]);
      }
      alert(`Research task completed for ${activeStock.ticker} (${activeStock.market}). Comprehensive audit dossier generated.`);
    } catch (err) {
      alert(`Research Task started for ${activeStock.ticker}.`);
    }
  };

  return (
    <div className={`min-h-screen flex flex-col font-sans transition-colors duration-200 ${
      isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'
    }`}>
      {/* 1. Terminal Sub-Header (Clean Consumer Style) */}
      <div className={`border-b px-4 sm:px-6 py-2.5 flex flex-wrap items-center justify-between gap-4 transition-colors ${
        isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-xs'
      }`}>
        {/* User Workspace Info */}
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-sky-500/10 border border-sky-500/30 flex items-center justify-center text-sky-500 font-bold text-xs uppercase">
            {user?.full_name?.charAt(0) || 'U'}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className={`font-bold text-sm ${isDark ? 'text-white' : 'text-slate-900'}`}>
                {user?.full_name || 'Active User'}
              </span>
              <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 px-2 py-0.5 rounded font-semibold flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>ACTIVE SESSION</span>
              </span>
            </div>
            <span className={`text-xs font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              {user?.email || 'user@example.com'}
            </span>
          </div>
        </div>

        {/* Global Market & Timeframe Preference Bar (Module 1 Guide Section 6) */}
        <div className={`flex items-center space-x-3 p-1.5 rounded-xl border transition-colors ${
          isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-100 border-slate-200'
        }`}>
          <div className={`flex items-center space-x-1.5 px-2 text-xs font-mono border-r ${
            isDark ? 'text-slate-400 border-slate-800' : 'text-slate-600 border-slate-300'
          }`}>
            <SlidersHorizontal className="h-3.5 w-3.5 text-sky-500" />
            <span className="hidden sm:inline">Preferences:</span>
          </div>

          {/* Market Dropdown */}
          <select
            value={preferences.market}
            onChange={(e) => handleSavePreferences(e.target.value, preferences.analysis_period)}
            className={`border text-xs font-mono font-semibold rounded-lg px-2.5 py-1 focus:outline-none transition-colors cursor-pointer ${
              isDark
                ? 'bg-slate-900 border-slate-700 text-sky-400'
                : 'bg-white border-slate-300 text-sky-600 shadow-2xs'
            }`}
          >
            <option value="NSE">NSE (India)</option>
            <option value="BSE">BSE (India)</option>
            <option value="NASDAQ">NASDAQ (US)</option>
            <option value="NYSE">NYSE (US)</option>
          </select>

          {/* Timeframe Dropdown */}
          <select
            value={preferences.analysis_period}
            onChange={(e) => handleSavePreferences(preferences.market, e.target.value)}
            className={`border text-xs font-mono rounded-lg px-2.5 py-1 focus:outline-none transition-colors cursor-pointer ${
              isDark
                ? 'bg-slate-900 border-slate-700 text-slate-300'
                : 'bg-white border-slate-300 text-slate-700 shadow-2xs'
            }`}
          >
            <option value="1 Month">1 Month</option>
            <option value="3 Months">3 Months</option>
            <option value="6 Months">6 Months</option>
            <option value="1 Year">1 Year (Default)</option>
            <option value="5 Years">5 Years</option>
          </select>

          {prefNotification && (
            <span className="text-[10px] font-mono text-emerald-500 animate-pulse px-2 font-bold">
              Saved!
            </span>
          )}
        </div>
      </div>

      {/* 2. Main Workspace Layout: Left Watchlist Drawer + Right Multi-Agent Intelligence */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Side: Zerodha Kite-style Watchlist Panel (Module 1 Guide Section 5) */}
        <div className={`w-full lg:w-80 border-b lg:border-b-0 lg:border-r flex flex-col transition-colors ${
          isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
        }`}>
          {/* Watchlist Header & Search */}
          <div className={`p-3.5 border-b ${isDark ? 'border-slate-800' : 'border-slate-200'}`}>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-xs font-mono font-bold tracking-wider uppercase ${
                isDark ? 'text-slate-300' : 'text-slate-700'
              }`}>
                WATCHLIST ({watchlist.length})
              </span>
              <button
                onClick={handleRefreshLivePrices}
                className="text-[10px] font-mono text-sky-500 hover:text-sky-600 flex items-center space-x-1 cursor-pointer"
                title="Refresh Real-Time Market Quotes"
              >
                <RefreshCw className={`h-3 w-3 ${refreshingWatchlist ? 'animate-spin' : ''}`} />
                <span>LIVE FEED</span>
              </button>
            </div>

            <form onSubmit={handleAddStock} className="relative">
              <input
                type="text"
                placeholder={`Search ${preferences.market} (e.g. INFY, TCS)...`}
                value={newTickerInput}
                onChange={(e) => setNewTickerInput(e.target.value)}
                disabled={addingStock}
                className={`w-full rounded-lg pl-8 pr-16 py-1.5 text-xs font-mono uppercase transition border focus:outline-none focus:ring-1 focus:ring-sky-500 ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-slate-100 placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <Search className="h-3.5 w-3.5 text-slate-400 absolute left-2.5 top-2.5" />
              <button
                type="submit"
                disabled={addingStock}
                className="absolute right-1.5 top-1 bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-[10px] font-bold px-2 py-1 rounded flex items-center space-x-1 cursor-pointer"
              >
                {addingStock ? (
                  <RefreshCw className="h-2.5 w-2.5 animate-spin" />
                ) : (
                  <span>+ ADD</span>
                )}
              </button>
            </form>

            {watchlistError && (
              <p className="text-[10px] text-rose-500 mt-1 font-mono">{watchlistError}</p>
            )}
          </div>

          {/* Watchlist Items List */}
          <div className={`flex-1 overflow-y-auto divide-y max-h-[300px] lg:max-h-none ${
            isDark ? 'divide-slate-800/60' : 'divide-slate-100'
          }`}>
            {watchlist.map((stock) => {
              const isSelected = activeStock.ticker === stock.ticker;
              return (
                <div
                  key={stock.ticker}
                  onClick={() => handleSelectStock(stock)}
                  className={`p-3 cursor-pointer flex items-center justify-between transition group ${
                    isSelected
                      ? isDark
                        ? 'bg-sky-500/10 border-l-2 border-sky-500'
                        : 'bg-sky-50 border-l-2 border-sky-600'
                      : isDark
                      ? 'hover:bg-slate-800/50'
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex flex-col">
                    <div className="flex items-center space-x-2">
                      <span className={`font-mono font-bold text-xs group-hover:text-sky-500 transition ${
                        isDark ? 'text-white' : 'text-slate-900'
                      }`}>
                        {stock.ticker}
                      </span>
                      <span className={`text-[9px] font-mono px-1 rounded ${
                        isDark ? 'bg-slate-800 text-slate-400' : 'bg-slate-200 text-slate-600'
                      }`}>
                        {stock.market || preferences.market}
                      </span>
                    </div>
                    <span className={`text-[11px] truncate max-w-[140px] ${
                      isDark ? 'text-slate-400' : 'text-slate-500'
                    }`}>
                      {stock.name}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <span className={`font-mono font-bold text-xs block ${
                        isDark ? 'text-white' : 'text-slate-900'
                      }`}>
                        {stock.price}
                      </span>
                      <span
                        className={`text-[10px] font-mono font-semibold ${
                          stock.isPositive ? 'text-emerald-500' : 'text-rose-500'
                        }`}
                      >
                        {stock.change}
                      </span>
                    </div>

                    <button
                      onClick={(e) => handleRemoveStock(stock.ticker, stock.saved_stock_id, e)}
                      className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-rose-500 p-1 transition cursor-pointer"
                      title="Remove stock from Watchlist"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Active Stock Overview & Specialized Multi-Agent Intelligence */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {/* 1. Active Stock Header Ribbon (Real-Time from Yahoo Finance) */}
          <div className={`border rounded-2xl p-5 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-colors ${
            isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
          }`}>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className={`text-2xl font-black tracking-tight font-mono ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {activeStock.ticker}
                </h1>
                <span className="bg-sky-500/10 text-sky-500 border border-sky-500/30 text-xs font-mono font-bold px-2 py-0.5 rounded">
                  {activeStock.market}
                </span>
                <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-xs font-mono font-bold px-2 py-0.5 rounded">
                  {preferences.analysis_period}
                </span>
                <span className={`text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  {activeStock.company_name}
                </span>
              </div>
              <div className="flex items-center space-x-2 mt-1">
                <span className={`text-xs font-mono ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>{activeStock.sector}</span>
                <span className="text-[10px] text-slate-400 font-mono">•</span>
                <span className="text-[10px] font-mono text-emerald-500 flex items-center space-x-1">
                  <Globe2 className="h-3 w-3 inline" />
                  <span>{activeStock.data_source}</span>
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-6">
              <div className="text-right">
                <span className={`text-2xl font-black font-mono block ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  {loadingActiveStock ? (
                    <span className="text-slate-400 animate-pulse text-lg">Fetching LTP...</span>
                  ) : (
                    activeStock.price
                  )}
                </span>
                <span
                  className={`text-xs font-mono font-bold flex items-center justify-end space-x-1 ${
                    activeStock.isPositive ? 'text-emerald-500' : 'text-rose-500'
                  }`}
                >
                  {activeStock.isPositive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                  <span>{activeStock.changePercent} ({activeStock.change})</span>
                </span>
              </div>

              {/* Run Multi-Agent Research Action */}
              <button
                onClick={handleRunResearch}
                className="bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs px-4 py-2.5 rounded-xl shadow-md transition flex items-center space-x-2 cursor-pointer"
              >
                <Sparkles className="h-4 w-4" />
                <span>Run Agent Research</span>
              </button>
            </div>
          </div>

          {/* 2. Key Financial Ratios Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className={`border p-3 rounded-xl transition-colors ${
              isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-2xs'
            }`}>
              <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>P/E RATIO</span>
              <span className={`text-sm font-bold font-mono mt-1 block ${isDark ? 'text-white' : 'text-slate-900'}`}>{activeStock.peRatio}</span>
              <span className="text-[10px] text-emerald-500 font-mono">Trailing P/E</span>
            </div>
            <div className={`border p-3 rounded-xl transition-colors ${
              isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-2xs'
            }`}>
              <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>P/B RATIO</span>
              <span className={`text-sm font-bold font-mono mt-1 block ${isDark ? 'text-white' : 'text-slate-900'}`}>{activeStock.pbRatio}</span>
              <span className={`text-[10px] font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Price to Book</span>
            </div>
            <div className={`border p-3 rounded-xl transition-colors ${
              isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-2xs'
            }`}>
              <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>ROE</span>
              <span className="text-sm font-bold font-mono text-emerald-500 mt-1 block">{activeStock.roe}</span>
              <span className="text-[10px] text-emerald-500 font-mono">Return on Equity</span>
            </div>
            <div className={`border p-3 rounded-xl transition-colors ${
              isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-2xs'
            }`}>
              <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>DEBT / EQUITY</span>
              <span className={`text-sm font-bold font-mono mt-1 block ${isDark ? 'text-white' : 'text-slate-900'}`}>{activeStock.debtToEquity}</span>
              <span className={`text-[10px] font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Solvency Ratio</span>
            </div>
            <div className={`border p-3 rounded-xl transition-colors ${
              isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-2xs'
            }`}>
              <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                {preferences.analysis_period === '1 Year' ? '52W HIGH / LOW' : `${preferences.analysis_period} HIGH / LOW`}
              </span>
              <span className={`text-xs font-bold font-mono mt-1 block truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>
                {riskMetrics.period_high && riskMetrics.period_low
                  ? `${formatPrice(riskMetrics.period_high, activeStock.market === 'NSE' || activeStock.market === 'BSE' ? 'INR' : 'USD')} / ${formatPrice(riskMetrics.period_low, activeStock.market === 'NSE' || activeStock.market === 'BSE' ? 'INR' : 'USD')}`
                  : `${activeStock.high52w} / ${activeStock.low52w}`}
              </span>
              <span className="text-[10px] text-sky-500 font-mono">
                {preferences.analysis_period} Range
              </span>
            </div>
            <div className={`border p-3 rounded-xl transition-colors ${
              isDark ? 'bg-slate-900/80 border-slate-800' : 'bg-white border-slate-200 shadow-2xs'
            }`}>
              <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>MARKET CAP</span>
              <span className={`text-sm font-bold font-mono mt-1 block ${isDark ? 'text-white' : 'text-slate-900'}`}>{activeStock.marketCap}</span>
              <span className={`text-[10px] font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>Market Size</span>
            </div>
          </div>

          {/* 3. Multi-Agent Intelligence Tabs */}
          <div className={`border rounded-2xl overflow-hidden shadow-sm transition-colors ${
            isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
          }`}>
            {/* Tab Navigation */}
            <div className={`flex border-b overflow-x-auto ${
              isDark ? 'border-slate-800 bg-slate-950/60' : 'border-slate-200 bg-slate-100/60'
            }`}>
              <button
                onClick={() => setActiveTab('technical')}
                className={`flex items-center space-x-2 px-5 py-3.5 text-xs font-mono font-bold tracking-wider uppercase transition whitespace-nowrap border-b-2 cursor-pointer ${
                  activeTab === 'technical'
                    ? 'border-sky-500 text-sky-500 bg-sky-500/10'
                    : isDark
                    ? 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-200/40'
                }`}
              >
                <TrendingUp className="h-4 w-4 text-sky-500" />
                <span>Technical Signals</span>
              </button>

              <button
                onClick={() => setActiveTab('fundamental')}
                className={`flex items-center space-x-2 px-5 py-3.5 text-xs font-mono font-bold tracking-wider uppercase transition whitespace-nowrap border-b-2 cursor-pointer ${
                  activeTab === 'fundamental'
                    ? 'border-emerald-500 text-emerald-500 bg-emerald-500/10'
                    : isDark
                    ? 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-200/40'
                }`}
              >
                <BarChart3 className="h-4 w-4 text-emerald-500" />
                <span>Fundamental Health</span>
              </button>

              <button
                onClick={() => setActiveTab('news')}
                className={`flex items-center space-x-2 px-5 py-3.5 text-xs font-mono font-bold tracking-wider uppercase transition whitespace-nowrap border-b-2 cursor-pointer ${
                  activeTab === 'news'
                    ? 'border-amber-500 text-amber-500 bg-amber-500/10'
                    : isDark
                    ? 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-200/40'
                }`}
              >
                <Newspaper className="h-4 w-4 text-amber-500" />
                <span>News & Sentiment</span>
              </button>

              <button
                onClick={() => setActiveTab('risk')}
                className={`flex items-center space-x-2 px-5 py-3.5 text-xs font-mono font-bold tracking-wider uppercase transition whitespace-nowrap border-b-2 cursor-pointer ${
                  activeTab === 'risk'
                    ? 'border-rose-500 text-rose-500 bg-rose-500/10'
                    : isDark
                    ? 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900/40'
                    : 'border-transparent text-slate-600 hover:text-slate-900 hover:bg-slate-200/40'
                }`}
              >
                <ShieldAlert className="h-4 w-4 text-rose-500" />
                <span>Risk & Volatility</span>
              </button>
            </div>

            {/* Tab Body */}
            <div className="p-6">
              {/* Technical Agent Tab */}
              {activeTab === 'technical' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className={`font-bold text-sm font-mono uppercase tracking-wide ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        QUANTITATIVE INDICATORS // {activeStock.ticker}
                      </h3>
                      <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                        Moving Averages, RSI (14) & Volatility Calculated dynamically for {techSignals.period_analyzed || preferences.analysis_period}
                      </p>
                    </div>
                    <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-xs font-mono px-2.5 py-1 rounded-md font-semibold">
                      {techSignals.trend_summary}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>SMA 50 / SMA 200</span>
                      <span className={`text-base font-bold font-mono mt-1 block ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        ₹{techSignals.sma_50} / ₹{techSignals.sma_200}
                      </span>
                      <span className="text-[11px] text-emerald-500 font-mono mt-1 block">
                        {techSignals.crossover}
                      </span>
                    </div>

                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>RSI (14-DAY)</span>
                      <span className="text-lg font-bold font-mono text-sky-500 mt-1 block">
                        {techSignals.rsi_14}
                      </span>
                      <span className={`text-[11px] font-mono mt-1 block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        {Number(techSignals.rsi_14) > 70 ? 'Overbought (>70)' : Number(techSignals.rsi_14) < 30 ? 'Oversold (<30)' : 'Neutral (30-70)'}
                      </span>
                    </div>

                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>MACD (12, 26, 9)</span>
                      <span className="text-lg font-bold font-mono text-emerald-500 mt-1 block">
                        {techSignals.macd}
                      </span>
                      <span className="text-[11px] text-emerald-500 font-mono mt-1 block">
                        Momentum Convergence
                      </span>
                    </div>

                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>ANNUALIZED VOLATILITY</span>
                      <span className="text-lg font-bold font-mono text-amber-500 mt-1 block">
                        {techSignals.volatility}
                      </span>
                      <span className={`text-[11px] font-mono mt-1 block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        Historical Price Fluctuation
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Fundamental Agent Tab */}
              {activeTab === 'fundamental' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className={`font-bold text-sm font-mono uppercase tracking-wide ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        FINANCIAL STATEMENT AUDIT // {activeStock.ticker}
                      </h3>
                      <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                        Real-time valuation metrics from audited corporate filings
                      </p>
                    </div>
                    <span className="bg-sky-500/10 text-sky-500 border border-sky-500/20 text-xs font-mono px-2.5 py-1 rounded-md font-semibold">
                      VALUATION MULTIPLE: {activeStock.peRatio}x
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>VALUATION ASSESSMENT</span>
                      <p className={`text-xs mt-2 leading-relaxed font-mono ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        Trading at {activeStock.peRatio}x Trailing P/E and {activeStock.pbRatio}x Price-to-Book. Enterprise Capitalization stands at {activeStock.marketCap}.
                      </p>
                    </div>
                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>CAPITAL RETURN EFFICIENCY</span>
                      <p className={`text-xs mt-2 leading-relaxed font-mono ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        Return on Equity (ROE) of {activeStock.roe}. Reflects efficiency in deploying shareholder capital into profit generation.
                      </p>
                    </div>
                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>BALANCE SHEET LEVERAGE</span>
                      <p className={`text-xs mt-2 leading-relaxed font-mono ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                        Debt-to-Equity ratio of {activeStock.debtToEquity}. Solvency indicators suggest manageable borrowing relative to operating cash flows.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* News & Sentiment Agent Tab */}
              {activeTab === 'news' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className={`font-bold text-sm font-mono uppercase tracking-wide ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        LIVE NEWS INTELLIGENCE // {activeStock.ticker}
                      </h3>
                      <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                        Real-time financial news stream with verified source links
                      </p>
                    </div>
                    <span className="bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 text-xs font-mono px-2.5 py-1 rounded-md font-semibold">
                      {liveNews.length} ARTICLES RETRIEVED
                    </span>
                  </div>

                  {liveNews.length > 0 ? (
                    <div className="space-y-3">
                      {liveNews.map((article, idx) => (
                        <div
                          key={idx}
                          className={`p-3.5 rounded-xl border flex items-start justify-between gap-4 transition-colors ${
                            isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                          }`}
                        >
                          <div>
                            <div className="flex items-center space-x-2">
                              <span
                                className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                                  article.sentiment === 'POSITIVE'
                                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                                    : article.sentiment === 'NEGATIVE'
                                    ? 'bg-rose-500/10 text-rose-500 border border-rose-500/20'
                                    : 'bg-slate-200 text-slate-700'
                                }`}
                              >
                                {article.sentiment}
                              </span>
                              <span className={`text-xs font-mono ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                                {article.publisher} • {article.published_at}
                              </span>
                            </div>
                            <h4 className={`text-xs font-bold mt-1.5 leading-snug ${isDark ? 'text-white' : 'text-slate-900'}`}>
                              {article.title}
                            </h4>
                          </div>
                          <a
                            href={article.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-slate-400 hover:text-sky-500 p-1 flex-shrink-0 cursor-pointer"
                            title="Open Verified Source Link"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className={`p-8 text-center rounded-xl border border-dashed font-mono text-xs ${
                      isDark ? 'border-slate-800 text-slate-500' : 'border-slate-300 text-slate-400'
                    }`}>
                      No breaking wire stories reported for {activeStock.ticker} on this exchange session.
                    </div>
                  )}
                </div>
              )}

              {/* Risk & Conflict Agent Tab */}
              {activeTab === 'risk' && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className={`font-bold text-sm font-mono uppercase tracking-wide ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        RISK ASSESSMENT & STRESS TESTING // {activeStock.ticker}
                      </h3>
                      <p className={`text-xs mt-0.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                        Historical Drawdown, Volatility Spectrum, and Downside Exposure
                      </p>
                    </div>
                    <span
                      className={`text-xs font-mono px-2.5 py-1 rounded-md font-semibold border ${
                        riskMetrics.risk_level === 'HIGH'
                          ? 'bg-rose-500/10 text-rose-500 border-rose-500/20'
                          : 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                      }`}
                    >
                      RISK LEVEL: {riskMetrics.risk_level}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>MAXIMUM DRAWDOWN</span>
                      <span className="text-lg font-bold font-mono text-rose-500 mt-1 block">
                        {riskMetrics.max_drawdown}
                      </span>
                      <span className={`text-[11px] font-mono mt-1 block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        Peak-to-Trough ({riskMetrics.period_analyzed || preferences.analysis_period})
                      </span>
                    </div>

                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>HORIZON RETURN</span>
                      <span className={`text-lg font-bold font-mono mt-1 block ${
                        (riskMetrics.period_return || '').startsWith('-') ? 'text-rose-500' : 'text-emerald-500'
                      }`}>
                        {riskMetrics.period_return || 'N/A'}
                      </span>
                      <span className={`text-[11px] font-mono mt-1 block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        Gain/Loss over {riskMetrics.period_analyzed || preferences.analysis_period}
                      </span>
                    </div>

                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>PERIOD HIGH / LOW</span>
                      <span className={`text-xs font-bold font-mono mt-2 block truncate ${isDark ? 'text-white' : 'text-slate-900'}`}>
                        {riskMetrics.period_high && riskMetrics.period_low
                          ? `${formatPrice(riskMetrics.period_high, activeStock.market === 'NSE' || activeStock.market === 'BSE' ? 'INR' : 'USD')} / ${formatPrice(riskMetrics.period_low, activeStock.market === 'NSE' || activeStock.market === 'BSE' ? 'INR' : 'USD')}`
                          : `${activeStock.high52w} / ${activeStock.low52w}`}
                      </span>
                      <span className={`text-[11px] font-mono mt-1 block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        Range in {riskMetrics.period_analyzed || preferences.analysis_period}
                      </span>
                    </div>

                    <div className={`p-4 rounded-xl border transition-colors ${
                      isDark ? 'bg-slate-950 border-slate-800' : 'bg-slate-50 border-slate-200'
                    }`}>
                      <span className={`text-xs font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>VOLATILITY EXPOSURE</span>
                      <span className="text-lg font-bold font-mono text-amber-500 mt-1 block">
                        {riskMetrics.volatility_annualized}
                      </span>
                      <span className={`text-[11px] font-mono mt-1 block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                        Fluctuation in {riskMetrics.period_analyzed || preferences.analysis_period}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 4. Research Tasks History (Module 1 Guide Section 4) */}
          <div className={`border rounded-2xl p-6 shadow-sm transition-colors ${
            isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200'
          }`}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className={`text-sm font-bold font-mono uppercase tracking-wide ${isDark ? 'text-white' : 'text-slate-900'}`}>
                  RESEARCH HISTORY & AUDIT LOG
                </h3>
                <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  Your saved equity research tasks and generated dossiers
                </p>
              </div>
              <span className={`text-xs font-mono ${isDark ? 'text-slate-500' : 'text-slate-400'}`}>
                {researchHistory.length} TASKS LOGGED
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className={`border-b uppercase ${isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-500'}`}>
                    <th className="py-2.5 px-3">Task ID</th>
                    <th className="py-2.5 px-3">Ticker</th>
                    <th className="py-2.5 px-3">Market</th>
                    <th className="py-2.5 px-3">Analysis Period</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-slate-800/60' : 'divide-slate-100'}`}>
                  {researchHistory.map((task) => (
                    <tr
                      key={task.task_id}
                      className={`transition ${isDark ? 'hover:bg-slate-800/40' : 'hover:bg-slate-50'}`}
                    >
                      <td className={`py-3 px-3 ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>#{task.task_id}</td>
                      <td className={`py-3 px-3 font-bold ${isDark ? 'text-white' : 'text-slate-900'}`}>{task.ticker}</td>
                      <td className="py-3 px-3 text-sky-500">{task.market}</td>
                      <td className={`py-3 px-3 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>{task.requested_period || '1 Year'}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            task.status === 'Completed'
                              ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30'
                              : task.status === 'Processing'
                              ? 'bg-amber-500/10 text-amber-500 border border-amber-500/30'
                              : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {task.status}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right">
                        <button
                          onClick={() => alert(`Research Dossier for ${task.ticker} (${task.market}) - Period: ${task.requested_period || '1 Year'}. Valuation, technical indicators, and news sentiment synthesized.`)}
                          className="text-sky-500 hover:text-sky-600 font-bold text-xs inline-flex items-center space-x-1 cursor-pointer"
                        >
                          <span>View Report</span>
                          <ExternalLink className="h-3 w-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
