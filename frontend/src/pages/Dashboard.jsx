import React, { useState, useEffect, useCallback } from 'react';
import {
  LayoutGrid,
  Star,
  Clock,
  Trash2,
  TrendingUp,
  FolderPlus,
  FileText,
  Sparkles,
  ExternalLink,
  X,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Calendar,
  Globe,
  Loader2,
  SlidersHorizontal,
  Check,
  Activity,
  Download,
  FileDown,
  Database
} from 'lucide-react';
import Navbar from '../components/Navbar';
import StockSearch from '../components/StockSearch';
import AgentCard from '../components/AgentCard';
import StockAnalyticsHub from '../components/StockAnalyticsHub';
import StructuredReportViewer from '../components/StructuredReportViewer';
import { useAuth } from '../context/AuthContext';
import { dashboardService } from '../services/api';

export const Dashboard = () => {
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState([]);
  const [recentResearch, setRecentResearch] = useState([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);
  const [loadingResearch, setLoadingResearch] = useState(false);

  // User Preferences State
  const [preferences, setPreferences] = useState({
    preferred_market: 'NSE',
    preferred_period: '6 Months',
  });
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [prefSavedMessage, setPrefSavedMessage] = useState('');

  // Modal states
  const [isResearchModalOpen, setIsResearchModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [activeReport, setActiveReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [launchingResearch, setLaunchingResearch] = useState(false);
  const [pdfNotice, setPdfNotice] = useState(false);

  const handleDownloadMarkdown = () => {
    if (!activeReport) return;
    const reportDate = new Date(activeReport?.created_at || selectedTask?.created_at).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
    const mdText = `# Research Report: ${selectedTask?.ticker} - ${selectedTask?.company_name}
Report Generated Date: ${reportDate}
Data Source: yfinance API
Data Retrieval Timestamp: ${new Date(selectedTask?.created_at).toLocaleString()}
Market Exchange: ${selectedTask?.market} | Horizon: ${selectedTask?.requested_period}

## Executive Summary
${activeReport.summary}

## Detailed Findings
${activeReport.report_content}

## Limitations & Disclaimer
${activeReport.limitations}
`;
    const blob = new Blob([mdText], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${selectedTask?.ticker || 'Stock'}_Research_Report.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Market Analytics Hub State (Appears only when user searches or selects a stock)
  const [analyticsTicker, setAnalyticsTicker] = useState(null);

  const handleSelectStockForAnalytics = (selectedTicker) => {
    setAnalyticsTicker(selectedTicker);
    // Smooth scroll down to the analytics hub
    setTimeout(() => {
      const el = document.getElementById('analytics-hub');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  };

  const handleQuickAddWatchlist = async (tickerToAdd) => {
    try {
      await dashboardService.addToWatchlist(tickerToAdd);
      fetchWatchlist();
    } catch (e) {
      console.error('Failed to add to watchlist:', e);
    }
  };

  // USD currency confirmation modal (for watchlist, preference, analytics)
  const [usdConfirm, setUsdConfirm] = useState({ open: false, stock: null, type: null, targetMarket: null });

  // Form state for new research
  const [researchForm, setResearchForm] = useState({
    ticker: '',
    company_name: '',
    market: 'NSE',
    requested_period: '6 Months',
  });

  const fetchWatchlist = useCallback(async () => {
    try {
      setLoadingWatchlist(true);
      const data = await dashboardService.getWatchlist();
      setWatchlist(data || []);
    } catch (err) {
      console.error('Error fetching watchlist:', err);
    } finally {
      setLoadingWatchlist(false);
    }
  }, []);

  const fetchRecentResearch = useCallback(async () => {
    try {
      setLoadingResearch(true);
      const data = await dashboardService.getRecentResearch();
      setRecentResearch(data || []);
    } catch (err) {
      console.error('Error fetching recent research:', err);
    } finally {
      setLoadingResearch(false);
    }
  }, []);

  const fetchPreferences = useCallback(async () => {
    try {
      const data = await dashboardService.getPreferences();
      if (data) {
        setPreferences({
          preferred_market: data.preferred_market || 'NSE',
          preferred_period: data.preferred_period || '6 Months',
        });
      }
    } catch (err) {
      console.error('Failed to load user preferences:', err);
    }
  }, []);

  useEffect(() => {
    fetchWatchlist();
    fetchRecentResearch();
    fetchPreferences();
  }, [fetchWatchlist, fetchRecentResearch, fetchPreferences]);

  const handleSavePreferences = async (e) => {
    if (e) e.preventDefault();
    try {
      setSavingPreferences(true);
      await dashboardService.updatePreferences(preferences);
      setPrefSavedMessage('Preferences saved to database!');
      setTimeout(() => setPrefSavedMessage(''), 2500);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    } finally {
      setSavingPreferences(false);
    }
  };

  const handleRemoveFromWatchlist = async (savedStockId) => {
    try {
      await dashboardService.removeFromWatchlist(savedStockId);
      setWatchlist((prev) => prev.filter((item) => item.saved_stock_id !== savedStockId));
    } catch (err) {
      console.error('Failed to remove stock:', err);
    }
  };

  const openResearchModal = (ticker, companyName = '', market = '') => {
    let detectedMarket = preferences.preferred_market;
    if (market) {
      if (market.includes('NSE') || market.includes('India')) detectedMarket = 'NSE';
      else if (market.includes('BSE')) detectedMarket = 'BSE';
      else if (market.includes('NASDAQ')) detectedMarket = 'NASDAQ';
      else if (market.includes('NYSE') || market.includes('United States')) detectedMarket = 'NYSE';
    }

    setResearchForm({
      ticker: ticker,
      company_name: companyName,
      market: detectedMarket,
      requested_period: preferences.preferred_period || '6 Months',
    });
    setIsResearchModalOpen(true);
  };

  const handleLaunchResearch = async (e) => {
    e.preventDefault();
    if (!researchForm.ticker) return;

    try {
      setLaunchingResearch(true);
      await dashboardService.createResearchTask(researchForm);
      await fetchRecentResearch();
      setIsResearchModalOpen(false);
    } catch (err) {
      console.error('Failed to launch research:', err);
    } finally {
      setLaunchingResearch(false);
    }
  };

  const handleOpenReport = async (task) => {
    try {
      setSelectedTask(task);
      setLoadingReport(true);
      setIsReportModalOpen(true);
      const reportData = await dashboardService.getResearchReport(task.task_id);
      setActiveReport(reportData);
    } catch (err) {
      console.error('Failed to load report:', err);
    } finally {
      setLoadingReport(false);
    }
  };

  const isUSMarket = (market) => market === 'NASDAQ' || market === 'NYSE';

  const displayName = user?.full_name || 'Stock Researcher';

  return (
    <div className="min-h-screen bg-[#05080a] text-slate-100 flex flex-col justify-between selection:bg-emerald-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-7">

        {/* Welcome Section */}
        <section className="relative flex items-center min-h-[135px] sm:min-h-[155px] px-3 sm:px-6 py-4 overflow-hidden rounded-2xl">
          {/* Left Text */}
          <div className="relative z-10 max-w-xl">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight drop-shadow-md">
              Welcome back, <span className="text-white">{displayName}</span>!
            </h1>
            <p className="mt-1.5 text-sm sm:text-base text-slate-300/90 font-normal drop-shadow-sm">
              Your stock research workspace.
            </p>
          </div>

          {/* Globe & Candlesticks graphic */}
          <div className="absolute inset-0 w-full h-full pointer-events-none select-none overflow-hidden flex justify-end items-center">
            <div className="relative w-full h-full flex justify-end">
              <img
                src="/images/dashboard-globe.png"
                alt="Digital Financial Globe and Market Growth"
                className="w-full sm:w-[92%] lg:w-[85%] h-full object-cover object-right opacity-85 sm:opacity-90"
              />
              <div className="absolute inset-0 bg-gradient-to-r from-[#05080a] via-[#05080a]/60 to-transparent pointer-events-none" />
            </div>
          </div>
        </section>

        {/* Section: User Preferences Control Bar */}
        <section className="bg-[#0b0f15] border border-[#1c2533] rounded-2xl p-4 sm:p-5 shadow-sm">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">

            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shrink-0">
                <SlidersHorizontal className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white">Research Preferences</h3>
                <p className="text-xs text-slate-400">Save default market exchange and historical analysis horizon</p>
              </div>
            </div>

            <div className="flex items-center flex-wrap gap-3 w-full md:w-auto">
              {/* Market Preference Dropdown */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-400 font-medium">Market:</span>
                <select
                  value={preferences.preferred_market}
                  onChange={(e) => {
                    const newMarket = e.target.value;
                    if (newMarket === 'NASDAQ' || newMarket === 'NYSE') {
                      setUsdConfirm({
                        open: true,
                        type: 'preference',
                        targetMarket: newMarket,
                        stock: null,
                      });
                    } else {
                      setPreferences({ ...preferences, preferred_market: newMarket });
                    }
                  }}
                  className="px-3 py-1.5 bg-[#111620] border border-[#1e293b] rounded-lg text-xs font-semibold text-white focus:outline-none focus:border-emerald-500 transition-colors"
                >
                  <option value="NSE">NSE (India)</option>
                  <option value="BSE">BSE (India)</option>
                  <option value="NASDAQ">NASDAQ (US)</option>
                  <option value="NYSE">NYSE (US)</option>
                </select>
              </div>

              {/* Analysis Period Dropdown */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-slate-400 font-medium">Period:</span>
                <select
                  value={preferences.preferred_period}
                  onChange={(e) => setPreferences({ ...preferences, preferred_period: e.target.value })}
                  className="px-3 py-1.5 bg-[#111620] border border-[#1e293b] rounded-lg text-xs font-semibold text-white focus:outline-none focus:border-emerald-500 transition-colors"
                >
                  <option value="1 Month">1 Month</option>
                  <option value="3 Months">3 Months</option>
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="5 Years">5 Years</option>
                </select>
              </div>

              {/* Save Preferences Button */}
              <button
                type="button"
                onClick={handleSavePreferences}
                disabled={savingPreferences}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition-all disabled:opacity-60 shrink-0"
              >
                {savingPreferences ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Check className="w-3.5 h-3.5" />
                )}
                <span>Save</span>
              </button>

              {prefSavedMessage && (
                <span className="text-xs text-emerald-400 font-medium animate-fade-in">
                  ✓ {prefSavedMessage}
                </span>
              )}
            </div>

          </div>
        </section>

        {/* Stock Search Section */}
        <section>
          <StockSearch
            onWatchlistUpdated={fetchWatchlist}
            onStartResearch={openResearchModal}
            onSelectStock={handleSelectStockForAnalytics}
          />
        </section>

        {/* Module 2: Market Analytics & Financial Intelligence Hub */}
        {analyticsTicker && (
          <section id="analytics-hub" className="animate-fade-in">
            <StockAnalyticsHub
              ticker={analyticsTicker}
              initialPeriod={preferences.preferred_period}
              onClose={() => setAnalyticsTicker(null)}
              onAddToWatchlist={handleQuickAddWatchlist}
              onOpenResearch={openResearchModal}
            />
          </section>
        )}

        {/* Research Agents Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2">
            <LayoutGrid className="w-5 h-5 text-white" />
            <h2 className="text-xl font-bold text-white tracking-tight">Research Agents</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AgentCard
              title="Fundamental Analysis Agent"
              description="Analyzes company revenue, earnings, profitability, debt, and financial ratios."
              iconType="fundamental"
            />
            <AgentCard
              title="Technical Analysis Agent"
              description="Examines historical stock prices, market trends, SMA, EMA, RSI, and MACD."
              iconType="technical"
            />
            <AgentCard
              title="News and Sentiment Analysis Agent"
              description="Analyzes financial news, company announcements, and market sentiment."
              iconType="news"
            />
            <AgentCard
              title="Risk Analysis Agent"
              description="Evaluates financial risks, market volatility, maximum drawdown, and conflicting findings."
              iconType="risk"
            />
          </div>
        </section>

        {/* Bottom Dual Panels: My Watchlist & Recent Research */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Left Panel: My Watchlist */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Star className="w-5 h-5 text-amber-400 fill-amber-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">My Watchlist</h2>
            </div>

            <div className="bg-[#0b0f15] border border-[#1c2533] rounded-2xl p-5 min-h-[220px] flex flex-col justify-center shadow-sm">
              {watchlist.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-center text-slate-400 py-6">
                  <div className="w-12 h-12 rounded-xl bg-[#121924] border border-[#1c2533] flex items-center justify-center mb-3 text-slate-400">
                    <FolderPlus className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <p className="text-sm font-medium text-slate-400">
                    Your manually saved stocks will appear here.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-[#18212e] w-full">
                  {watchlist.map((stock) => (
                    <div key={stock.saved_stock_id} className="flex items-center justify-between py-3 px-1 gap-2">
                      {/* Left: ticker + enriched market info (Clickable to open Market Analytics & Financial Intelligence) */}
                      <div
                        onClick={() => {
                          if (stock.is_us_market) {
                            setUsdConfirm({ open: true, stock, type: 'analytics' });
                          } else {
                            handleSelectStockForAnalytics(stock.ticker);
                          }
                        }}
                        className="flex flex-col min-w-0 cursor-pointer group"
                        title="Click to view Market Analytics & Financial Intelligence"
                      >
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-white text-sm tracking-wide group-hover:text-emerald-400 transition-colors">
                            {stock.ticker}
                          </span>
                          {/* Currency badge */}
                          {stock.is_us_market ? (
                            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-amber-950/60 text-amber-400 border border-amber-500/40">$ USD</span>
                          ) : (
                            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">₹ INR</span>
                          )}
                          {stock.exchange && (
                            <span className="text-[10px] text-slate-500 font-medium">{stock.exchange}</span>
                          )}
                        </div>
                        {stock.company_name && (
                          <span className="text-[11px] text-slate-400 truncate max-w-[180px] mt-0.5 group-hover:text-slate-200 transition-colors">
                            {stock.company_name}
                          </span>
                        )}
                        <div className="flex items-center gap-2 mt-0.5">
                          {stock.current_price != null && (
                            <span className="text-xs font-semibold text-slate-200">
                              {stock.currency_symbol || (stock.is_us_market ? '$' : '₹')}{Number(stock.current_price).toFixed(2)}
                            </span>
                          )}
                          {stock.change_percent != null && (
                            <span className={`text-[10px] font-semibold ${stock.change_percent >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {stock.change_percent >= 0 ? '+' : ''}{Number(stock.change_percent).toFixed(2)}%
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {/* Analyze — USD confirmation for US stocks */}
                        <button
                          onClick={() => {
                            if (stock.is_us_market) {
                              setUsdConfirm({ open: true, stock, type: 'research' });
                            } else {
                              openResearchModal(stock.ticker, stock.company_name, stock.exchange || '');
                            }
                          }}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-950/40 hover:bg-emerald-900/50 text-emerald-300 border border-emerald-500/30 transition-all"
                          title="Start research for this saved stock"
                        >
                          <Sparkles className="w-3 h-3 text-emerald-400" />
                          <span>Analyze</span>
                        </button>

                        {/* Remove */}
                        <button
                          onClick={() => handleRemoveFromWatchlist(stock.saved_stock_id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-950/30 transition-colors"
                          title="Remove from watchlist"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Panel: Recent Research */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-200" />
              <h2 className="text-lg font-bold text-white tracking-tight">Recent Research</h2>
            </div>

            <div className="bg-[#0b0f15] border border-[#1c2533] rounded-2xl p-5 min-h-[220px] flex flex-col justify-center shadow-sm">
              {recentResearch.length === 0 ? (
                <div className="flex flex-col items-center justify-center text-center text-slate-400 py-6">
                  <div className="w-12 h-12 rounded-xl bg-[#121924] border border-[#1c2533] flex items-center justify-center mb-3 text-slate-400">
                    <FileText className="w-6 h-6 stroke-[1.5]" />
                  </div>
                  <p className="text-sm font-medium text-slate-400">
                    Your previous research records will appear here.
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-[#18212e] w-full">
                  {recentResearch.map((task) => (
                    <div key={task.task_id} className="flex items-center justify-between py-3 px-1 gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-bold text-white text-sm">{task.ticker}</span>
                          <span className="text-xs text-slate-400 truncate">
                            {task.company_name}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                          <span className="font-medium text-slate-300">{task.market}</span>
                          <span>•</span>
                          <span>{task.requested_period}</span>
                          <span>•</span>
                          <span>{new Date(task.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2.5 shrink-0">
                        {/* Research Status Badge */}
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-950/70 text-emerald-400 border border-emerald-500/40 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                          <span>{task.status}</span>
                        </span>

                        {/* Open report */}
                        <button
                          onClick={() => handleOpenReport(task)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-[#141d2a] hover:bg-[#1a2536] text-slate-200 border border-[#243347] transition-all"
                        >
                          <FileText className="w-3 h-3 text-emerald-400" />
                          <span>Report</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        </section>

      </main>

      {/* ── MODAL 1: USD Currency Confirmation (Preference, Watchlist, Analytics) ── */}
      {usdConfirm.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-sm bg-[#0b0f15] border border-amber-500/40 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-start gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white mb-1">Currency Notice — US Dollar Market</h3>
                {usdConfirm.type === 'preference' ? (
                  <p className="text-sm text-slate-300 leading-relaxed">
                    You have selected <span className="font-semibold text-amber-300">{usdConfirm.targetMarket} (US Market)</span> as your market preference. All stock valuations, historical prices, and analytics will be quoted in <span className="font-bold text-white">US Dollars (USD $)</span>.
                  </p>
                ) : (
                  <p className="text-sm text-slate-300 leading-relaxed">
                    <span className="font-semibold text-amber-300">{usdConfirm.stock?.ticker}</span> is listed on a{' '}
                    <span className="font-semibold text-amber-300">US Exchange ({usdConfirm.stock?.exchange || 'NASDAQ/NYSE'})</span>.
                    All prices and financial data are quoted in{' '}
                    <span className="font-bold text-white">US Dollars (USD $)</span>.
                  </p>
                )}
              </div>
            </div>
            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/20 text-xs text-amber-300/90 mb-5">
              💡 If you are based in India, note that returns and metrics will be affected by USD/INR foreign exchange fluctuations.
            </div>
            <div className="flex items-center gap-3 justify-end">
              <button
                type="button"
                onClick={() => setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null })}
                className="px-4 py-2 rounded-lg border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  if (usdConfirm.type === 'preference') {
                    setPreferences((prev) => ({ ...prev, preferred_market: usdConfirm.targetMarket }));
                    setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null });
                  } else if (usdConfirm.type === 'analytics') {
                    const t = usdConfirm.stock?.ticker;
                    setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null });
                    if (t) handleSelectStockForAnalytics(t);
                  } else {
                    const s = usdConfirm.stock;
                    setUsdConfirm({ open: false, stock: null, type: null, targetMarket: null });
                    if (s) openResearchModal(s.ticker, s.company_name, s.exchange || 'NASDAQ');
                  }
                }}
                className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold transition-all shadow-md"
              >
                Yes, Proceed in USD ($)
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── MODAL 2: Launch Stock Research Task ── */}
      {isResearchModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-md bg-[#0b0f15] border border-[#1c2533] rounded-3xl p-6 sm:p-7 shadow-2xl relative">

            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Start Research Task</h3>
                  <p className="text-xs text-slate-400">Configure parameters for Multi-Agent analysis</p>
                </div>
              </div>
              <button
                onClick={() => setIsResearchModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleLaunchResearch} className="space-y-4">
              {/* Selected Stock Info */}
              <div className="p-3 rounded-xl bg-[#101722] border border-[#1c2533] flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400">Target Asset</span>
                  <div className="font-bold text-white text-base">{researchForm.ticker}</div>
                </div>
                {researchForm.company_name && (
                  <span className="text-xs text-slate-300 max-w-[200px] truncate text-right">
                    {researchForm.company_name}
                  </span>
                )}
              </div>

              {/* Market Selection */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5 text-slate-400" />
                  <span>Market / Exchange</span>
                </label>
                <select
                  value={researchForm.market}
                  onChange={(e) => setResearchForm({ ...researchForm, market: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="NSE">NSE – National Stock Exchange of India</option>
                  <option value="BSE">BSE – BSE Ltd., India</option>
                  <option value="NASDAQ">NASDAQ – US Stock Exchange</option>
                  <option value="NYSE">NYSE – New York Stock Exchange</option>
                </select>
              </div>

              {/* USD Currency Notice — shown when NASDAQ or NYSE is selected */}
              {isUSMarket(researchForm.market) && (
                <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/30 border border-amber-500/30">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-amber-300 leading-relaxed">
                    <span className="font-semibold text-amber-200">Currency Notice:</span> This stock is on a US exchange ({researchForm.market}).
                    All prices and financial data are quoted in <span className="font-bold text-white">US Dollars (USD $)</span>.
                  </p>
                </div>
              )}

              {/* Analysis Period */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>Analysis Period</span>
                </label>
                <select
                  value={researchForm.requested_period}
                  onChange={(e) => setResearchForm({ ...researchForm, requested_period: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="1 Month">1 Month</option>
                  <option value="3 Months">3 Months</option>
                  <option value="6 Months">6 Months</option>
                  <option value="1 Year">1 Year</option>
                  <option value="5 Years">5 Years</option>
                </select>
              </div>

              {/* Action Buttons */}
              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsResearchModalOpen(false)}
                  className="px-4 py-2.5 rounded-lg border border-[#1e293b] text-xs font-medium text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={launchingResearch}
                  className="px-5 py-2.5 rounded-lg bg-[#00a86b] hover:bg-[#00ba77] text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-emerald-900/30 transition-all disabled:opacity-60"
                >
                  {launchingResearch ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Saving Task...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Launch Research Task</span>
                    </>
                  )}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

      {/* ── MODAL 3: View Generated Research Report ── */}
      {isReportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm">
          <div className="w-full max-w-3xl bg-[#0b0f15] border border-[#1c2533] rounded-3xl p-6 sm:p-8 shadow-2xl relative max-h-[90vh] flex flex-col justify-between">

            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1c2533] pb-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>{selectedTask?.ticker}</span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/30">
                      Report Complete
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    {selectedTask?.company_name} • {selectedTask?.market} ({selectedTask?.requested_period})
                  </p>
                  {/* Report Generated Date, Data Source & Retrieval Time Badges */}
                  <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-2.5 flex-wrap">
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121924] border border-[#1e293b] text-emerald-300 font-medium">
                      <Calendar className="w-3 h-3 text-emerald-400" />
                      <span>Generated: <strong className="text-white">{new Date(activeReport?.created_at || selectedTask?.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</strong></span>
                    </span>
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121924] border border-[#1e293b] text-slate-300 font-medium">
                      <Database className="w-3 h-3 text-emerald-400" />
                      <span>Source: <strong className="text-white">yfinance API</strong></span>
                    </span>
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#121924] border border-[#1e293b] text-slate-300 font-mono">
                      <Clock className="w-3 h-3 text-cyan-400" />
                      <span>Retrieved: {new Date(selectedTask?.created_at).toLocaleString()}</span>
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  setIsReportModalOpen(false);
                  setPdfNotice(false);
                }}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto pr-2 space-y-4 text-xs sm:text-sm">
              {/* PDF Export Banner Notice */}
              {pdfNotice && (
                <div className="p-3 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs flex items-center justify-between animate-fade-in">
                  <span>📄 <strong>PDF Export Notice:</strong> PDF report download option is currently a placeholder. Markdown report download is active below!</span>
                  <button onClick={() => setPdfNotice(false)} className="text-amber-400 hover:text-white ml-2 text-sm">✕</button>
                </div>
              )}

              {loadingReport ? (
                <div className="flex items-center justify-center py-16 gap-3 text-slate-400">
                  <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
                  <span>Loading report from database...</span>
                </div>
              ) : activeReport ? (
                <>
                  {/* Executive Summary */}
                  <div className="p-4 sm:p-5 rounded-2xl bg-[#0c121c] border border-emerald-500/25 space-y-3 shadow-md">
                    <div className="flex items-center justify-between border-b border-[#182333] pb-2.5">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400">
                          <Sparkles className="w-3.5 h-3.5" />
                        </div>
                        <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                          Executive Synthesis
                        </h4>
                      </div>
                      <div className="flex items-center gap-2">
                        {isUSMarket(selectedTask?.market) && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            USD ($)
                          </span>
                        )}
                        <span className="text-[10px] font-medium text-slate-400 bg-[#141b25] px-2 py-0.5 rounded-md border border-[#222e40]">
                          {selectedTask?.requested_period}
                        </span>
                      </div>
                    </div>

                    {/* US Currency Notice Callout */}
                    {(isUSMarket(selectedTask?.market) || activeReport.summary?.includes('Currency Notice')) && (
                      <div className="flex items-start gap-2.5 p-3 rounded-xl bg-amber-950/25 border border-amber-500/30 text-xs text-amber-300/90 leading-relaxed">
                        <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-semibold text-amber-200">US Market Currency Notice: </span>
                          <span>
                            All valuation multiples, historical prices, and financial metrics for {selectedTask?.ticker} are quoted in <strong className="text-white">US Dollars ($ USD)</strong>.
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Clean Synthesis Narrative */}
                    <p className="text-slate-200 text-xs sm:text-sm leading-relaxed font-normal">
                      {activeReport.summary
                        .replace(/\*\*⚠️ Currency Notice.*?\*\*\.?/gs, '')
                        .replace(/All valuation multiples and metrics for .*? are denominated in \*\*US Dollars \(\$ USD\)\*\*\.?/gs, '')
                        .replace(/\*\*/g, '')
                        .trim()}
                    </p>
                  </div>

                  {/* Multi-Agent Breakdown Rendered via StructuredReportViewer */}
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                        Research Findings
                      </h4>
                      <span className="text-[11px] text-slate-400">
                        AI-Powered Research Report
                      </span>
                    </div>
                    <StructuredReportViewer content={activeReport.report_content} />
                  </div>

                  {/* Limitations and Disclaimer */}
                  <div className="p-3.5 rounded-xl bg-[#141312] border border-amber-900/30 text-amber-300/80 text-xs flex items-start gap-2.5">
                    <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-amber-300 block mb-0.5">Disclaimer & Limitations</span>
                      <p className="text-slate-400 leading-normal">
                        {activeReport.limitations}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-10 text-slate-400">
                  Could not load report content.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="pt-4 border-t border-[#1c2533] mt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-[11px] text-slate-400 order-2 sm:order-1 flex-wrap">
                <span>Generated: <strong className="text-emerald-400">{new Date(activeReport?.created_at || selectedTask?.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</strong></span>
                <span>•</span>
                <span>Source: <strong className="text-white">yfinance API</strong></span>
                <span>•</span>
                <span>Retrieved: <strong className="text-slate-300">{new Date(selectedTask?.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</strong></span>
              </div>
              <div className="flex items-center gap-2 order-1 sm:order-2 flex-wrap">
                {/* Dummy Download PDF Button (Module 8 Feature) */}
                <button
                  type="button"
                  onClick={() => setPdfNotice(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#141b25] hover:bg-[#1a2330] text-xs font-semibold text-slate-300 border border-[#222e40] hover:border-slate-500 transition-colors shadow-sm"
                  title="Export report as formatted PDF (Module 8 Feature)"
                >
                  <FileDown className="w-3.5 h-3.5 text-red-400" />
                  <span>Download PDF</span>
                </button>

                {/* Download Markdown Report Button */}
                <button
                  type="button"
                  onClick={handleDownloadMarkdown}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-xs font-semibold text-emerald-300 border border-emerald-500/40 transition-colors shadow-sm"
                  title="Download report as Markdown (.md)"
                >
                  <Download className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Download Markdown</span>
                </button>

                <button
                  onClick={() => {
                    setIsReportModalOpen(false);
                    setPdfNotice(false);
                  }}
                  className="px-4 py-1.5 rounded-lg bg-[#141b25] hover:bg-[#1a2330] text-xs font-medium text-slate-200 border border-[#222e40] transition-colors"
                >
                  Close Report
                </button>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="w-full bg-[#070a0e] border-t border-[#1c2533] py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-400">
          <div>
            <span className="font-bold text-slate-200">Multi-Agent Stock Research Analyst</span>
            <span className="mx-2 text-slate-600">|</span>
            <span>AI-Powered Stock Research and Analysis Platform.</span>
          </div>
          <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
            <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
            <span>Research Smarter. Invest Better.</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Dashboard;
