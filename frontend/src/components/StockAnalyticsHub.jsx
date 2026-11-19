import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  Database,
  Download,
  Building2,
  FileSpreadsheet,
  BarChart3,
  ExternalLink,
  AlertTriangle,
  X,
  Sparkles,
  Plus,
  RefreshCw,
  Loader2
} from 'lucide-react';
import { stockService } from '../services/api';

export const StockAnalyticsHub = ({
  ticker,
  initialPeriod = '1y',
  onClose,
  onAddToWatchlist,
  onOpenResearch,
}) => {
  const [activeTab, setActiveTab] = useState('charts'); // 'charts' | 'ohlcv' | 'profile' | 'financials'
  const [financialSubTab, setFinancialSubTab] = useState('income'); // 'income' | 'balance' | 'cashflow'
  const [period, setPeriod] = useState(initialPeriod || '1y');
  
  // Data states
  const [historicalData, setHistoricalData] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [financialsData, setFinancialsData] = useState(null);

  // Loading and error states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [usdModalDismissed, setUsdModalDismissed] = useState(false);

  // Fetch Historical + TSA
  const fetchHistorical = async (targetTicker, targetPeriod) => {
    try {
      setLoading(true);
      setError(null);
      const data = await stockService.getHistorical(targetTicker, targetPeriod);
      setHistoricalData(data);
    } catch (err) {
      console.error('Error fetching historical stock data:', err);
      setError(err?.response?.data?.detail || 'Failed to retrieve historical stock data from yfinance.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch Profile & Financials asynchronously
  const fetchSupplementary = async (targetTicker) => {
    try {
      const [prof, fin] = await Promise.allSettled([
        stockService.getProfile(targetTicker),
        stockService.getFinancials(targetTicker),
      ]);
      if (prof.status === 'fulfilled') setProfileData(prof.value);
      if (fin.status === 'fulfilled') setFinancialsData(fin.value);
    } catch (e) {
      console.warn('Error fetching supplementary profile or financials:', e);
    }
  };

  useEffect(() => {
    if (ticker) {
      setUsdModalDismissed(false);
      fetchHistorical(ticker, period);
      fetchSupplementary(ticker);
    }
  }, [ticker, period]);

  // Export OHLCV as CSV
  const handleExportCSV = () => {
    if (!historicalData || !historicalData.ohlcv) return;
    const headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Daily Change %'];
    const rows = historicalData.ohlcv.map((r) => [
      r.date,
      r.open,
      r.high,
      r.low,
      r.close,
      r.volume,
      r.change_percent != null ? `${r.change_percent}%` : 'N/A',
    ]);
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${historicalData.ticker}_OHLCV_${historicalData.period}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!ticker) return null;

  const currencySymbol = historicalData?.currency_symbol || '₹';
  const tsa = historicalData?.time_series_analysis || {};
  const histogram = tsa?.histogram || [];
  const priceSeries = tsa?.price_series || [];

  // =========================================================================
  // Pure SVG Price Chart Generation
  // =========================================================================
  const renderPriceChart = () => {
    if (!priceSeries || priceSeries.length < 2) {
      return (
        <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
          Insufficient data points to render price chart
        </div>
      );
    }

    const width = 640;
    const height = 240;
    const padding = { top: 20, right: 20, bottom: 30, left: 55 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const allPrices = priceSeries.map((p) => p.close);
    const minP = Math.min(...allPrices);
    const maxP = Math.max(...allPrices);
    const priceRange = maxP - minP || 1;

    const getX = (i) => padding.left + (i / (priceSeries.length - 1)) * chartW;
    const getY = (val) => padding.top + chartH - ((val - minP) / priceRange) * chartH;

    // Price line path
    const pricePath = priceSeries
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(p.close).toFixed(1)}`)
      .join(' ');

    // SMA 20 path
    const sma20Path = priceSeries
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(p.sma_20).toFixed(1)}`)
      .join(' ');

    // SMA 50 path
    const sma50Path = priceSeries
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(p.sma_50).toFixed(1)}`)
      .join(' ');

    // Gradient fill area
    const areaPath = `${pricePath} L ${padding.left + chartW} ${padding.top + chartH} L ${padding.left} ${padding.top + chartH} Z`;

    // 4 horizontal gridlines
    const gridY = [0, 0.33, 0.66, 1].map((pct) => {
      const val = minP + pct * priceRange;
      const y = padding.top + chartH - pct * chartH;
      return { val, y };
    });

    return (
      <div className="w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none">
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00d084" stopOpacity="0.28" />
              <stop offset="100%" stopColor="#00d084" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines & Y-axis labels */}
          {gridY.map((g, idx) => (
            <g key={idx}>
              <line
                x1={padding.left}
                y1={g.y}
                x2={padding.left + chartW}
                y2={g.y}
                stroke="#1c2533"
                strokeDasharray="4 4"
              />
              <text
                x={padding.left - 8}
                y={g.y + 4}
                textAnchor="end"
                className="text-[10px] fill-slate-400 font-mono"
              >
                {currencySymbol}
                {g.val >= 1000 ? g.val.toFixed(0) : g.val.toFixed(1)}
              </text>
            </g>
          ))}

          {/* Price area fill */}
          <path d={areaPath} fill="url(#priceGradient)" />

          {/* Lines */}
          <path d={sma50Path} fill="none" stroke="#f59e0b" strokeWidth="1.75" strokeDasharray="3 3" opacity="0.85" />
          <path d={sma20Path} fill="none" stroke="#06b6d4" strokeWidth="1.75" opacity="0.85" />
          <path d={pricePath} fill="none" stroke="#00d084" strokeWidth="2.5" />

          {/* Start and End date labels */}
          <text
            x={padding.left}
            y={height - 8}
            className="text-[10px] fill-slate-400 font-mono"
          >
            {priceSeries[0].date}
          </text>
          <text
            x={padding.left + chartW}
            y={height - 8}
            textAnchor="end"
            className="text-[10px] fill-slate-400 font-mono"
          >
            {priceSeries[priceSeries.length - 1].date}
          </text>
        </svg>

        {/* Chart Legend */}
        <div className="flex items-center justify-center gap-5 mt-2 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-[#00d084] rounded-full inline-block" />
            <span className="text-slate-300">Close Price</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-[#06b6d4] rounded-full inline-block" />
            <span className="text-slate-300">20-Day SMA</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1 bg-[#f59e0b] border-dashed rounded-full inline-block" />
            <span className="text-slate-300">50-Day SMA</span>
          </div>
        </div>
      </div>
    );
  };

  // =========================================================================
  // Pure SVG Price Distribution Histogram Generation
  // =========================================================================
  const renderHistogram = () => {
    if (!histogram || histogram.length === 0) {
      return (
        <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
          Insufficient data points to generate frequency distribution
        </div>
      );
    }

    const width = 480;
    const height = 240;
    const padding = { top: 20, right: 15, bottom: 40, left: 45 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;

    const maxPct = Math.max(...histogram.map((b) => b.frequency_percent), 1);
    const barWidth = (chartW / histogram.length) * 0.78;
    const barSpacing = chartW / histogram.length;

    return (
      <div className="w-full overflow-hidden">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto select-none">
          {/* Y-axis gridlines */}
          {[0, 0.5, 1].map((pct, idx) => {
            const y = padding.top + chartH - pct * chartH;
            return (
              <g key={idx}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + chartW}
                  y2={y}
                  stroke="#1c2533"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 6}
                  y={y + 3}
                  textAnchor="end"
                  className="text-[10px] fill-slate-400 font-mono"
                >
                  {(pct * maxPct).toFixed(0)}%
                </text>
              </g>
            );
          })}

          {/* Histogram Bars */}
          {histogram.map((b, i) => {
            const barH = (b.frequency_percent / maxPct) * chartH;
            const x = padding.left + i * barSpacing + (barSpacing - barWidth) / 2;
            const y = padding.top + chartH - barH;
            const fillColor =
              b.tone === 'green' ? '#00d084' : b.tone === 'red' ? '#ef4444' : '#64748b';

            return (
              <g key={i} className="group">
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barH}
                  fill={fillColor}
                  opacity="0.85"
                  rx="3"
                  className="transition-all hover:opacity-100"
                />
                <text
                  x={x + barWidth / 2}
                  y={height - 22}
                  textAnchor="middle"
                  className="text-[9px] fill-slate-400 font-mono"
                >
                  {b.min_return >= 0 ? `+${b.min_return}%` : `${b.min_return}%`}
                </text>
                {b.count > 0 && (
                  <text
                    x={x + barWidth / 2}
                    y={y - 4}
                    textAnchor="middle"
                    className="text-[9px] fill-slate-300 font-bold font-mono"
                  >
                    {b.count}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        <div className="flex items-center justify-between text-[11px] text-slate-400 px-3 mt-1">
          <span className="text-red-400">← Negative Returns (Drawdown)</span>
          <span className="font-medium text-slate-300">Daily Return Distribution (%)</span>
          <span className="text-emerald-400">Positive Returns (Gains) →</span>
        </div>
      </div>
    );
  };

  return (
    <section className="bg-[#0b0f15] border border-emerald-500/30 rounded-3xl p-5 sm:p-7 shadow-2xl shadow-black/80 relative space-y-6">
      {/* US Market Currency Notice Modal in Analytics Hub */}
      {historicalData?.is_us_market && !usdModalDismissed && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-sm bg-[#0b0f15] border border-amber-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white mb-1">US Dollar Currency Notice</h3>
                <p className="text-xs text-amber-300 font-medium">
                  {historicalData.company_name || historicalData.ticker} ({historicalData.exchange || 'US Market'})
                </p>
              </div>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              This asset is traded on a US exchange. All price charts, 20/50-day moving averages (SMA), OHLCV data, and financial statements in this Analytics Hub are quoted in <strong className="text-white">US Dollars ($ USD)</strong>.
            </p>
            <div className="p-2.5 rounded-xl bg-amber-950/30 border border-amber-500/20 text-[11px] text-amber-300/90">
              💡 Returns and price performance will be affected by USD/INR foreign exchange rate movements.
            </div>
            <div className="flex justify-end pt-1">
              <button
                type="button"
                onClick={() => setUsdModalDismissed(true)}
                className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md transition-all"
              >
                Understood (Proceed in USD $)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Top Banner: Module 2 Identification + Ticker Header + Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#1c2533]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wider uppercase bg-emerald-500/10 text-[#00d084] border border-emerald-500/30">
              Market Analytics & Financial Intelligence
            </span>
            {historicalData?.is_us_market && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                US Market ($ USD)
              </span>
            )}
          </div>

          <div className="flex items-baseline gap-3 flex-wrap">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {historicalData?.ticker || ticker}
            </h2>
            <span className="text-base text-slate-400 font-medium">
              {historicalData?.company_name}
            </span>
            <span className="px-2 py-0.5 rounded-md text-xs font-semibold bg-[#121924] border border-[#1e293b] text-slate-300">
              {historicalData?.exchange || 'Market Exchange'}
            </span>
            {tsa.current_price && (
              <span className="text-xl sm:text-2xl font-bold text-white font-mono ml-auto lg:ml-0">
                {currencySymbol}
                {tsa.current_price.toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          {onAddToWatchlist && (
            <button
              onClick={() => onAddToWatchlist(historicalData?.ticker || ticker)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#121924] hover:bg-[#1a2332] text-slate-200 border border-[#1e293b] transition-all"
            >
              <Plus className="w-3.5 h-3.5 text-emerald-400" />
              <span>Watchlist</span>
            </button>
          )}

          {onOpenResearch && (
            <button
              onClick={() =>
                onOpenResearch(
                  historicalData?.ticker || ticker,
                  historicalData?.company_name || ticker,
                  historicalData?.market || 'NSE'
                )
              }
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>AI Research</span>
            </button>
          )}

          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/50 border border-transparent hover:border-[#1e293b] transition-all"
              title="Close Analytics Hub"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>

      {/* Data Source & Timestamp Strip */}
      <div className="flex items-center justify-between p-2.5 px-4 rounded-2xl bg-[#0e141d] border border-[#1c2533] text-xs">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-400">Data Source:</span>
          <span className="font-semibold text-white">yfinance API</span>
        </div>
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-400">
          <Clock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Retrieved: {historicalData?.retrieved_at || 'Live Feed'}</span>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 border-b border-[#1c2533] pb-2 overflow-x-auto">
        <button
          onClick={() => setActiveTab('charts')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'charts'
              ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>Price & TSA Charts</span>
        </button>

        <button
          onClick={() => setActiveTab('ohlcv')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'ohlcv'
              ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          <span>OHLCV Table</span>
        </button>

        <button
          onClick={() => setActiveTab('profile')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'profile'
              ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Company Profile</span>
        </button>

        <button
          onClick={() => setActiveTab('financials')}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all shrink-0 ${
            activeTab === 'financials'
              ? 'bg-emerald-500 text-black shadow-lg shadow-emerald-500/20'
              : 'text-slate-400 hover:text-white hover:bg-slate-800/40'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Financial Statements</span>
        </button>
      </div>

      {/* Loading or Error Banners */}
      {loading && (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
          <p className="text-sm font-medium text-slate-400">
            Fetching market data & computing time series analysis from yfinance...
          </p>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-2xl bg-red-950/30 border border-red-500/40 text-red-300 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 1: PRICE CHARTS & TIME SERIES ANALYSIS (TSA)                    */}
      {/* =================================================================== */}
      {!loading && !error && activeTab === 'charts' && (
        <div className="space-y-6">
          {/* Horizon Period Selector */}
          <div className="flex items-center justify-between flex-wrap gap-3">
            <span className="text-xs font-semibold text-slate-300">
              Historical Range:
            </span>
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#070b10] border border-[#1c2533]">
              {['1mo', '3mo', '6mo', '1y', '5y'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold uppercase transition-all ${
                    period === p
                      ? 'bg-emerald-500 text-black'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* 4 Time Series Analysis (TSA) Metric Badges */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="p-4 rounded-2xl bg-[#0e141d] border border-[#1c2533] space-y-1">
              <span className="text-[11px] font-medium text-slate-400">20-Day SMA</span>
              <div className="text-lg font-bold text-cyan-400 font-mono">
                {currencySymbol}
                {tsa.sma_20 ? tsa.sma_20.toLocaleString() : 'N/A'}
              </div>
              <p className="text-[10px] text-slate-500">Short-term trend momentum</p>
            </div>

            <div className="p-4 rounded-2xl bg-[#0e141d] border border-[#1c2533] space-y-1">
              <span className="text-[11px] font-medium text-slate-400">50-Day SMA</span>
              <div className="text-lg font-bold text-amber-400 font-mono">
                {currencySymbol}
                {tsa.sma_50 ? tsa.sma_50.toLocaleString() : 'N/A'}
              </div>
              <p className="text-[10px] text-slate-500">Medium-term baseline support</p>
            </div>

            <div className="p-4 rounded-2xl bg-[#0e141d] border border-[#1c2533] space-y-1">
              <span className="text-[11px] font-medium text-slate-400">Annualized Volatility</span>
              <div className="text-lg font-bold text-white font-mono">
                {tsa.volatility_annualized_percent != null
                  ? `${tsa.volatility_annualized_percent}%`
                  : 'N/A'}
              </div>
              <p className="text-[10px] text-slate-500">
                Daily: {tsa.volatility_daily_percent ?? 0}%
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-[#0e141d] border border-[#1c2533] space-y-1">
              <span className="text-[11px] font-medium text-slate-400">Trend Direction</span>
              <div className="flex items-center gap-1.5">
                {tsa.trend === 'Bullish' ? (
                  <TrendingUp className="w-4 h-4 text-[#00d084]" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-400" />
                )}
                <span
                  className={`text-lg font-bold ${
                    tsa.trend === 'Bullish'
                      ? 'text-[#00d084]'
                      : tsa.trend === 'Bearish'
                      ? 'text-red-400'
                      : 'text-amber-400'
                  }`}
                >
                  {tsa.trend || 'Neutral'}
                </span>
              </div>
              <p className="text-[10px] text-slate-400 truncate" title={tsa.trend_signal}>
                {tsa.trend_signal}
              </p>
            </div>
          </div>

          {/* Dual Visual Analytics Cards: Price Chart & Histogram */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            {/* Left Column: Historical Price & Moving Averages (~62%) */}
            <div className="lg:col-span-7 p-4 sm:p-5 rounded-2xl bg-[#070b10] border border-[#1c2533] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Historical Stock Prices & Moving Averages
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Close Price, 20-Day SMA, and 50-Day SMA across {period.toUpperCase()}
                  </p>
                </div>
              </div>
              {renderPriceChart()}
            </div>

            {/* Right Column: Price Return Distribution Histogram (~38%) */}
            <div className="lg:col-span-5 p-4 sm:p-5 rounded-2xl bg-[#070b10] border border-[#1c2533] space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Daily Return Distribution Histogram
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    Frequency density of daily percentage price changes
                  </p>
                </div>
              </div>
              {renderHistogram()}
            </div>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: OHLCV TABULAR VIEW                                           */}
      {/* =================================================================== */}
      {!loading && !error && activeTab === 'ohlcv' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-sm font-bold text-white">
                Historical OHLCV Records ({historicalData?.ohlcv?.length || 0} Trading Days)
              </h3>
              <p className="text-xs text-slate-400">
                Detailed Open, High, Low, Close, and Volume dataset collected from yfinance
              </p>
            </div>
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#121924] hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export CSV</span>
            </button>
          </div>

          <div className="rounded-2xl border border-[#1c2533] overflow-hidden">
            <div className="max-h-96 overflow-y-auto overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0e141d] text-slate-400 uppercase tracking-wider sticky top-0 z-10 border-b border-[#1c2533]">
                  <tr>
                    <th className="py-2.5 px-3">Date</th>
                    <th className="py-2.5 px-3">Open ({currencySymbol})</th>
                    <th className="py-2.5 px-3">High ({currencySymbol})</th>
                    <th className="py-2.5 px-3">Low ({currencySymbol})</th>
                    <th className="py-2.5 px-3">Close ({currencySymbol})</th>
                    <th className="py-2.5 px-3">Volume</th>
                    <th className="py-2.5 px-3 text-right">Daily Change</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#18212e] text-slate-300">
                  {historicalData?.ohlcv?.map((row, i) => (
                    <tr key={i} className="hover:bg-[#121924]/60 transition-colors">
                      <td className="py-2 px-3 font-semibold text-white">{row.date}</td>
                      <td className="py-2 px-3">{row.open.toLocaleString()}</td>
                      <td className="py-2 px-3 text-emerald-400">{row.high.toLocaleString()}</td>
                      <td className="py-2 px-3 text-red-400">{row.low.toLocaleString()}</td>
                      <td className="py-2 px-3 font-bold text-white">{row.close.toLocaleString()}</td>
                      <td className="py-2 px-3 text-slate-400">{row.volume.toLocaleString()}</td>
                      <td
                        className={`py-2 px-3 text-right font-bold ${
                          row.change_percent == null
                            ? 'text-slate-500'
                            : row.change_percent >= 0
                            ? 'text-emerald-400'
                            : 'text-red-400'
                        }`}
                      >
                        {row.change_percent != null
                          ? `${row.change_percent >= 0 ? '+' : ''}${row.change_percent}%`
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 3: COMPANY PROFILE & VALUATION RATIOS                           */}
      {/* =================================================================== */}
      {!loading && !error && activeTab === 'profile' && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="p-3 rounded-2xl bg-[#0e141d] border border-[#1c2533]">
              <span className="text-slate-400 text-[11px] block">Sector</span>
              <span className="font-bold text-white text-xs truncate block">
                {profileData?.sector || 'N/A'}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0e141d] border border-[#1c2533]">
              <span className="text-slate-400 text-[11px] block">Industry</span>
              <span className="font-bold text-white text-xs truncate block">
                {profileData?.industry || 'N/A'}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0e141d] border border-[#1c2533]">
              <span className="text-slate-400 text-[11px] block">Market Cap</span>
              <span className="font-bold text-[#00d084] text-xs font-mono block">
                {profileData?.market_cap_formatted || 'N/A'}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0e141d] border border-[#1c2533]">
              <span className="text-slate-400 text-[11px] block">Trailing P/E</span>
              <span className="font-bold text-white text-xs font-mono block">
                {profileData?.trailing_pe ?? 'N/A'}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0e141d] border border-[#1c2533]">
              <span className="text-slate-400 text-[11px] block">Beta</span>
              <span className="font-bold text-cyan-400 text-xs font-mono block">
                {profileData?.beta ?? 'N/A'}
              </span>
            </div>
            <div className="p-3 rounded-2xl bg-[#0e141d] border border-[#1c2533]">
              <span className="text-slate-400 text-[11px] block">52-Week Range</span>
              <span className="font-bold text-white text-[11px] font-mono block truncate">
                {profileData?.fifty_two_week_low != null && profileData?.fifty_two_week_high != null
                  ? `${currencySymbol}${profileData.fifty_two_week_low} - ${currencySymbol}${profileData.fifty_two_week_high}`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Business Summary */}
          <div className="p-4 sm:p-5 rounded-2xl bg-[#070b10] border border-[#1c2533] space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white">Business Overview</h3>
              {profileData?.website && (
                <a
                  href={profileData.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300"
                >
                  <span>Official Website</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
            <p className="text-xs text-slate-300 leading-relaxed max-w-4xl">
              {profileData?.summary}
            </p>
          </div>

          {/* Key Executives */}
          {profileData?.executives && profileData.executives.length > 0 && (
            <div className="p-4 rounded-2xl bg-[#070b10] border border-[#1c2533] space-y-2">
              <h3 className="text-sm font-bold text-white">Key Corporate Officers</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 text-xs">
                {profileData.executives.map((exec, idx) => (
                  <div key={idx} className="p-2.5 rounded-xl bg-[#0e141d] border border-[#1c2533]">
                    <span className="font-bold text-white block">{exec.name}</span>
                    <span className="text-[11px] text-slate-400 block">{exec.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 4: FINANCIAL STATEMENTS                                         */}
      {/* =================================================================== */}
      {!loading && !error && activeTab === 'financials' && (
        <div className="space-y-4">
          {/* Sub-tab selection */}
          <div className="flex items-center gap-2">
            {[
              { id: 'income', label: 'Income Statement' },
              { id: 'balance', label: 'Balance Sheet' },
              { id: 'cashflow', label: 'Cash Flow' },
            ].map((st) => (
              <button
                key={st.id}
                onClick={() => setFinancialSubTab(st.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  financialSubTab === st.id
                    ? 'bg-emerald-500/20 text-[#00d084] border border-emerald-500/40'
                    : 'text-slate-400 hover:text-white bg-[#0e141d] border border-[#1c2533]'
                }`}
              >
                {st.label}
              </button>
            ))}
          </div>

          {/* Statements Table */}
          <div className="rounded-2xl border border-[#1c2533] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0e141d] text-slate-400 uppercase tracking-wider border-b border-[#1c2533]">
                  <tr>
                    <th className="py-2.5 px-4">Financial Metric</th>
                    <th className="py-2.5 px-4 text-right">Reported Value ({currencySymbol})</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#18212e] text-slate-300">
                  {(() => {
                    const activeRecords =
                      financialSubTab === 'income'
                        ? financialsData?.income_statement
                        : financialSubTab === 'balance'
                        ? financialsData?.balance_sheet
                        : financialsData?.cash_flow;

                    if (!activeRecords || activeRecords.length === 0) {
                      return (
                        <tr>
                          <td colSpan="2" className="py-6 text-center text-slate-500">
                            No reported statement figures available for this period.
                          </td>
                        </tr>
                      );
                    }

                    return activeRecords.map((item, idx) => {
                      // Find value column (either 'Latest' or the first date key)
                      const valKey = Object.keys(item).find((k) => k !== 'metric') || 'Latest';
                      const numVal = item[valKey];
                      return (
                        <tr key={idx} className="hover:bg-[#121924]/60 transition-colors">
                          <td className="py-2.5 px-4 font-semibold text-white">{item.metric}</td>
                          <td className="py-2.5 px-4 text-right font-bold text-emerald-400">
                            {numVal != null && !isNaN(numVal)
                              ? numVal >= 1e7
                                ? `${(numVal / 1e7).toLocaleString(undefined, { maximumFractionDigits: 2 })} Cr`
                                : numVal.toLocaleString(undefined, { maximumFractionDigits: 2 })
                              : '—'}
                          </td>
                        </tr>
                      );
                    });
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default StockAnalyticsHub;
