import React, { useState, useEffect, useRef } from 'react';
import {
  Layers,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  BarChart3,
  DollarSign,
  ShieldAlert,
  Loader2,
  Sparkles,
  Plus,
  X,
  Target,
  Building2,
  MessageSquare,
  Shield,
  Info,
} from 'lucide-react';
import { api } from '../api/client';
import StockLogo from './StockLogo';

export default function CompareView({ onSelectReport }) {
  const [completedSessions, setCompletedSessions] = useState([]);
  const [selectedSessionIds, setSelectedSessionIds] = useState([]);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('implied_upside');

  // Comparison metrics catalog for interactive cross-stock visualization
  const COMPARISON_METRICS = [
    { id: 'implied_upside', label: 'Implied Return', unit: '%', desc: '12-Month consensus price target vs current price' },
    { id: 'confidence', label: 'Confidence Level', unit: '%', desc: 'Consensus committee confidence score across 5 agents' },
    { id: 'pe_ratio', label: 'Trailing P/E', unit: 'x', desc: 'Price to trailing 12-month earnings multiple' },
    { id: 'forward_pe', label: 'Forward P/E', unit: 'x', desc: 'Price to forward 12-month projected earnings multiple' },
    { id: 'rsi_14', label: 'RSI-14 Momentum', unit: '', desc: 'Relative Strength Index (30 Oversold / 70 Overbought)' },
    { id: 'profit_margin', label: 'Profit Margin', unit: '%', desc: 'Net profit as a percentage of total revenue' },
    { id: 'operating_margin', label: 'Operating Margin', unit: '%', desc: 'Operating income as a percentage of total revenue' },
    { id: 'risk_score', label: 'Risk Severity', unit: '/ 10', desc: 'Stress-test risk score (0 Minimal to 10 Critical)' },
  ];

  // Helper to extract numeric and display values for any comparative metric
  const getMetricValue = (item, metricId) => {
    switch (metricId) {
      case 'implied_upside': {
        const val = item.implied_upside_percent;
        return {
          numeric: val != null ? Number(val) : null,
          display: val != null ? `${val > 0 ? '+' : ''}${val}%` : 'Unavailable',
        };
      }
      case 'confidence': {
        const val = item.confidence_score;
        return {
          numeric: val != null ? Math.round(val * 100) : null,
          display: val != null ? `${Math.round(val * 100)}%` : 'Unavailable',
        };
      }
      case 'pe_ratio': {
        const val = item.pe_ratio;
        return {
          numeric: val != null ? Number(val) : null,
          display: val != null ? `${Number(val).toFixed(1)}x` : 'Unavailable',
        };
      }
      case 'forward_pe': {
        const val = item.forward_pe;
        return {
          numeric: val != null ? Number(val) : null,
          display: val != null ? `${Number(val).toFixed(1)}x` : 'Unavailable',
        };
      }
      case 'rsi_14': {
        const val = item.rsi_14;
        return {
          numeric: val != null ? Number(val) : null,
          display: val != null ? `${Number(val).toFixed(1)}` : 'Unavailable',
        };
      }
      case 'profit_margin': {
        const raw = item.profit_margins;
        if (raw == null) return { numeric: null, display: 'Unavailable' };
        const val = Math.abs(raw) <= 1 ? raw * 100 : raw;
        return {
          numeric: Number(val),
          display: `${val.toFixed(1)}%`,
        };
      }
      case 'operating_margin': {
        const raw = item.operating_margins;
        if (raw == null) return { numeric: null, display: 'Unavailable' };
        const val = Math.abs(raw) <= 1 ? raw * 100 : raw;
        return {
          numeric: Number(val),
          display: `${val.toFixed(1)}%`,
        };
      }
      case 'risk_score': {
        const val = item.risk_score;
        return {
          numeric: val != null ? Number(val) : null,
          display: val != null ? `${Number(val).toFixed(1)} / 10` : 'Unavailable',
        };
      }
      default:
        return { numeric: null, display: 'Unavailable' };
    }
  };

  // Add stock dropdown state
  const [isAddMenuOpen, setIsAddMenuOpen] = useState(false);
  const addMenuRef = useRef(null);

  // Load user's completed sessions
  useEffect(() => {
    fetchCompletedSessions();
  }, []);

  // Close add dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (addMenuRef.current && !addMenuRef.current.contains(e.target)) {
        setIsAddMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchCompletedSessions = async () => {
    setLoadingSessions(true);
    setError(null);
    try {
      const data = await api.listSessions(100, 0);
      const completed = (data.sessions || []).filter((s) => s.status === 'COMPLETED');
      setCompletedSessions(completed);

      // Pre-select first 2 distinct ticker sessions if available
      if (completed.length >= 2 && selectedSessionIds.length === 0) {
        // Find 2 sessions with distinct tickers if possible
        const distinct = [];
        const seenTickers = new Set();
        for (const s of completed) {
          if (!seenTickers.has(s.ticker)) {
            seenTickers.add(s.ticker);
            distinct.push(s.id);
          }
          if (distinct.length === 2) break;
        }

        const initial = distinct.length === 2 ? distinct : [completed[0].id, completed[1].id];
        setSelectedSessionIds(initial);
        runComparison(initial);
      } else if (completed.length === 1) {
        setSelectedSessionIds([completed[0].id]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load completed research sessions.');
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleAddStock = (sessionId) => {
    if (selectedSessionIds.includes(sessionId)) return;
    if (selectedSessionIds.length >= 5) {
      setError('You can compare a maximum of 5 stocks simultaneously.');
      return;
    }
    const updated = [...selectedSessionIds, sessionId];
    setSelectedSessionIds(updated);
    setIsAddMenuOpen(false);
    if (updated.length >= 2) {
      runComparison(updated);
    }
  };

  const handleRemoveStock = (sessionId) => {
    const updated = selectedSessionIds.filter((id) => id !== sessionId);
    setSelectedSessionIds(updated);
    if (updated.length >= 2) {
      runComparison(updated);
    } else {
      setComparisonResult(null);
    }
  };

  const runComparison = async (ids = selectedSessionIds) => {
    if (ids.length < 2) {
      setError('Please select at least 2 completed stock sessions to compare.');
      return;
    }
    if (ids.length > 5) {
      setError('You can compare up to 5 stocks at once.');
      return;
    }

    setComparing(true);
    setError(null);

    try {
      const result = await api.compareStocks(ids);
      setComparisonResult(result);
    } catch (err) {
      setError(err.message || 'Comparison analysis failed.');
    } finally {
      setComparing(false);
    }
  };

  // Color palette for compared stocks (matching screenshot)
  const stockColors = [
    {
      name: 'lime',
      dot: 'bg-[#C5F500]',
      stroke: '#82CB00',
      fillStart: 'rgba(197, 245, 0, 0.40)',
      fillEnd: 'rgba(197, 245, 0, 0.02)',
      badge: 'bg-[#C5F500]/25 text-[#111318]',
    },
    {
      name: 'purple',
      dot: 'bg-[#8B5CF6]',
      stroke: '#8B5CF6',
      fillStart: 'rgba(139, 92, 246, 0.35)',
      fillEnd: 'rgba(139, 92, 246, 0.02)',
      badge: 'bg-purple-50 text-purple-700',
    },
    {
      name: 'blue',
      dot: 'bg-[#3B82F6]',
      stroke: '#3B82F6',
      fillStart: 'rgba(59, 130, 246, 0.35)',
      fillEnd: 'rgba(59, 130, 246, 0.02)',
      badge: 'bg-blue-50 text-blue-700',
    },
    {
      name: 'orange',
      dot: 'bg-[#F97316]',
      stroke: '#F97316',
      fillStart: 'rgba(249, 115, 22, 0.35)',
      fillEnd: 'rgba(249, 115, 22, 0.02)',
      badge: 'bg-orange-50 text-orange-700',
    },
    {
      name: 'rose',
      dot: 'bg-[#EC4899]',
      stroke: '#EC4899',
      fillStart: 'rgba(236, 72, 153, 0.35)',
      fillEnd: 'rgba(236, 72, 153, 0.02)',
      badge: 'bg-pink-50 text-pink-700',
    },
  ];

  // Helper to map category name to lucide icon
  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Consensus':
        return <Target className="w-4 h-4 text-gray-500" />;
      case 'Classification':
        return <Building2 className="w-4 h-4 text-gray-500" />;
      case 'Valuation':
        return <BarChart3 className="w-4 h-4 text-gray-500" />;
      case 'Technicals':
        return <TrendingUp className="w-4 h-4 text-gray-500" />;
      case 'Sentiment':
        return <MessageSquare className="w-4 h-4 text-gray-500" />;
      case 'Risk':
        return <Shield className="w-4 h-4 text-gray-500" />;
      default:
        return <Layers className="w-4 h-4 text-gray-500" />;
    }
  };

  // Generate dynamic key takeaways from genuine comparison items
  const generateKeyTakeaways = (items) => {
    if (!items || items.length === 0) return [];
    const takeaways = [];

    // Sort by implied upside
    const validUpsides = items.filter((it) => it.implied_upside_percent !== null);
    if (validUpsides.length > 0) {
      const sorted = [...validUpsides].sort(
        (a, b) => (b.implied_upside_percent || 0) - (a.implied_upside_percent || 0)
      );
      const top = sorted[0];
      const sign = (top.implied_upside_percent || 0) >= 0 ? '+' : '';
      takeaways.push(
        `${top.ticker} shows higher upside potential (${sign}${top.implied_upside_percent}%) with a ${top.recommendation.replace('_', ' ')} consensus.`
      );

      if (sorted.length > 1) {
        const second = sorted[1];
        const sSign = (second.implied_upside_percent || 0) >= 0 ? '+' : '';
        takeaways.push(
          `${second.ticker} remains a ${second.recommendation.replace('_', ' ')} with a steady upside of ${sSign}${second.implied_upside_percent}%.`
        );
      }
    }

    // Valuation status takeaway
    const valuations = [...new Set(items.map((it) => it.valuation_status).filter(Boolean))];
    if (valuations.length === 1 && valuations[0] === 'FAIRLY_VALUED') {
      takeaways.push('Both stocks are fairly valued based on current fundamentals.');
    } else if (valuations.includes('UNDERVALUED')) {
      const undervalued = items.filter((it) => it.valuation_status === 'UNDERVALUED');
      takeaways.push(
        `${undervalued.map((it) => it.ticker).join(', ')} identified as undervalued relative to cash flow and book value.`
      );
    } else {
      takeaways.push('Valuation metrics reflect balanced risk-reward across current multiples.');
    }

    // Risk / Solvency summary
    const lowSolvencyRisk = items.filter((it) => it.solvency_risk === 'LOW');
    if (lowSolvencyRisk.length === items.length) {
      takeaways.push('All compared assets maintain strong solvency health and balance sheet reserves.');
    }

    return takeaways.slice(0, 3);
  };

  // Sessions available to add (not yet selected)
  const availableToAdd = completedSessions.filter(
    (s) => !selectedSessionIds.includes(s.id)
  );

  return (
    <div className="space-y-6 sm:space-y-7 animate-fadeIn">
      {/* Stock Selection Bar matching Reference Screenshot 4 */}
      <div className="p-4 sm:p-5 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2.5">
          <span className="text-xs font-black text-[#111318] mr-1">
            Select Stocks to Compare (2 to 5)
          </span>

          {/* Selected Stock Chips */}
          {selectedSessionIds.map((sid) => {
            const session = completedSessions.find((s) => s.id === sid);
            const ticker = session ? session.ticker : `#${sid}`;
            const company = session ? session.company_name : '';

            return (
              <span
                key={sid}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#1A3C2B] text-white text-xs font-bold shadow-2xs"
              >
                <span className="text-[#C5F500] font-black">{ticker}</span>
                {company && (
                  <span className="text-gray-300 text-[11px] max-w-[140px] truncate font-normal">
                    {company}
                  </span>
                )}
                <button
                  onClick={() => handleRemoveStock(sid)}
                  className="hover:text-[#C5F500] text-gray-400 cursor-pointer ml-0.5"
                  title="Remove stock"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            );
          })}

          {/* + Add Stock Button with Dropdown */}
          <div className="relative" ref={addMenuRef}>
            <button
              onClick={() => setIsAddMenuOpen(!isAddMenuOpen)}
              disabled={selectedSessionIds.length >= 5}
              className="h-8 px-3.5 rounded-full bg-white border border-gray-200/90 hover:bg-gray-50 active:scale-95 text-[#111318] text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-2xs disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Plus className="w-3.5 h-3.5 text-[#111318]" />
              <span>Add Stock</span>
            </button>

            {/* Dropdown Menu */}
            {isAddMenuOpen && (
              <div className="absolute left-0 top-10 z-40 w-72 bg-white rounded-2xl shadow-xl border border-gray-100 p-2 space-y-1 animate-fadeIn">
                <div className="px-3 py-1.5 border-b border-gray-100">
                  <span className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Available Completed Stocks
                  </span>
                </div>

                {availableToAdd.length === 0 ? (
                  <div className="p-3 text-center text-xs text-gray-400">
                    No other completed sessions available to add.
                  </div>
                ) : (
                  <div className="max-h-56 overflow-y-auto space-y-0.5">
                    {availableToAdd.map((s) => (
                      <button
                        key={s.id}
                        onClick={() => handleAddStock(s.id)}
                        className="w-full px-3 py-2 rounded-xl text-left hover:bg-gray-50 flex items-center justify-between transition cursor-pointer group"
                      >
                        <div className="flex items-center gap-2.5">
                          <StockLogo ticker={s.ticker} size="xs" />
                          <div>
                            <span className="font-mono font-black text-xs text-[#111318] block">
                              {s.ticker}
                            </span>
                            <span className="text-[10px] text-gray-400 block truncate max-w-[140px]">
                              {s.company_name}
                            </span>
                          </div>
                        </div>
                        <span className="text-[11px] font-bold text-emerald-700 opacity-0 group-hover:opacity-100 transition">
                          + Add
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Selected Counter */}
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs font-extrabold text-gray-500">
            Selected: <strong className="text-[#111318]">{selectedSessionIds.length}</strong> / 5
          </span>
          {comparing && (
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#111318]">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#17191F]" />
              <span>Updating...</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* When fewer than 2 stocks selected */}
      {selectedSessionIds.length < 2 && (
        <div className="p-12 rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-gray-100 text-gray-400 mx-auto flex items-center justify-center">
            <Layers className="w-6 h-6" />
          </div>
          <h4 className="text-base font-black text-[#111318]">
            Select at least 2 stocks to compare
          </h4>
          <p className="text-xs text-gray-500 max-w-md mx-auto leading-relaxed">
            Choose 2 to 5 completed equity research dossiers from your library above to generate the side-by-side multi-agent comparison matrix and relative performance charts.
          </p>
        </div>
      )}

      {/* Stock Summary Cards Row */}
      {comparisonResult && comparisonResult.items && (
        <div className="space-y-6 sm:space-y-7">
          {/* Overview Cards Grid */}
          <div
            className={`grid grid-cols-1 gap-4 sm:gap-5 ${
              comparisonResult.items.length === 2
                ? 'md:grid-cols-2'
                : comparisonResult.items.length === 3
                ? 'md:grid-cols-3'
                : 'md:grid-cols-2 lg:grid-cols-4'
            }`}
          >
            {comparisonResult.items.map((item, idx) => {
              const isStrongBuy = item.recommendation === 'STRONG_BUY';
              const isBuy = item.recommendation === 'BUY';
              const isSell = item.recommendation === 'SELL' || item.recommendation === 'STRONG_SELL';

              const colorToken = stockColors[idx % stockColors.length];

              return (
                <div
                  key={item.session_id}
                  className="p-5 sm:p-6 rounded-[24px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] space-y-4 flex flex-col justify-between relative overflow-hidden"
                >
                  <div>
                    {/* Header: Logo, Ticker, Name, Rating */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <StockLogo ticker={item.ticker} size="lg" />
                        <div>
                          <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                            {item.ticker}
                          </h3>
                          <p className="text-xs text-gray-500 font-medium truncate max-w-[150px]">
                            {item.company_name}
                          </p>
                        </div>
                      </div>

                      {/* Rating Pill */}
                      <span
                        className={`text-xs font-black px-3 py-1 rounded-full whitespace-nowrap ${
                          isStrongBuy || isBuy
                            ? 'bg-[#C5F500]/25 text-[#111318] border border-[#C5F500]/60'
                            : isSell
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-amber-50 text-amber-700 border border-amber-200'
                        }`}
                      >
                        {item.recommendation.replace('_', ' ')}
                      </span>
                    </div>

                    {/* 4 Metrics: Price, Target, Implied, Confidence */}
                    <div className="grid grid-cols-4 gap-2 pt-5 border-t border-gray-100 mt-4 text-left">
                      <div>
                        <span className="text-[11px] font-bold text-gray-400 block">Price</span>
                        <span className="text-sm sm:text-base font-black text-[#111318] block mt-0.5">
                          {item.current_price !== null ? `$${item.current_price.toFixed(2)}` : 'Unavailable'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[11px] font-bold text-gray-400 block">Target</span>
                        <span className="text-sm sm:text-base font-black text-[#111318] block mt-0.5">
                          {item.target_price !== null ? `$${item.target_price.toFixed(2)}` : 'Unavailable'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[11px] font-bold text-gray-400 block">Implied</span>
                        <span
                          className={`text-sm sm:text-base font-black block mt-0.5 ${
                            item.implied_upside_percent !== null && item.implied_upside_percent >= 0
                              ? 'text-emerald-600'
                              : item.implied_upside_percent !== null
                              ? 'text-rose-600'
                              : 'text-gray-400 font-normal italic text-xs'
                          }`}
                        >
                          {item.implied_upside_percent !== null
                            ? `${item.implied_upside_percent > 0 ? '+' : ''}${item.implied_upside_percent}%`
                            : 'Unavailable'}
                        </span>
                      </div>

                      <div>
                        <span className="text-[11px] font-bold text-gray-400 block">Confidence</span>
                        <span className="text-sm sm:text-base font-black text-[#111318] block mt-0.5">
                          {Math.round(item.confidence_score * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* View Dossier Button */}
                  <div className="pt-2">
                    <button
                      onClick={() => onSelectReport(item.session_id)}
                      className="w-full h-9 rounded-xl bg-gray-50 hover:bg-[#17191F] hover:text-white text-[#111318] text-xs font-black transition flex items-center justify-center gap-1.5 cursor-pointer border border-gray-200/70 shadow-2xs group"
                    >
                      <span>View Dossier</span>
                      <ArrowRight className="w-3.5 h-3.5 transition group-hover:translate-x-0.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Split Section: Matrix on Left (60%), Performance & Takeaways on Right (40%) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* LEFT: Side-by-Side Multi-Agent Metric Matrix */}
            <div className="lg:col-span-7 rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 space-y-5 overflow-hidden">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0 mt-0.5">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                    Side-by-Side Multi-Agent Metric Matrix
                  </h3>
                  <p className="text-xs text-gray-500 font-medium">
                    Direct cross-comparison across valuation multiples, momentum, sentiment, and risk
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto -mx-6 sm:-mx-7 px-6 sm:px-7">
                <table className="w-full text-left text-xs sm:text-sm border-collapse min-w-[550px]">
                  <thead>
                    <tr className="border-b border-gray-100 text-[11px] font-black text-gray-400 uppercase tracking-wider">
                      <th className="pb-3 px-3 w-28">Category</th>
                      <th className="pb-3 px-3 w-40">Metric</th>
                      {comparisonResult.items.map((it) => (
                        <th
                          key={it.ticker}
                          className="pb-3 px-3 text-center font-mono font-black text-sm text-[#111318]"
                        >
                          {it.ticker}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100/80">
                    {comparisonResult.matrix.map((row, idx) => {
                      return (
                        <tr
                          key={idx}
                          className="hover:bg-gray-50/60 transition-colors"
                        >
                          {/* Category with Icon */}
                          <td className="py-2.5 px-3">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-gray-400">
                              {getCategoryIcon(row.category)}
                              <span className="hidden sm:inline">{row.category}</span>
                            </div>
                          </td>

                          {/* Metric Name */}
                          <td className="py-2.5 px-3 font-bold text-xs sm:text-sm text-[#111318]">
                            {row.metric}
                          </td>

                          {/* Stock Values */}
                          {comparisonResult.items.map((it) => {
                            const val = row.values[it.ticker];
                            const isMissing = val === null || val === undefined || val === '' || val === '—';
                            const displayVal = !isMissing ? String(val) : 'Unavailable';

                            // Conditional badge styling for ratings & states
                            const isPositive =
                              displayVal === 'STRONG_BUY' ||
                              displayVal === 'BUY' ||
                              displayVal === 'BULLISH' ||
                              displayVal === 'UNDERVALUED';

                            const isNegative =
                              displayVal === 'SELL' ||
                              displayVal === 'STRONG_SELL' ||
                              displayVal === 'BEARISH' ||
                              displayVal === 'OVERVALUED';

                            const isNeutral =
                              displayVal === 'HOLD' ||
                              displayVal === 'FAIRLY_VALUED' ||
                              displayVal === 'NEUTRAL';

                            return (
                              <td
                                key={it.ticker}
                                className="py-2.5 px-3 text-center font-medium text-xs sm:text-sm"
                              >
                                {isMissing ? (
                                  <span className="text-gray-400 font-normal italic text-xs">
                                    Unavailable
                                  </span>
                                ) : isPositive ? (
                                  <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-black bg-[#C5F500]/25 text-[#111318] border border-[#C5F500]/50">
                                    {displayVal.replace('_', ' ')}
                                  </span>
                                ) : isNegative ? (
                                  <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-50 text-rose-700 border border-rose-200">
                                    {displayVal.replace('_', ' ')}
                                  </span>
                                ) : isNeutral ? (
                                  <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-100 text-gray-700 border border-gray-200/60">
                                    {displayVal.replace('_', ' ')}
                                  </span>
                                ) : (
                                  <span
                                    className={`font-semibold ${
                                      displayVal.startsWith('+')
                                        ? 'text-emerald-600 font-black'
                                        : displayVal.startsWith('-') && displayVal.endsWith('%')
                                        ? 'text-rose-600 font-black'
                                        : 'text-[#111318]'
                                    }`}
                                  >
                                    {displayVal}
                                  </span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* RIGHT: Performance Comparison & Key Takeaways */}
            <div className="lg:col-span-5 space-y-6">
              {/* Card 1: Multi-Metric Comparative Visualization */}
              <div className="rounded-[26px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-5 sm:p-6 space-y-4">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#111318]" />
                    <h4 className="text-sm font-black text-[#111318]">
                      Performance & Metric Comparison
                    </h4>
                  </div>

                  {/* Metric Selector Dropdown */}
                  <select
                    value={selectedMetric}
                    onChange={(e) => setSelectedMetric(e.target.value)}
                    className="h-8 px-2.5 rounded-xl bg-gray-50 border border-gray-200 text-xs font-bold text-[#111318] focus:outline-none focus:ring-2 focus:ring-[#C5F500] cursor-pointer"
                  >
                    {COMPARISON_METRICS.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Metric Description */}
                <p className="text-[11px] text-gray-500 font-medium">
                  {COMPARISON_METRICS.find((m) => m.id === selectedMetric)?.desc}
                </p>

                {/* Stock Horizontal Comparison Bars */}
                <div className="space-y-3 pt-2">
                  {(() => {
                    const parsed = comparisonResult.items.map((it, idx) => {
                      const res = getMetricValue(it, selectedMetric);
                      return {
                        ...it,
                        color: stockColors[idx % stockColors.length],
                        numeric: res.numeric,
                        display: res.display,
                      };
                    });

                    // Determine max scale for visualization
                    const validNums = parsed
                      .map((p) => p.numeric)
                      .filter((n) => n !== null && !isNaN(n));
                    let maxScale = 100;
                    if (selectedMetric === 'risk_score') {
                      maxScale = 10;
                    } else if (selectedMetric === 'rsi_14' || selectedMetric === 'confidence') {
                      maxScale = 100;
                    } else if (selectedMetric === 'pe_ratio' || selectedMetric === 'forward_pe') {
                      const maxVal = validNums.length > 0 ? Math.max(...validNums) : 25;
                      maxScale = Math.max(maxVal * 1.15, 20);
                    } else {
                      const maxVal =
                        validNums.length > 0
                          ? Math.max(...validNums.map(Math.abs))
                          : 25;
                      maxScale = Math.max(maxVal * 1.15, 10);
                    }

                    return parsed.map((item) => (
                      <div key={item.ticker} className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span
                              className="w-2.5 h-2.5 rounded-full shrink-0"
                              style={{ backgroundColor: item.color.stroke }}
                            />
                            <StockLogo ticker={item.ticker} size="xs" />
                            <span className="font-mono font-black text-xs text-[#111318]">
                              {item.ticker}
                            </span>
                            <span className="text-[11px] text-gray-500 font-medium truncate max-w-[130px] hidden sm:inline">
                              {item.company_name}
                            </span>
                          </div>
                          <span className="font-mono font-black text-xs text-[#111318]">
                            {item.display}
                          </span>
                        </div>

                        {/* Progress Bar Container */}
                        <div className="h-3 rounded-full bg-gray-100 overflow-hidden relative">
                          {item.numeric !== null ? (
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{
                                width: `${Math.min(100, Math.max(4, (Math.abs(item.numeric) / maxScale) * 100))}%`,
                                backgroundColor: item.color.stroke,
                              }}
                            />
                          ) : (
                            <div className="h-full flex items-center justify-center text-[9px] font-bold text-gray-400">
                              Unavailable
                            </div>
                          )}
                        </div>
                      </div>
                    ));
                  })()}
                </div>

                {/* Benchmark Guide */}
                <div className="pt-2 border-t border-gray-100 flex items-center justify-between text-[10px] text-gray-400 font-bold px-1">
                  {selectedMetric === 'rsi_14' ? (
                    <>
                      <span>0 Oversold</span>
                      <span>50 Neutral</span>
                      <span>100 Overbought</span>
                    </>
                  ) : selectedMetric === 'risk_score' ? (
                    <>
                      <span>0 Low Risk</span>
                      <span>5 Moderate</span>
                      <span>10 High Risk</span>
                    </>
                  ) : selectedMetric === 'confidence' ? (
                    <>
                      <span>0% Minimum</span>
                      <span>50%</span>
                      <span>100% Maximum</span>
                    </>
                  ) : (
                    <>
                      <span>Cross-Stock Comparison</span>
                      <span>Normalized Metric Value</span>
                    </>
                  )}
                </div>
              </div>

              {/* Card 2: Key Takeaways */}
              <div className="rounded-[26px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] p-5 sm:p-6 space-y-4">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#111318]" />
                  <h4 className="text-sm font-black text-[#111318]">
                    Key Takeaways
                  </h4>
                </div>

                <div className="space-y-3">
                  {generateKeyTakeaways(comparisonResult.items).map((bullet, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-2xl bg-gray-50/70 border border-gray-100 flex items-start gap-3"
                    >
                      <div className="w-5 h-5 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                      </div>
                      <p className="text-xs text-gray-700 leading-relaxed font-medium">
                        {bullet}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
