import React, { useState, useEffect, useRef } from 'react';
import { useOutletContext } from 'react-router-dom';
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

  const [query, setQuery] = useState('');
  const [marketFilter, setMarketFilter] = useState('');
  const [period, setPeriod] = useState(preferences?.analysis_period || '1 Year');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const [selectedStock, setSelectedStock] = useState(null);
  const [activeTab, setActiveTab] = useState('technical'); // technical | fundamental | market-data
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [marketData, setMarketData] = useState(null);
  const [fundamentalData, setFundamentalData] = useState(null);
  const [technicalData, setTechnicalData] = useState(null);
  const [savingWatchlist, setSavingWatchlist] = useState(false);

  const searchRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

  const runLiveAnalysis = async (stock, targetPeriod) => {
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
  };

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
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Compass className="w-6 h-6 text-blue-600" />
            Stock Explorer & Live Agents
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Search NSE, BSE, NASDAQ & NYSE stocks to run Market Data Validation, Fundamental Analysis, and Technical Charts
          </p>
        </div>
      </div>

      {/* Search & Controls */}
      <div className="bg-white p-5 sm:p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
          <div ref={searchRef} className="md:col-span-6 relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => searchResults.length > 0 && setDropdownOpen(true)}
              placeholder="Search company name or ticker (e.g., AAPL, NVDA, INFY, Reliance)..."
              className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
            />
            {searching && <Loader2 className="w-4 h-4 text-blue-600 animate-spin absolute right-3.5 top-3.5" />}

            {dropdownOpen && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-xl border border-slate-200 z-40 max-h-80 overflow-y-auto divide-y divide-slate-100">
                {searchResults.length === 0 ? (
                  <div className="p-4 text-center text-xs text-slate-500">No matching equities found.</div>
                ) : (
                  searchResults.map((s) => (
                    <button
                      key={`${s.market}-${s.ticker}`}
                      type="button"
                      onClick={() => runLiveAnalysis(s, period)}
                      className="w-full px-4 py-3 text-left hover:bg-blue-50/50 transition-colors flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 text-sm">{s.ticker}</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                            {s.market}
                          </span>
                          {s.sector && <span className="text-[11px] text-slate-400">{s.sector}</span>}
                        </div>
                        <p className="text-xs text-slate-600">{s.company_name}</p>
                      </div>
                      <span className="text-xs font-semibold text-blue-600">Analyze →</span>
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
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
            >
              <option value="">All Markets (NSE, BSE, US)</option>
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
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-semibold text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600"
            >
              <option value="1 Month">1 Month</option>
              <option value="3 Months">3 Months</option>
              <option value="6 Months">6 Months</option>
              <option value="1 Year">1 Year</option>
              <option value="5 Years">5 Years</option>
            </select>
          </div>
        </div>

        {/* Quick Picks */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase">Quick Explore:</span>
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
              className="px-3 py-1 rounded-lg bg-slate-100 hover:bg-blue-50 text-slate-700 hover:text-blue-700 text-xs font-semibold transition-colors"
            >
              {preset.ticker} ({preset.market})
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {loadingAnalysis && (
        <div className="py-16 bg-white rounded-3xl border border-slate-200/80 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
          <p className="text-sm font-bold text-slate-800">
            Collecting OHLCV & financial statements, running Fundamental & Technical Agents...
          </p>
          <p className="text-xs text-slate-500">
            Validating data quality, computing financial ratios, SMA/EMA/RSI/MACD & volatility metrics.
          </p>
        </div>
      )}

      {/* Results Area */}
      {!loadingAnalysis && selectedStock && marketData && (
        <div className="space-y-6">
          {/* Stock Summary Banner */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white p-6 rounded-3xl shadow-xl border border-slate-800 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30">
                  {marketData.market}
                </span>
                <span className="text-xs text-slate-300 font-mono">{marketData.yf_symbol}</span>
                <span className="text-xs text-slate-400">• {profile.sector}</span>
              </div>
              <h2 className="text-2xl font-extrabold">
                {profile.company_name} <span className="text-blue-400 font-mono">({marketData.ticker})</span>
              </h2>
              <p className="text-xs text-slate-300 mt-1">
                Current Price: <span className="font-bold text-white">{curSym}{profile.current_price ?? 'N/A'}</span> •{' '}
                {period} Return:{' '}
                <span className={`font-bold ${(perf.change_percent || 0) >= 0 ? 'text-emerald-300' : 'text-rose-300'}`}>
                  {perf.change_percent >= 0 ? '+' : ''}
                  {perf.change_percent}%
                </span>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2.5">
              <button
                type="button"
                onClick={handleSaveToWatchlist}
                disabled={savingWatchlist}
                className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-xs font-semibold flex items-center gap-1.5 transition-colors"
              >
                <Bookmark className="w-3.5 h-3.5" />
                Save to Watchlist
              </button>
              <button
                type="button"
                onClick={() => openResearchModal({ ...selectedStock, company_name: profile.company_name })}
                className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-xs font-semibold flex items-center gap-1.5 shadow-lg shadow-blue-600/30 transition-colors"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                Save Full Research Report
              </button>
            </div>
          </div>

          {/* Agent Tabs */}
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'technical', label: 'Technical Analysis & Charts', icon: Activity },
              { id: 'fundamental', label: 'Fundamental Analysis Agent', icon: PieChart },
              { id: 'market-data', label: 'OHLCV, Financials & Data Quality', icon: Database },
            ].map((t) => {
              const Icon = t.icon;
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setActiveTab(t.id)}
                  className={`px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 border transition-all ${
                    activeTab === t.id
                      ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                      : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
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
              <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-2">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Building2 className="w-5 h-5 text-blue-600" />
                  Company Profile
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">{profile.description}</p>
              </div>

              <DataQualityPanel dataQuality={marketData.data_quality} sources={marketData.sources} />

              {/* Recent OHLCV Table */}
              {marketData.ohlcv?.length > 0 && (
                <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm space-y-3">
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-indigo-600" />
                    Validated Historical OHLCV Data (Latest 20 Sessions of {marketData.ohlcv.length})
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-slate-100 text-slate-400 font-semibold">
                          <th className="py-2 px-3">Date</th>
                          <th className="py-2 px-3">Open</th>
                          <th className="py-2 px-3">High</th>
                          <th className="py-2 px-3">Low</th>
                          <th className="py-2 px-3">Close</th>
                          <th className="py-2 px-3">Volume</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 font-mono">
                        {marketData.ohlcv.slice(-20).reverse().map((bar) => (
                          <tr key={bar.date} className="hover:bg-slate-50/70">
                            <td className="py-2 px-3 text-slate-600">{bar.date}</td>
                            <td className="py-2 px-3">{curSym}{bar.open}</td>
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

