import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  TrendingUp,
  BarChart3,
  DollarSign,
  AlertTriangle,
  RefreshCw,
  Building2,
  Users,
  CheckCircle2,
  ShieldCheck,
  Scale,
  Calendar,
  ExternalLink,
  Search,
  Award,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Info,
  Briefcase,
  X
} from 'lucide-react';
import { stockService } from '../services/api';

/* ── Quick suggestions for peer dual-search autocomplete ── */
const PEER_QUICK_SUGGESTIONS = [
  { ticker: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ (US)' },
  { ticker: 'MSFT', name: 'Microsoft Corporation', exchange: 'NASDAQ (US)' },
  { ticker: 'GOOGL', name: 'Alphabet Inc.', exchange: 'NASDAQ (US)' },
  { ticker: 'AMZN', name: 'Amazon.com Inc.', exchange: 'NASDAQ (US)' },
  { ticker: 'TSLA', name: 'Tesla, Inc.', exchange: 'NASDAQ (US)' },
  { ticker: 'NVDA', name: 'NVIDIA Corporation', exchange: 'NASDAQ (US)' },
  { ticker: 'META', name: 'Meta Platforms Inc.', exchange: 'NASDAQ (US)' },
  { ticker: 'JPM', name: 'JPMorgan Chase & Co.', exchange: 'NYSE (US)' },
  { ticker: 'V', name: 'Visa Inc.', exchange: 'NYSE (US)' },
  { ticker: 'WMT', name: 'Walmart Inc.', exchange: 'NYSE (US)' },
  { ticker: 'RELIANCE.NS', name: 'Reliance Industries', exchange: 'NSE (India)' },
  { ticker: 'TCS.NS', name: 'Tata Consultancy Services', exchange: 'NSE (India)' },
  { ticker: 'INFY.NS', name: 'Infosys Limited', exchange: 'NSE (India)' },
  { ticker: 'HDFCBANK.NS', name: 'HDFC Bank Limited', exchange: 'NSE (India)' },
  { ticker: 'WIPRO.NS', name: 'Wipro Limited', exchange: 'NSE (India)' },
  { ticker: 'ICICIBANK.NS', name: 'ICICI Bank Limited', exchange: 'NSE (India)' },
  { ticker: 'SBIN.NS', name: 'State Bank of India', exchange: 'NSE (India)' },
  { ticker: 'HINDUNILVR.NS', name: 'Hindustan Unilever', exchange: 'NSE (India)' },
  { ticker: 'BHARTIARTL.NS', name: 'Bharti Airtel Limited', exchange: 'NSE (India)' },
  { ticker: 'ITC.NS', name: 'ITC Limited', exchange: 'NSE (India)' },
];

export const FundamentalAnalysisModal = ({
  isOpen,
  onClose,
  initialTicker = 'INFY.NS',
  preferredMarket,
}) => {
  const [ticker, setTicker] = useState(initialTicker);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedPeer, setSelectedPeer] = useState('');
  const [showCustomPeer, setShowCustomPeer] = useState(false);

  /* Chart metric toggle */
  const [chartMetric, setChartMetric] = useState('all');

  /* Company profile summary expand */
  const [showFullSummary, setShowFullSummary] = useState(false);

  /* Peer dual-search autocomplete */
  const [peerSearchQuery, setPeerSearchQuery] = useState('');
  const [peerSuggestions, setPeerSuggestions] = useState([]);
  const [peerSearchLoading, setPeerSearchLoading] = useState(false);
  const [showPeerDropdown, setShowPeerDropdown] = useState(false);
  const [dismissAuditNotice, setDismissAuditNotice] = useState(false);
  const peerSearchRef = useRef(null);
  const peerDebounceRef = useRef(null);

  /* ── Lifecycle ── */
  useEffect(() => {
    if (isOpen && initialTicker) {
      setTicker(initialTicker);
      setSelectedPeer('');
      setShowCustomPeer(false);
      setPeerSearchQuery('');
      setChartMetric('all');
      setShowFullSummary(false);
      setDismissAuditNotice(false);
      fetchAnalysis(initialTicker, null);
    }
  }, [isOpen, initialTicker]);

  /* Close peer dropdown on outside click */
  useEffect(() => {
    const handler = (e) => {
      if (peerSearchRef.current && !peerSearchRef.current.contains(e.target)) {
        setShowPeerDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  /* ── API ── */
  const fetchAnalysis = async (targetTicker, peerTicker) => {
    setLoading(true);
    setError(null);
    try {
      const res = await stockService.getFundamentalAnalysis(targetTicker, peerTicker);
      setData(res);
      if (res?.peer_comparison?.selected_peer) {
        setSelectedPeer(res.peer_comparison.selected_peer);
      }
    } catch (err) {
      console.error('Fundamental analysis error:', err);
      setError(
        err?.response?.data?.detail ||
          'Failed to retrieve fundamental financial analysis.'
      );
    } finally {
      setLoading(false);
    }
  };

  /* ── Peer selection handlers ── */
  const handlePeerChange = (newPeer) => {
    if (newPeer === 'CUSTOM') {
      setShowCustomPeer(true);
      return;
    }
    setShowCustomPeer(false);
    setSelectedPeer(newPeer);
    fetchAnalysis(ticker, newPeer);
  };

  /* Dual-search: filters PEER_QUICK_SUGGESTIONS instantly, then
     debounces a live API call via stockService.search() */
  const handlePeerSearchInput = useCallback(
    (query) => {
      setPeerSearchQuery(query);
      setShowPeerDropdown(true);

      if (!query.trim()) {
        setPeerSuggestions([]);
        setPeerSearchLoading(false);
        return;
      }

      const q = query.toLowerCase();
      const quickMatches = PEER_QUICK_SUGGESTIONS.filter(
        (s) =>
          s.ticker.toLowerCase().includes(q) ||
          s.name.toLowerCase().includes(q)
      ).filter((s) => s.ticker.toUpperCase() !== ticker.toUpperCase());
      setPeerSuggestions(quickMatches.slice(0, 6));

      if (peerDebounceRef.current) clearTimeout(peerDebounceRef.current);
      setPeerSearchLoading(true);
      peerDebounceRef.current = setTimeout(async () => {
        try {
          const apiResults = await stockService.search(query);
          const combined = [...quickMatches];
          const seen = new Set(
            quickMatches.map((s) => s.ticker.toUpperCase())
          );
          seen.add(ticker.toUpperCase());

          if (Array.isArray(apiResults)) {
            apiResults.forEach((r) => {
              if (!seen.has(r.ticker?.toUpperCase())) {
                combined.push({
                  ticker: r.ticker,
                  name: r.name || r.company_name || r.ticker,
                  exchange: r.exchange || r.market || '',
                });
                seen.add(r.ticker?.toUpperCase());
              }
            });
          }
          setPeerSuggestions(combined.slice(0, 8));
        } catch {
          /* keep quick-match results on error */
        } finally {
          setPeerSearchLoading(false);
        }
      }, 350);
    },
    [ticker]
  );

  const handleSelectPeerSuggestion = (suggestion) => {
    setSelectedPeer(suggestion.ticker);
    setPeerSearchQuery('');
    setShowPeerDropdown(false);
    setShowCustomPeer(false);
    fetchAnalysis(ticker, suggestion.ticker);
  };

  /* ── Guard ── */
  if (!isOpen) return null;

  /* ── Derived data ── */
  const profile = data?.company_profile || {};
  const revEarnings = data?.revenue_earnings || {};
  const multiYearChart = revEarnings?.multi_year_chart || [];
  const profitability = data?.profitability || {};
  const debtStability = data?.debt_stability || {};
  const valuation = data?.valuation_ratios || {};
  const peerComp = data?.peer_comparison || {};
  const missingAudit = data?.missing_data_audit || {};
  const historicalGrowth = data?.historical_comparison || [];

  const currSym = data?.currency === 'USD' ? '$' : '₹';

  const formatMoneyVal = (val, formatted) => {
    if (formatted) return formatted;
    if (val === null || val === undefined) return 'N/A';
    if (typeof val === 'number') {
      const abs = Math.abs(val);
      const sign = val < 0 ? '-' : '';
      if (data?.currency === 'USD') {
        if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`;
        if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(2)}M`;
      } else {
        if (abs >= 1e7) return `${sign}₹${(abs / 1e7).toFixed(2)} Cr`;
        if (abs >= 1e5) return `${sign}₹${(abs / 1e5).toFixed(2)} Lakh`;
      }
      return `${sign}${currSym}${abs.toLocaleString()}`;
    }
    return String(val);
  };

  /* Chart bars per selected metric */
  const getBarData = (item) => {
    switch (chartMetric) {
      case 'revenue':
        return [
          {
            key: 'rev',
            val: Number(item.revenue) || 0,
            fmt: item.revenue_formatted,
            color: 'bg-cyan-500',
            label: 'Revenue',
          },
        ];
      case 'net_income':
        return [
          {
            key: 'ni',
            val: Math.max(0, Number(item.net_income) || 0),
            fmt: item.net_income_formatted,
            color: 'bg-emerald-500',
            label: 'Net Income',
          },
        ];
      case 'ebitda':
        return [
          {
            key: 'ebitda',
            val: Number(item.ebitda) || 0,
            fmt: item.ebitda_formatted,
            color: 'bg-purple-500',
            label: 'EBITDA',
          },
        ];
      default:
        return [
          {
            key: 'rev',
            val: Number(item.revenue) || 0,
            fmt: item.revenue_formatted,
            color: 'bg-cyan-500',
            label: 'Revenue',
          },
          {
            key: 'ni',
            val: Math.max(0, Number(item.net_income) || 0),
            fmt: item.net_income_formatted,
            color: 'bg-emerald-500',
            label: 'Net Income',
          },
        ];
    }
  };

  const maxBarVal = multiYearChart.reduce((max, item) => {
    const r = Number(item.revenue) || 0;
    const ni = Math.max(0, Number(item.net_income) || 0);
    const eb = Number(item.ebitda) || 0;
    if (chartMetric === 'revenue') return Math.max(max, r);
    if (chartMetric === 'net_income') return Math.max(max, ni);
    if (chartMetric === 'ebitda') return Math.max(max, eb);
    return Math.max(max, r, ni);
  }, 1);

  /* 52-week range position (0-100) */
  const range52W = (() => {
    const low = profile.fifty_two_week_low || 0;
    const high = profile.fifty_two_week_high || 1;
    const price = profile.current_price || 0;
    if (high === low) return 50;
    return Math.min(100, Math.max(0, ((price - low) / (high - low)) * 100));
  })();

  /* Profitability metrics */
  const profitMetrics = [
    { label: 'Gross Margin', value: profitability.gross_margin, color: 'bg-blue-500', textColor: 'text-blue-400', benchmark: 30 },
    { label: 'Operating Margin', value: profitability.operating_margin, color: 'bg-cyan-500', textColor: 'text-cyan-400', benchmark: 20 },
    { label: 'Net Profit Margin', value: profitability.net_profit_margin, color: 'bg-emerald-500', textColor: 'text-emerald-400', benchmark: 15 },
    { label: 'Return on Equity', value: profitability.roe, color: 'bg-purple-500', textColor: 'text-purple-400', benchmark: 15 },
    { label: 'Return on Assets', value: profitability.roa, color: 'bg-amber-500', textColor: 'text-amber-400', benchmark: 10 },
  ];

  /* Solvency risk zones */
  const deVal = debtStability.debt_to_equity ?? 0;
  const debtRiskZone =
    deVal < 0.5 ? 'Safe' : deVal < 1.0 ? 'Moderate' : 'Elevated';
  const debtRiskColor =
    debtRiskZone === 'Safe'
      ? 'text-emerald-400'
      : debtRiskZone === 'Moderate'
      ? 'text-amber-400'
      : 'text-red-400';

  const crVal = debtStability.current_ratio ?? 0;
  const liquidityZone =
    crVal >= 2.0
      ? 'Strong'
      : crVal >= 1.5
      ? 'Healthy'
      : crVal >= 1.0
      ? 'Adequate'
      : 'Weak';
  const liquidityColor =
    liquidityZone === 'Strong' || liquidityZone === 'Healthy'
      ? 'text-emerald-400'
      : liquidityZone === 'Adequate'
      ? 'text-amber-400'
      : 'text-red-400';

  /* ════════════════════ RENDER ════════════════════ */
  return (
    <div className="fixed inset-0 z-50 bg-[#090d14] flex flex-col w-screen h-screen overflow-hidden">
      {/* ── Header Bar ── */}
      <div className="flex items-center justify-between px-5 sm:px-8 py-3.5 border-b border-[#172233] bg-[#0b1019] shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#141b25] hover:bg-[#1a2332] text-xs font-semibold text-slate-200 border border-[#222e40] transition-colors"
          >
            <span>← Back to Dashboard</span>
          </button>
          <div className="h-6 w-px bg-[#1c2533] mx-1" />
          <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-base sm:text-lg font-bold text-white">
                {data?.company_name || ticker}
              </h3>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded-md bg-[#162338] text-cyan-400 border border-cyan-500/30">
                {ticker}
              </span>
              {data?.sector && (
                <span className="text-[11px] text-slate-400">
                  • {data.sector}{' '}
                  {data.industry ? `(${data.industry})` : ''}
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-400">
              Fundamental Analysis • Real-Time Financial Statements &amp;
              Valuation Multiples
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {data?.verdict && (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-semibold">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>{data.verdict}</span>
              {data.confidence_score && (
                <span className="text-[10px] text-emerald-400/80 font-mono">
                  ({data.confidence_score})
                </span>
              )}
            </div>
          )}
          <button
            onClick={() => fetchAnalysis(ticker, selectedPeer)}
            title="Refresh Fundamentals"
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-[#1a2638] transition-colors"
          >
            <RefreshCw
              className={`w-4 h-4 ${
                loading ? 'animate-spin text-cyan-400' : ''
              }`}
            />
          </button>
        </div>
      </div>

      {/* ── Content Body ── */}
      <div className="flex-1 overflow-y-auto p-4 sm:p-8 bg-[#090d14]">
        <div className="max-w-7xl mx-auto space-y-6 text-slate-200">
          {/* Mobile Health Verdict */}
          {data?.verdict && (
            <div className="sm:hidden flex items-center justify-between p-3 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-semibold">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                {data.verdict}
              </span>
              {data.confidence_score && (
                <span className="font-mono text-[11px] text-emerald-400">
                  Reliability: {data.confidence_score}
                </span>
              )}
            </div>
          )}

          {/* Missing Data Notification Banner */}
          {missingAudit.notice && !dismissAuditNotice && (
            <div className="p-3.5 sm:p-4 rounded-xl bg-amber-950/25 border border-amber-500/40 flex items-start justify-between gap-3 text-amber-200/90 text-xs sm:text-sm">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-semibold text-amber-300">
                      Data Audit Notice
                    </p>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300/80 border border-amber-500/30 font-medium">
                      Reporting Standard Variation
                    </span>
                  </div>
                  <p className="mt-1 text-amber-100/90 leading-relaxed font-sans">
                    {missingAudit.notice}
                  </p>
                  <p className="mt-1.5 text-[11px] text-amber-300/70 leading-normal">
                    💡 <em>Accounting Note:</em> For Indian IT services companies, technical innovation and development costs are filed under <strong>Employee Benefit Expenses & Technical Subcontractor Costs</strong> rather than a separate standalone US-GAAP &ldquo;R&amp;D&rdquo; line item.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setDismissAuditNotice(true)}
                className="p-1 text-amber-400/80 hover:text-amber-200 hover:bg-amber-900/30 rounded-lg transition-colors shrink-0"
                title="Dismiss Notice"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-red-950/30 border border-red-500/40 text-red-200 text-sm">
              {error}
            </div>
          )}

          {loading && !data && (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-emerald-400" />
              <p className="text-sm">
                Retrieving financial statements and computing fundamental
                ratios...
              </p>
            </div>
          )}

          {data && (
            <>
              {/* ═══════════ 0. COMPANY PROFILE CARD ═══════════ */}
              <div className="p-5 sm:p-6 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm">
                <div className="flex flex-col lg:flex-row gap-5">
                  {/* Left — info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/25 flex items-center justify-center shrink-0">
                        <Building2 className="w-5 h-5 text-cyan-400" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white flex items-center gap-2">
                          Company Overview
                          {profile.exchange && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-[#162338] text-slate-400 border border-[#1e2e44]">
                              {profile.exchange}
                            </span>
                          )}
                        </h4>
                        <p className="text-[11px] text-slate-400">
                          {data.sector} • {data.industry}
                        </p>
                      </div>
                    </div>

                    {/* Business Summary */}
                    {profile.summary && (
                      <div className="mb-3">
                        <p className="text-xs text-slate-300/90 leading-relaxed">
                          {showFullSummary
                            ? profile.summary
                            : profile.summary.length > 200
                            ? profile.summary.slice(0, 200) + '...'
                            : profile.summary}
                        </p>
                        {profile.summary.length > 200 && (
                          <button
                            onClick={() =>
                              setShowFullSummary(!showFullSummary)
                            }
                            className="text-[11px] text-cyan-400 hover:text-cyan-300 mt-1 font-medium"
                          >
                            {showFullSummary ? 'Show less' : 'Read more'}
                          </button>
                        )}
                      </div>
                    )}

                    {/* Quick Stats Row */}
                    <div className="flex flex-wrap gap-3 text-[11px]">
                      {profile.employees && (
                        <span className="flex items-center gap-1 text-slate-400">
                          <Users className="w-3 h-3" />{' '}
                          {profile.employees.toLocaleString()} employees
                        </span>
                      )}
                      {profile.website && (
                        <a
                          href={profile.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-cyan-400 hover:text-cyan-300"
                        >
                          <ExternalLink className="w-3 h-3" /> Website
                        </a>
                      )}
                      {profile.market_cap_formatted && (
                        <span className="flex items-center gap-1 text-slate-400">
                          <Briefcase className="w-3 h-3" /> Market Cap:{' '}
                          <strong className="text-white">
                            {profile.market_cap_formatted}
                          </strong>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Right — Price & 52-Week Range */}
                  <div className="lg:w-72 shrink-0 flex flex-col gap-3">
                    {profile.current_price != null && (
                      <div className="p-4 rounded-xl bg-[#080d15] border border-[#182335]">
                        <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                          Current Price
                        </span>
                        <div className="flex items-baseline gap-1.5 mt-1">
                          <span className="text-2xl font-bold text-white font-mono">
                            {profile.currency_symbol}
                            {profile.current_price.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                          </span>
                        </div>
                      </div>
                    )}

                    {profile.fifty_two_week_low != null &&
                      profile.fifty_two_week_high != null && (
                        <div className="p-4 rounded-xl bg-[#080d15] border border-[#182335]">
                          <span className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">
                            52-Week Range
                          </span>
                          <div className="mt-2.5 relative">
                            <div className="w-full bg-[#1a2638] rounded-full h-2 overflow-hidden">
                              <div
                                className="h-2 rounded-full"
                                style={{
                                  width: `${range52W}%`,
                                  background:
                                    'linear-gradient(90deg, #ef4444 0%, #f59e0b 40%, #10b981 100%)',
                                }}
                              />
                            </div>
                            <div className="flex justify-between text-[10px] mt-1.5 font-mono">
                              <span className="text-red-400">
                                {profile.currency_symbol}
                                {profile.fifty_two_week_low.toLocaleString()}
                              </span>
                              <span className="text-emerald-400">
                                {profile.currency_symbol}
                                {profile.fifty_two_week_high.toLocaleString()}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                  </div>
                </div>
              </div>

              {/* ═══════════ 1 & 2. REVENUE CHART + PROFITABILITY ═══════════ */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                {/* 1. Revenue & Earnings Trajectory */}
                <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm flex flex-col">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-cyan-400" />
                        Revenue &amp; Earnings Trajectory
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Multi-year financial performance ({data.currency})
                      </p>
                    </div>
                    {revEarnings.yoy_growth_rate !== undefined && (
                      <span
                        className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                          revEarnings.yoy_growth_rate >= 0
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25'
                            : 'bg-red-500/10 text-red-400 border-red-500/25'
                        }`}
                      >
                        {revEarnings.yoy_growth_rate >= 0 ? (
                          <span className="flex items-center gap-1">
                            <ArrowUpRight className="w-3 h-3" /> +
                            {revEarnings.yoy_growth_rate}% YoY
                          </span>
                        ) : (
                          <span className="flex items-center gap-1">
                            <ArrowDownRight className="w-3 h-3" />{' '}
                            {revEarnings.yoy_growth_rate}% YoY
                          </span>
                        )}
                      </span>
                    )}
                  </div>

                  {/* Metric Toggle Tabs */}
                  <div className="flex items-center gap-1.5 mb-4 p-1 bg-[#080d15] rounded-lg border border-[#182335] w-fit">
                    {[
                      { key: 'all', label: 'All' },
                      { key: 'revenue', label: 'Revenue' },
                      { key: 'net_income', label: 'Net Income' },
                      { key: 'ebitda', label: 'EBITDA' },
                    ].map((tab) => (
                      <button
                        key={tab.key}
                        onClick={() => setChartMetric(tab.key)}
                        className={`px-3 py-1 text-[11px] font-semibold rounded-md transition-all ${
                          chartMetric === tab.key
                            ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                            : 'text-slate-400 hover:text-slate-200 border border-transparent'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Bar Chart */}
                  <div className="flex-1 pt-2 pb-1">
                    {multiYearChart.length > 0 ? (
                      <div className="flex items-end justify-between gap-3 h-44 px-2 border-b border-[#1f2d42]">
                        {multiYearChart.map((item, idx) => {
                          const bars = getBarData(item);
                          return (
                            <div
                              key={idx}
                              className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group"
                            >
                              <div className="w-full flex items-end justify-center gap-2 h-36">
                                {bars.map((bar) => {
                                  const ratio =
                                    maxBarVal > 0
                                      ? Math.min(1, Math.max(0, bar.val / maxBarVal))
                                      : 0;
                                  const barHeightPx = Math.max(16, Math.round(ratio * 118));
                                  return (
                                    <div
                                      key={bar.key}
                                      className="relative flex flex-col items-center justify-end group/bar"
                                      style={{
                                        width:
                                          bars.length > 1 ? '44%' : '65%',
                                        maxWidth: 42,
                                      }}
                                    >
                                      {/* Value label on hover */}
                                      <span className="text-[9px] font-mono font-bold text-slate-300 mb-1 opacity-0 group-hover:opacity-100 group-hover/bar:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                                        {bar.fmt || formatMoneyVal(bar.val)}
                                      </span>
                                      {/* The visible bar with guaranteed pixel height */}
                                      <div
                                        style={{
                                          height: `${barHeightPx}px`,
                                        }}
                                        className={`w-full rounded-t-md ${bar.color} shadow-md transition-all duration-300 hover:brightness-125 cursor-pointer min-h-[16px]`}
                                        title={`${bar.label} (${item.year}): ${
                                          bar.fmt || formatMoneyVal(bar.val)
                                        }`}
                                      />
                                    </div>
                                  );
                                })}
                              </div>
                              <span className="text-xs font-semibold text-slate-300 font-mono mt-1">
                                {item.year}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="h-44 flex items-center justify-center text-xs text-slate-500">
                        No multi-year data available
                      </div>
                    )}

                    {/* Legend */}
                    <div className="flex items-center gap-4 text-xs text-slate-400 mt-3 pt-2">
                      {(chartMetric === 'all' ||
                        chartMetric === 'revenue') && (
                        <div className="flex items-center gap-1.5">
                          <span className="w-3 h-3 rounded-sm bg-cyan-500 inline-block" />
                          <span>Revenue</span>
                        </div>
                      )}
                      {(chartMetric === 'all' ||
                        chartMetric === 'net_income') && (
                        <div className="flex items-center gap-1.5">
                          <span className="w-3 h-3 rounded-sm bg-emerald-500 inline-block" />
                          <span>Net Income</span>
                        </div>
                      )}
                      {chartMetric === 'ebitda' && (
                        <div className="flex items-center gap-1.5">
                          <span className="w-3 h-3 rounded-sm bg-purple-500 inline-block" />
                          <span>EBITDA</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 2. Profitability Margins */}
                <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm flex flex-col">
                  <div className="mb-4">
                    <h4 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-emerald-400" />
                      Profitability Margins
                    </h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Return metrics and operating efficiencies
                    </p>
                  </div>

                  <div className="space-y-4 flex-1 flex flex-col justify-center">
                    {profitMetrics.map((m, idx) => (
                      <div key={idx}>
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-slate-300 font-medium">
                            {m.label}
                          </span>
                          <div className="flex items-center gap-2">
                            <span
                              className={`font-bold ${m.textColor} font-mono`}
                            >
                              {m.value != null ? `${m.value}%` : 'N/A'}
                            </span>
                            {m.value != null && m.value >= m.benchmark && (
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-semibold">
                                Above avg
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="w-full bg-[#162234] rounded-full h-2.5 overflow-hidden relative">
                          {/* Industry avg benchmark line */}
                          <div
                            className="absolute top-0 bottom-0 w-px bg-slate-500/50 z-10"
                            style={{
                              left: `${Math.min(100, m.benchmark * 2)}%`,
                            }}
                            title={`Industry avg ~${m.benchmark}%`}
                          />
                          <div
                            className={`${m.color} h-2.5 rounded-full transition-all duration-700`}
                            style={{
                              width: `${Math.min(
                                100,
                                Math.max(0, (m.value || 0) * 2)
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* ═══════════ 3. SOLVENCY & FINANCIAL HEALTH ═══════════ */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                {/* Debt-to-Equity Gauge */}
                <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-teal-400" />
                    Debt-to-Equity
                  </h4>
                  <div className="text-center">
                    <span className="text-3xl font-bold text-white font-mono">
                      {debtStability.debt_to_equity ?? 'N/A'}
                    </span>
                    <div className="mt-3 w-full bg-[#162234] rounded-full h-3 overflow-hidden relative">
                      <div
                        className="absolute top-0 bottom-0 left-[33%] w-px bg-amber-500/40"
                        title="Moderate (0.5)"
                      />
                      <div
                        className="absolute top-0 bottom-0 left-[66%] w-px bg-red-500/40"
                        title="Elevated (1.0)"
                      />
                      <div
                        className={`h-3 rounded-full transition-all duration-700 ${
                          debtRiskZone === 'Safe'
                            ? 'bg-emerald-500'
                            : debtRiskZone === 'Moderate'
                            ? 'bg-amber-500'
                            : 'bg-red-500'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, deVal * 66)
                          )}%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-[9px] text-slate-500 mt-1 font-mono">
                      <span>0</span>
                      <span className="text-amber-500/60">0.5</span>
                      <span className="text-red-500/60">1.0</span>
                      <span>1.5+</span>
                    </div>
                    <span
                      className={`text-xs font-semibold mt-2 inline-block ${debtRiskColor}`}
                    >
                      {debtRiskZone} Zone
                    </span>
                  </div>
                </div>

                {/* Current Ratio Gauge */}
                <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5 text-blue-400" />
                    Current Ratio (Liquidity)
                  </h4>
                  <div className="text-center">
                    <span className="text-3xl font-bold text-white font-mono">
                      {crVal ? `${crVal}x` : 'N/A'}
                    </span>
                    <div className="mt-3 w-full bg-[#162234] rounded-full h-3 overflow-hidden relative">
                      <div
                        className="absolute top-0 bottom-0 left-[33%] w-px bg-amber-500/40"
                        title="Adequate (1.0x)"
                      />
                      <div
                        className="absolute top-0 bottom-0 left-[50%] w-px bg-emerald-500/40"
                        title="Healthy (1.5x)"
                      />
                      <div
                        className={`h-3 rounded-full transition-all duration-700 ${
                          liquidityZone === 'Weak'
                            ? 'bg-red-500'
                            : liquidityZone === 'Adequate'
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(5, crVal * 30)
                          )}%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-[9px] text-slate-500 mt-1 font-mono">
                      <span>0</span>
                      <span className="text-amber-500/60">1.0x</span>
                      <span className="text-emerald-500/60">1.5x</span>
                      <span>3.0x+</span>
                    </div>
                    <span
                      className={`text-xs font-semibold mt-2 inline-block ${liquidityColor}`}
                    >
                      {liquidityZone} Liquidity
                    </span>
                  </div>
                </div>

                {/* Solvency Assessment */}
                <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm flex flex-col justify-between">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                    Solvency Assessment
                  </h4>
                  <div className="flex-1 flex flex-col justify-center space-y-4">
                    <div className="p-3.5 rounded-xl bg-[#080d15] border border-[#182335]">
                      <span className="text-[10px] text-slate-500 block">
                        Operating Cash Flow
                      </span>
                      <span className="text-base font-bold text-white font-mono">
                        {debtStability.operating_cash_flow
                          ? formatMoneyVal(debtStability.operating_cash_flow)
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="p-3.5 rounded-xl bg-[#080d15] border border-[#182335]">
                      <span className="text-[10px] text-slate-500 block">
                        Overall Verdict
                      </span>
                      <span className="text-sm font-bold text-emerald-400">
                        {debtStability.solvency_assessment || 'Safe Solvency'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* ═══════════ 4. VALUATION MULTIPLES ═══════════ */}
              <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm">
                <h4 className="text-sm sm:text-base font-bold text-white mb-3.5 flex items-center gap-2">
                  <Scale className="w-4 h-4 text-purple-400" />
                  Valuation Multiples &amp; Efficiency Metrics
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  {[
                    {
                      label: 'P/E Ratio',
                      value: valuation.pe_ratio
                        ? `${valuation.pe_ratio}x`
                        : 'N/A',
                      sub: 'TTM Multiple',
                      color: 'text-cyan-400',
                    },
                    {
                      label: 'P/B Ratio',
                      value: valuation.pb_ratio
                        ? `${valuation.pb_ratio}x`
                        : 'N/A',
                      sub: 'Price / Book',
                      color: 'text-cyan-400',
                    },
                    {
                      label: 'EPS',
                      value: valuation.eps
                        ? `${currSym}${valuation.eps}`
                        : 'N/A',
                      sub: 'Per Share',
                      color: 'text-emerald-400',
                    },
                    {
                      label: 'Return on Assets',
                      value: profitability.roa
                        ? `${profitability.roa}%`
                        : 'N/A',
                      sub: 'Asset Efficiency',
                      color: 'text-purple-400',
                    },
                    {
                      label: 'Gross Margin',
                      value: profitability.gross_margin
                        ? `${profitability.gross_margin}%`
                        : 'N/A',
                      sub: 'Gross Revenue',
                      color: 'text-emerald-400',
                    },
                    {
                      label: 'Solvency',
                      value: debtStability.solvency_assessment
                        ? debtStability.solvency_assessment
                            .split('/')[0]
                            .trim()
                        : 'Safe',
                      sub: 'Balance Sheet',
                      color: 'text-teal-300',
                      small: true,
                    },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-xl bg-[#080d15] border border-[#182335]"
                    >
                      <span className="text-[11px] text-slate-400 block">
                        {item.label}
                      </span>
                      <span
                        className={`${
                          item.small ? 'text-xs' : 'text-base'
                        } font-bold ${
                          item.color
                        } font-mono block mt-0.5 truncate`}
                      >
                        {item.value}
                      </span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">
                        {item.sub}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* ═══════════ 5. PEER COMPARISON ═══════════ */}
              <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-[#182436] mb-4">
                  <div>
                    <h4 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                      <Users className="w-4 h-4 text-cyan-400" />
                      Peer Benchmarking &amp; Comparison
                    </h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Benchmark {ticker} metrics against industry competitors
                    </p>
                  </div>

                  {/* Peer Selector Dropdown */}
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <label className="text-xs font-medium text-slate-300 shrink-0">
                      Select Peer:
                    </label>
                    <select
                      value={showCustomPeer ? 'CUSTOM' : selectedPeer}
                      onChange={(e) => handlePeerChange(e.target.value)}
                      className="bg-[#090e17] border border-cyan-500/40 text-cyan-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-medium"
                    >
                      {peerComp.available_peers?.map((p) => (
                        <option key={p.ticker} value={p.ticker}>
                          {p.ticker} — {p.name}
                        </option>
                      ))}
                      <option value="CUSTOM">+ Custom Peer Search...</option>
                    </select>
                  </div>
                </div>

                {/* Custom Peer: Dual Search Autocomplete */}
                {showCustomPeer && (
                  <div className="mb-4 relative" ref={peerSearchRef}>
                    <div className="flex items-center gap-2 p-3 rounded-xl bg-[#080d15] border border-cyan-500/30">
                      <Search className="w-4 h-4 text-cyan-400 shrink-0" />
                      <input
                        type="text"
                        placeholder="Search company name or ticker (e.g. Apple, MSFT, TCS.NS)..."
                        value={peerSearchQuery}
                        onChange={(e) =>
                          handlePeerSearchInput(e.target.value)
                        }
                        onFocus={() => {
                          if (peerSearchQuery.trim())
                            setShowPeerDropdown(true);
                        }}
                        className="bg-transparent border-none text-xs text-white placeholder-slate-500 focus:outline-none flex-1"
                        autoFocus
                      />
                      {peerSearchLoading && (
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                      )}
                    </div>

                    {/* Autocomplete Dropdown */}
                    {showPeerDropdown && peerSuggestions.length > 0 && (
                      <div className="absolute top-full left-0 right-0 mt-1 bg-[#0c1220] border border-cyan-500/30 rounded-xl shadow-2xl z-20 max-h-64 overflow-y-auto">
                        {peerSuggestions.map((s, idx) => (
                          <button
                            key={`${s.ticker}-${idx}`}
                            onClick={() =>
                              handleSelectPeerSuggestion(s)
                            }
                            className="w-full text-left px-4 py-2.5 hover:bg-cyan-500/10 transition-colors flex items-center justify-between gap-3 border-b border-[#162338] last:border-b-0"
                          >
                            <div className="flex items-center gap-2.5">
                              <span className="text-xs font-bold font-mono text-cyan-400 w-20 shrink-0">
                                {s.ticker}
                              </span>
                              <span className="text-xs text-slate-300 truncate">
                                {s.name}
                              </span>
                            </div>
                            <span className="text-[10px] text-slate-500 shrink-0 font-mono">
                              {s.exchange}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                    {showPeerDropdown &&
                      peerSearchQuery.trim() &&
                      peerSuggestions.length === 0 &&
                      !peerSearchLoading && (
                        <div className="absolute top-full left-0 right-0 mt-1 bg-[#0c1220] border border-[#182335] rounded-xl p-4 text-xs text-slate-400 text-center">
                          No results found for &ldquo;{peerSearchQuery}&rdquo;
                        </div>
                      )}
                  </div>
                )}

                {/* Peer Comparison Narrative */}
                {peerComp.narrative && (
                  <div className="p-4 rounded-xl bg-[#080d15] border border-[#182335] mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-4 h-4 text-cyan-400 shrink-0" />
                      <span className="text-xs font-bold text-cyan-400 uppercase tracking-wider">
                        Competitive Analysis
                      </span>
                    </div>
                    <p className="text-xs text-slate-300/90 leading-relaxed">
                      {peerComp.narrative}
                    </p>
                  </div>
                )}

                {/* Visual Comparative Bars */}
                {peerComp.comparison_table?.length > 0 && (
                  <div className="space-y-4 mb-4">
                    {peerComp.comparison_table.map((row, idx) => {
                      const targetNum = parseFloat(row.target_val) || 0;
                      const peerNum = parseFloat(row.peer_val) || 0;
                      const maxVal = Math.max(
                        Math.abs(targetNum),
                        Math.abs(peerNum),
                        0.01
                      );
                      const targetWidth =
                        (Math.abs(targetNum) / maxVal) * 100;
                      const peerWidth =
                        (Math.abs(peerNum) / maxVal) * 100;
                      const isTargetBetter =
                        row.standing?.includes('Outperforming') ||
                        row.standing?.includes('Favorable');

                      return (
                        <div
                          key={idx}
                          className="p-3.5 rounded-xl bg-[#080d15] border border-[#182335]"
                        >
                          <div className="flex items-center justify-between mb-2.5">
                            <span className="text-xs font-semibold text-slate-200">
                              {row.metric}
                            </span>
                            <span
                              className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                isTargetBetter
                                  ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                  : 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                              }`}
                            >
                              {isTargetBetter ? (
                                <Award className="w-3 h-3" />
                              ) : null}
                              {row.standing?.split('(')[0]?.trim()}
                            </span>
                          </div>

                          {/* Target bar */}
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="text-[10px] text-cyan-400 font-mono w-20 shrink-0 truncate">
                              {ticker}
                            </span>
                            <div className="flex-1 bg-[#162234] rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-cyan-500 h-2 rounded-full transition-all duration-500"
                                style={{
                                  width: `${Math.max(4, targetWidth)}%`,
                                }}
                              />
                            </div>
                            <span className="text-[11px] font-bold text-white font-mono w-16 text-right">
                              {row.target_val}
                            </span>
                          </div>

                          {/* Peer bar */}
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-purple-400 font-mono w-20 shrink-0 truncate">
                              {peerComp.peer_name || selectedPeer}
                            </span>
                            <div className="flex-1 bg-[#162234] rounded-full h-2 overflow-hidden">
                              <div
                                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                                style={{
                                  width: `${Math.max(4, peerWidth)}%`,
                                }}
                              />
                            </div>
                            <span className="text-[11px] font-medium text-slate-300 font-mono w-16 text-right">
                              {row.peer_val}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Tabular Comparison */}
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-[#1b273a] text-slate-400 font-semibold">
                        <th className="py-2.5 px-3">Metric</th>
                        <th className="py-2.5 px-3 text-cyan-400">
                          {ticker} (Target)
                        </th>
                        <th className="py-2.5 px-3 text-purple-400">
                          {peerComp.peer_name || selectedPeer}
                        </th>
                        <th className="py-2.5 px-3">Competitive Standing</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#141d2c]">
                      {peerComp.comparison_table?.map((row, idx) => (
                        <tr
                          key={idx}
                          className="hover:bg-[#121c2d]/50 transition-colors"
                        >
                          <td className="py-2.5 px-3 font-medium text-slate-200">
                            {row.metric}
                          </td>
                          <td className="py-2.5 px-3 font-bold text-white font-mono">
                            {row.target_val}
                          </td>
                          <td className="py-2.5 px-3 font-medium text-slate-300 font-mono">
                            {row.peer_val}
                          </td>
                          <td className="py-2.5 px-3">
                            <span
                              className="inline-flex items-center gap-1 font-semibold text-[11px]"
                              style={{
                                color: row.standing_color || '#10b981',
                              }}
                            >
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              {row.standing}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* ═══════════ 6. HISTORICAL FINANCIAL STATEMENTS ═══════════ */}
              {multiYearChart.length > 0 && (
                <div className="p-5 rounded-2xl bg-[#0e1624] border border-[#1b273a] shadow-sm space-y-4">
                  <div>
                    <h4 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-emerald-400" />
                      Historical Financial Statements Breakdown
                    </h4>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Multi-year revenue, profit, EBITDA, and operational
                      cash flows ({data.currency})
                    </p>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-[#1b273a] text-slate-400 font-semibold">
                          <th className="py-2.5 px-3">Fiscal Year</th>
                          <th className="py-2.5 px-3">Total Revenue</th>
                          <th className="py-2.5 px-3">Net Income</th>
                          <th className="py-2.5 px-3">EBITDA</th>
                          <th className="py-2.5 px-3">
                            Operating Cash Flow
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#141d2c]">
                        {multiYearChart.map((yr, idx) => (
                          <tr
                            key={idx}
                            className="hover:bg-[#121c2d]/50 transition-colors font-mono"
                          >
                            <td className="py-2.5 px-3 font-bold text-cyan-400">
                              {yr.year}
                            </td>
                            <td className="py-2.5 px-3 text-slate-200">
                              {yr.revenue_formatted ||
                                formatMoneyVal(yr.revenue)}
                            </td>
                            <td className="py-2.5 px-3 text-emerald-400 font-semibold">
                              {yr.net_income_formatted ||
                                formatMoneyVal(yr.net_income)}
                            </td>
                            <td className="py-2.5 px-3 text-slate-300">
                              {yr.ebitda_formatted ||
                                formatMoneyVal(yr.ebitda)}
                            </td>
                            <td className="py-2.5 px-3 text-cyan-300">
                              {yr.operating_cash_flow_formatted ||
                                formatMoneyVal(yr.operating_cash_flow)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Year-over-Year Growth */}
                  {historicalGrowth.length > 0 && (
                    <div className="pt-3 border-t border-[#162234]">
                      <h5 className="text-xs font-bold text-slate-300 mb-2.5 flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
                        Year-over-Year Performance Trajectory
                      </h5>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                        {historicalGrowth.map((g, idx) => (
                          <div
                            key={idx}
                            className="p-3 rounded-xl bg-[#090e17] border border-[#1a283c] flex items-center justify-between"
                          >
                            <div>
                              <span className="text-[11px] font-mono text-cyan-400 font-bold block">
                                {g.period}
                              </span>
                              <span className="text-[10px] text-slate-400 block mt-0.5">
                                {g.status}
                              </span>
                            </div>
                            <div className="text-right">
                              <span
                                className={`text-xs font-mono font-bold ${
                                  g.revenue_growth?.startsWith('+')
                                    ? 'text-emerald-400'
                                    : 'text-red-400'
                                }`}
                              >
                                {g.revenue_growth}
                              </span>
                              <span className="text-[9px] text-slate-500 block">
                                Revenue YoY
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ── Footer Bar ── */}
      <div className="px-6 py-3 border-t border-[#172233] bg-[#0a0f18] flex items-center justify-between text-xs text-slate-400 shrink-0">
        <div className="flex items-center gap-2">
          <span>Fundamental Analysis • {ticker}</span>
        </div>
      </div>
    </div>
  );
};

export default FundamentalAnalysisModal;
