import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import {
  Search,
  Compass,
  Loader2,
  Bookmark,
  Play,
  BarChart3,
  PieChart,
  Activity,
  Database,
  Building2,
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import FundamentalPanel from '../components/analysis/FundamentalPanel';
import TechnicalPanel from '../components/analysis/TechnicalPanel';
import DataQualityPanel from '../components/analysis/DataQualityPanel';

export default function StockExplorerPage() {
  const { preferences, addToast } = useAuth();
  const { openResearchModal } = useOutletContext();
  const [searchParams] = useSearchParams();

  const [query, setQuery] = useState('');
  const [marketFilter, setMarketFilter] = useState('');
  const [period, setPeriod] = useState(preferences?.analysis_period || '1 Year');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const [selectedStock, setSelectedStock] = useState(null);
  const [activeTab, setActiveTab] = useState('technical');
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [marketData, setMarketData] = useState(null);
  const [fundamentalData, setFundamentalData] = useState(null);
  const [technicalData, setTechnicalData] = useState(null);
  const [savingWatchlist, setSavingWatchlist] = useState(false);

  const searchRef = useRef(null);
  const autoLoadedKey = useRef('');

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const runLiveAnalysis = useCallback(async (stock, targetPeriod) => {
    setSelectedStock(stock);
    setDropdownOpen(false);
    setLoadingAnalysis(true);
    try {
      const params = `market=${encodeURIComponent(stock.market)}&period=${encodeURIComponent(targetPeriod)}`;
      const [mdRes, fundRes, techRes] = await Promise.all([
        api.get(`/stocks/${encodeURIComponent(stock.ticker)}/market-data?${params}`),
        api.get(`/stocks/${encodeURIComponent(stock.ticker)}/fundamental?${params}`),
        api.get(`/stocks/${encodeURIComponent(stock.ticker)}/technical?${params}`),
      ]);
      setMarketData(mdRes.data);
      setFundamentalData(fundRes.data.fundamental_analysis);
      setTechnicalData(techRes.data.technical_analysis);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to collect market data and run analysis.';
      addToast(msg, 'error');
    } finally {
      setLoadingAnalysis(false);
    }
  }, [addToast]);

  useEffect(() => {
    const qTicker = searchParams.get('ticker');
    const qMarket = searchParams.get('market') || preferences?.preferred_market || 'NASDAQ';
    if (qTicker) {
      const key = `${qTicker.toUpperCase()}-${qMarket.toUpperCase()}`;
      if (autoLoadedKey.current !== key) {
        autoLoadedKey.current = key;
        runLiveAnalysis(
          { ticker: qTicker.toUpperCase(), company_name: qTicker.toUpperCase(), market: qMarket.toUpperCase() },
          period
        );
      }
    }
  }, [searchParams, preferences, period, runLiveAnalysis]);

  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      setDropdownOpen(false);
      return;
    }
    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        let url = `/stocks/search?q=${encodeURIComponent(query.trim())}`;
        if (marketFilter) url += `&market=${encodeURIComponent(marketFilter)}`;
        const res = await api.get(url);
        setSearchResults(res.data || []);
        setDropdownOpen(true);
      } catch (err) {
        console.error('Stock search failed:', err);
      } finally {
        setSearching(false);
      }
    }, 280);
    return () => clearTimeout(timer);
  }, [query, marketFilter]);

  const handlePeriodChange = (newPeriod) => {
    setPeriod(newPeriod);
    if (selectedStock) {
      runLiveAnalysis(selectedStock, newPeriod);
    }
  };

  const handleSaveToWatchlist = async () => {
    if (!selectedStock) return;
    setSavingWatchlist(true);
    try {
      await api.post('/watchlist', {
        ticker: selectedStock.ticker,
        company_name: marketData?.profile?.company_name || selectedStock.company_name,
        market: selectedStock.market,
      });
      addToast(`Saved ${selectedStock.ticker} to your watchlist!`, 'success');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Could not add stock to watchlist.';
      addToast(msg, 'error');
    } finally {
      setSavingWatchlist(false);
    }
  };

  const profile = marketData?.profile || {};
  const perf = marketData?.period_performance || {};
  const curSym = profile.currency === 'INR' ? '₹' : '$';

  return (
    <div className="space-y-6 pb-12">
      <div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-[#0A624C] font-semibold">
          Real-Time Market Terminal
        </span>
        <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <Compass className="w-6 h-6 text-[#0A624C]" />
          Live Stock Explorer & Agents
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Search NSE, BSE, NASDAQ & NYSE equities to run OHLCV validation, Fundamental ratios, and Plotly Technical charts
        </p>
      </div>

      <div className="glass-panel p-5 sm:p-6 rounded-3xl space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div ref={searchRef} className="md:col-span-6 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => searchResults.length > 0 && setDropdownOpen(true)}
              placeholder="Search company name or ticker (AAPL, NVDA, INFY, Reliance)..."
              className="w-full pl-10 pr-10 py-2.5 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-[#0A624C] focus:ring-2 focus:ring-emerald-600/15"
            />
            {searching && <Loader2 className="w-4 h-4 text-[#0A624C] animate-spin absolute right-3.5 top-3.5" />}

            {dropdownOpen && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-xl border border-[#E4E1D8] z-40 max-h-80 overflow-y-auto divide-y divide-[#EDEAE0]">
                {searchResults.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">No matching equities found.</div>
                ) : (
                  searchResults.map((s) => (
                    <button
                      key={`${s.market}-${s.ticker}`}
                      type="button"
                      onClick={() => runLiveAnalysis(s, period)}
                      className="w-full px-4 py-3 text-left hover:bg-[#FAF9F5] transition-colors flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-slate-900 text-sm">{s.ticker}</span>
                          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                            {s.market}
                          </span>
                          {s.sector && <span className="text-[11px] text-slate-500">{s.sector}</span>}
                        </div>
                        <p className="text-xs text-slate-600">{s.company_name}</p>
                      </div>
                      <span className="text-xs font-mono font-bold text-[#0A624C]">ANALYZE →</span>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

          <div className="md:col-span-3">
            <select
              value={marketFilter}
              onChange={(e) => setMarketFilter(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-sm font-mono font-semibold text-slate-700 focus:bg-white focus:outline-none focus:border-[#0A624C]"
            >
              <option value="">ALL MARKETS</option>
              <option value="NASDAQ">NASDAQ (US)</option>
              <option value="NYSE">NYSE (US)</option>
              <option value="NSE">NSE (India)</option>
              <option value="BSE">BSE (India)</option>
            </select>
          </div>

          <div className="md:col-span-3">
            <select
              value={period}
              onChange={(e) => handlePeriodChange(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-sm font-mono font-semibold text-slate-700 focus:bg-white focus:outline-none focus:border-[#0A624C]"
            >
              <option value="1 Month">1 Month</option>
              <option value="3 Months">3 Months</option>
              <option value="6 Months">6 Months</option>
              <option value="1 Year">1 Year</option>
              <option value="5 Years">5 Years</option>
            </select>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[10px] font-mono font-semibold text-slate-400 uppercase">QUICK LAUNCH:</span>
          {[
            { ticker: 'AAPL', company_name: 'Apple Inc.', market: 'NASDAQ' },
            { ticker: 'NVDA', company_name: 'NVIDIA Corporation', market: 'NASDAQ' },
            { ticker: 'INFY', company_name: 'Infosys Limited', market: 'NSE' },
            { ticker: 'RELIANCE', company_name: 'Reliance Industries Limited', market: 'NSE' },
            { ticker: 'JPM', company_name: 'JPMorgan Chase & Co.', market: 'NYSE' },
          ].map((preset) => (
            <button
              key={`${preset.market}-${preset.ticker}`}
              type="button"
              onClick={() => runLiveAnalysis(preset, period)}
              className="px-3 py-1 rounded-lg bg-[#FAF9F5] hover:bg-emerald-50 text-slate-700 hover:text-[#0A624C] border border-[#E4E1D8] hover:border-emerald-200 text-xs font-mono font-semibold transition-colors"
            >
              {preset.ticker} <span className="text-slate-400">({preset.market})</span>
            </button>
          ))}
        </div>
      </div>

      {loadingAnalysis && (
        <div className="py-16 glass-panel rounded-3xl text-center space-y-3">
          <Loader2 className="w-8 h-8 text-[#0A624C] animate-spin mx-auto" />
          <p className="text-sm font-bold text-slate-900">
            Collecting OHLCV & financial statements, running Fundamental & Technical Agents...
          </p>
          <p className="text-xs font-mono text-slate-500">
            Validating data quality, computing financial ratios, SMA/EMA/RSI/MACD & volatility metrics.
          </p>
        </div>
      )}

      {!loadingAnalysis && selectedStock && marketData && (
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-3xl flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative overflow-hidden">
            <div className="absolute -right-20 -top-20 w-56 h-56 rounded-full bg-emerald-100/50 blur-3xl pointer-events-none" />
            <div className="relative z-10">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                  {marketData.market}
                </span>
                <span className="text-xs text-slate-500 font-mono">{marketData.yf_symbol}</span>
                <span className="text-xs text-slate-500">• {profile.sector}</span>
              </div>
              <h2 className="font-display text-2xl font-bold text-slate-900">
                {profile.company_name} <span className="text-[#0A624C] font-mono">({marketData.ticker})</span>
              </h2>
              <p className="text-xs font-mono text-slate-600 mt-1">
                PRICE: <span className="font-bold text-slate-900">{curSym}{profile.current_price ?? 'N/A'}</span> •{' '}
                {period.toUpperCase()} RETURN:{' '}
                <span className={`font-bold ${(perf.change_percent || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                  {perf.change_percent >= 0 ? '+' : ''}
                  {perf.change_percent}%
                </span>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5 relative z-10">
              <button
                type="button"
                onClick={handleSaveToWatchlist}
                disabled={savingWatchlist}
                className="px-4 py-2 rounded-xl bg-[#FAF9F5] hover:bg-[#EFECE4] border border-[#DCD8CD] text-xs font-mono font-semibold text-slate-700 flex items-center gap-1.5 transition-colors"
              >
                <Bookmark className="w-3.5 h-3.5 text-amber-600" />
                PIN TO RADAR
              </button>
              <button
                type="button"
                onClick={() => openResearchModal({ ...selectedStock, company_name: profile.company_name })}
                className="px-4 py-2 rounded-xl bg-[#0A624C] hover:bg-[#084C3B] text-white text-xs font-mono font-bold flex items-center gap-1.5 shadow-sm transition-colors"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                SAVE FULL DOSSIER
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { id: 'technical', label: 'Technical Charts & Indicators', icon: Activity },
              { id: 'fundamental', label: 'Fundamental Analysis Agent', icon: PieChart },
              { id: 'market-data', label: 'OHLCV, Financials & Validation', icon: Database },
            ].map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setActiveTab(t.id)}
                  className={`px-4 py-2.5 rounded-xl text-xs font-mono font-bold flex items-center gap-2 border transition-all ${
                    activeTab === t.id
                      ? 'bg-[#0A624C] text-white border-[#0A624C] shadow-sm'
                      : 'bg-white text-slate-600 border-[#E4E1D8] hover:text-slate-900'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {t.label}
                </button>
              );
            })}
          </div>

          {activeTab === 'technical' && <TechnicalPanel technical={technicalData} />}
          {activeTab === 'fundamental' && <FundamentalPanel fundamental={fundamentalData} />}
          {activeTab === 'market-data' && (
            <div className="space-y-6">
              <div className="glass-panel p-6 rounded-3xl space-y-2">
                <h3 className="font-display text-base font-bold text-slate-900 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-[#0A624C]" />
                  Company Profile
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">{profile.description}</p>
              </div>

              <DataQualityPanel dataQuality={marketData.data_quality} sources={marketData.sources} />

              {marketData.ohlcv?.length > 0 && (
                <div className="glass-panel p-6 rounded-3xl space-y-3">
                  <h3 className="font-display text-base font-bold text-slate-900 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-[#1E3A5F]" />
                    Validated Historical OHLCV Data (Latest 20 of {marketData.ohlcv.length})
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#E4E1D8] text-slate-500 font-mono uppercase bg-[#FAF9F5]">
                          <th className="py-2 px-3">Date</th>
                          <th className="py-2 px-3">Open</th>
                          <th className="py-2 px-3">High</th>
                          <th className="py-2 px-3">Low</th>
                          <th className="py-2 px-3">Close</th>
                          <th className="py-2 px-3">Volume</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#EDEAE0] font-mono">
                        {marketData.ohlcv.slice(-20).reverse().map((bar) => (
                          <tr key={bar.date} className="hover:bg-[#FAF9F5]">
                            <td className="py-2 px-3 text-slate-500">{bar.date}</td>
                            <td className="py-2 px-3 text-slate-800">{curSym}{bar.open}</td>
                            <td className="py-2 px-3 text-emerald-700">{curSym}{bar.high}</td>
                            <td className="py-2 px-3 text-rose-700">{curSym}{bar.low}</td>
                            <td className="py-2 px-3 font-bold text-slate-900">{curSym}{bar.close}</td>
                            <td className="py-2 px-3 text-slate-500">{bar.volume.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
