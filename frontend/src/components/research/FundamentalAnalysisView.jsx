import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ShieldCheck,
  Scale,
  Activity,
  Layers,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  Users,
  Sparkles,
  Info,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';

export default function FundamentalAnalysisView({
  fundamental,
  loading = false,
  error = null,
  onRefresh,
  currency = 'USD',
  ticker = '',
}) {
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' | 'profitability' | 'stability' | 'valuation' | 'historical' | 'peers' | 'integrity'
  const [isExpanded, setIsExpanded] = useState(true);

  if (loading) {
    return (
      <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex items-center justify-center rounded-2xl">
        <div className="flex items-center gap-2.5 text-xs font-mono text-zinc-400">
          <Spinner className="h-4 w-4 text-rose-500" />
          <span>Executing Module 3 Fundamental Analysis Agent…</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 rounded-2xl space-y-3">
        <AlertBanner type="warning" message={error} />
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="btn-secondary py-1 px-2.5 text-[11px] flex items-center gap-1.5"
          >
            <RefreshCw className="h-3 w-3 text-zinc-400" />
            <span>Retry Fundamental Analysis</span>
          </button>
        )}
      </div>
    );
  }

  if (!fundamental) {
    return null;
  }

  const {
    revenue_and_earnings: rev,
    profitability: prof,
    debt_and_stability: stab,
    valuation_ratios: val,
    historical_comparison: hist,
    peer_comparison: peer,
    data_integrity_audit: audit,
    optional_enhancements: opt,
    executive_summary: execSummary,
    currency: fundCurrency,
    data_source: dataSource,
    retrieval_timestamp: retrievedAt,
  } = fundamental;

  const curr = fundCurrency || currency || 'USD';
  const currSym = curr === 'INR' ? '₹' : curr === 'USD' ? '$' : `${curr} `;

  // Resolve financial statement reporting currency (e.g. USD for foreign ADR filers like Infosys)
  const stmtCurr = hist?.statement_currency || fundamental?.statement_currency || curr;
  const stmtCurrSym = stmtCurr === 'INR' ? '₹' : stmtCurr === 'USD' ? '$' : `${stmtCurr} `;

  const formatStatementNumber = (valNum) => {
    if (valNum === null || valNum === undefined || isNaN(valNum)) return '—';
    const absVal = Math.abs(valNum);
    const sign = valNum < 0 ? '-' : '';
    if (absVal >= 1e9) return `${sign}${stmtCurrSym}${(absVal / 1e9).toFixed(2)}B`;
    if (absVal >= 1e6) return `${sign}${stmtCurrSym}${(absVal / 1e6).toFixed(2)}M`;
    if (absVal >= 1e3) return `${sign}${stmtCurrSym}${(absVal / 1e3).toFixed(2)}K`;
    return `${sign}${stmtCurrSym}${Math.round(absVal).toLocaleString()}`;
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'computed':
      case 'available':
        return <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">Computed</span>;
      case 'loss_making':
      case 'negative_equity':
        return <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">{status === 'loss_making' ? 'Loss Making' : 'Negative Equity'}</span>;
      case 'turnaround':
        return <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">Turnaround</span>;
      case 'unavailable':
      default:
        return <span className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded border border-white/[0.06]">N/A</span>;
    }
  };

  const getRatingBadge = (rating) => {
    if (rating === 'Strong') {
      return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">Strong Stability</span>;
    }
    if (rating === 'Moderate') {
      return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/25">Moderate Stability</span>;
    }
    if (rating === 'High Debt / Strained') {
      return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/25">High Debt / Strained</span>;
    }
    return <span className="text-xs font-semibold px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">{rating || 'N/A'}</span>;
  };

  return (
    <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 rounded-2xl space-y-4">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-400">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-tight uppercase">
                Module 3 – Fundamental Analysis Agent
              </h3>
              <span className="text-[10px] font-mono font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                {dataSource || 'yfinance'}
              </span>
              {audit?.is_consistent ? (
                <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  <CheckCircle2 className="h-3 w-3" />
                  Audit Verified ({audit?.data_quality_score?.toFixed(0)}%)
                </span>
              ) : (
                <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                  <AlertTriangle className="h-3 w-3" />
                  Audit Disclosures
                </span>
              )}
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Comprehensive valuation, solvency, profitability & peer benchmarking
              {ticker ? ` for ${ticker}` : ''}
              {retrievedAt ? ` • Computed ${new Date(retrievedAt).toLocaleDateString()}` : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              className="btn-secondary py-1 px-2.5 text-[11px] flex items-center gap-1.5"
              title="Refresh fundamental metrics"
            >
              <RefreshCw className="h-3 w-3 text-zinc-400" />
              <span>Refresh</span>
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="btn-secondary py-1 px-2.5 text-[11px] flex items-center gap-1.5"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3 w-3" />
                <span>Collapse</span>
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3" />
                <span>Expand</span>
              </>
            )}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4 animate-fade-in">
          {/* Executive Summary Card */}
          {execSummary && (
            <div className="p-3.5 rounded-xl bg-gradient-to-r from-rose-950/20 via-[#11111a] to-blue-950/20 border border-white/[0.08]">
              <div className="flex items-start gap-2.5">
                <Info className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                <p className="text-xs text-zinc-200 leading-relaxed font-sans">
                  {execSummary}
                </p>
              </div>
            </div>
          )}

          {/* Navigation Sub-Tabs */}
          <div className="flex flex-wrap items-center gap-1.5 pb-2 border-b border-white/[0.06]">
            {[
              { id: 'summary', label: 'Core Overview', icon: Activity },
              { id: 'profitability', label: 'Profitability & Margins', icon: TrendingUp },
              { id: 'stability', label: 'Debt & Stability', icon: ShieldCheck },
              { id: 'valuation', label: 'Valuation & Multiples', icon: Scale },
              { id: 'historical', label: 'Multi-Year Matrix', icon: Layers },
              { id: 'peers', label: 'Peer Benchmarking', icon: Users },
              { id: 'integrity', label: 'Data Integrity Audit', icon: CheckCircle2 },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                    isActive
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                      : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: Core Overview / Summary */}
          {activeTab === 'summary' && (
            <div className="space-y-4">
              {/* Top KPI Cards Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {/* Revenue */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                  <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Latest Revenue</span>
                  <div className="mt-1">
                    <div className="text-lg font-bold text-white font-mono">{rev?.revenue?.formatted || '—'}</div>
                    <div className="flex items-center gap-1.5 mt-0.5 text-xs font-mono">
                      {rev?.revenue_growth_yoy?.value !== null && rev?.revenue_growth_yoy?.value !== undefined ? (
                        <span className={rev.revenue_growth_yoy.value >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          {rev.revenue_growth_yoy.formatted} YoY
                        </span>
                      ) : (
                        <span className="text-zinc-500">YoY N/A</span>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-500 font-mono">Period: {rev?.revenue?.period || 'Latest'}</div>
                </div>

                {/* Net Income */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                  <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Net Income</span>
                  <div className="mt-1">
                    <div className="text-lg font-bold text-white font-mono">{rev?.net_income?.formatted || '—'}</div>
                    <div className="flex items-center gap-1.5 mt-0.5 text-xs font-mono">
                      {rev?.net_income_growth_yoy?.value !== null && rev?.net_income_growth_yoy?.value !== undefined ? (
                        <span className={rev.net_income_growth_yoy.value >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
                          {rev.net_income_growth_yoy.formatted} YoY
                        </span>
                      ) : (
                        <span className="text-zinc-500">YoY N/A</span>
                      )}
                    </div>
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-500 font-mono">Period: {rev?.net_income?.period || 'Latest'}</div>
                </div>

                {/* Return on Equity */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Return on Equity</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-white/[0.05] text-zinc-400 border border-white/[0.05]">
                      {prof?.return_on_equity?.method === 'average_equity' ? 'Avg Eq' : 'End Eq'}
                    </span>
                  </div>
                  <div className="mt-1">
                    <div className="text-lg font-bold text-white font-mono">{prof?.return_on_equity?.formatted || '—'}</div>
                    <div className="text-xs text-zinc-400 mt-0.5 font-mono">ROA: {prof?.return_on_assets?.formatted || '—'}</div>
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-500 font-mono">{prof?.margin_trend || 'Margin Trend'}</div>
                </div>

                {/* Financial Stability */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                  <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Solvency Rating</span>
                  <div className="mt-1">
                    {getRatingBadge(stab?.stability_rating)}
                    <div className="text-xs text-zinc-400 mt-1 font-mono">D/E: {stab?.debt_to_equity?.formatted || '—'}</div>
                  </div>
                  <div className="mt-2 text-[10px] text-zinc-500 font-mono">Current: {stab?.current_ratio?.formatted || '—'}</div>
                </div>
              </div>

              {/* Narratives breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] space-y-1.5">
                  <div className="flex items-center gap-1.5 text-zinc-300 font-semibold">
                    <BarChart3 className="h-4 w-4 text-rose-400" />
                    <span>Revenue & Earnings Analysis</span>
                  </div>
                  <p className="text-zinc-400 leading-relaxed">{rev?.summary_narrative}</p>
                </div>
                <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] space-y-1.5">
                  <div className="flex items-center gap-1.5 text-zinc-300 font-semibold">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    <span>Financial Stability & Solvency</span>
                  </div>
                  <p className="text-zinc-400 leading-relaxed">{stab?.summary_narrative}</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: Profitability & Margins */}
          {activeTab === 'profitability' && (
            <div className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06]">
                  <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Gross Margin</span>
                  <div className="text-xl font-bold text-white font-mono mt-1">{prof?.gross_margin?.formatted || '—'}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">{prof?.gross_margin?.notes || 'Gross profit / Revenue'}</div>
                </div>
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06]">
                  <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Operating Margin</span>
                  <div className="text-xl font-bold text-white font-mono mt-1">{prof?.operating_margin?.formatted || '—'}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">{prof?.operating_margin?.notes || 'Operating income / Revenue'}</div>
                </div>
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06]">
                  <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Net Profit Margin</span>
                  <div className="text-xl font-bold text-white font-mono mt-1">{prof?.net_margin?.formatted || '—'}</div>
                  <div className="text-[10px] text-zinc-500 mt-1">{prof?.net_margin?.notes || 'Net income / Revenue'}</div>
                </div>
              </div>

              {/* ROE & ROA Section */}
              <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.04]">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">Capital Efficiency Ratios</h4>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] text-zinc-400">ROE Method:</span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                      {prof?.return_on_equity?.method === 'average_equity' ? 'Two-Period Average Equity' : 'Reporting Period Ending Equity'}
                    </span>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="text-xs text-zinc-400">Return on Equity (ROE)</span>
                    <div className="text-2xl font-bold text-white font-mono">{prof?.return_on_equity?.formatted || '—'}</div>
                    <p className="text-[11px] text-zinc-400 leading-relaxed">{prof?.return_on_equity?.notes}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-xs text-zinc-400">Return on Assets (ROA)</span>
                    <div className="text-2xl font-bold text-white font-mono">{prof?.return_on_assets?.formatted || '—'}</div>
                    <p className="text-[11px] text-zinc-400 leading-relaxed">{prof?.return_on_assets?.notes}</p>
                  </div>
                </div>
              </div>

              {/* Narrative */}
              <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06]">
                <p className="text-xs text-zinc-300 leading-relaxed">{prof?.summary_narrative}</p>
              </div>
            </div>
          )}

          {/* TAB 3: Debt & Financial Stability */}
          {activeTab === 'stability' && (() => {
            const totalDebtNum = stab?.total_debt?.value;
            const stDebtNum = stab?.short_term_debt?.value;
            const ltDebtNum = stab?.long_term_debt?.value;
            const hasValidDebtSplit = totalDebtNum != null && totalDebtNum > 0 && (stDebtNum != null || ltDebtNum != null);
            const stPct = hasValidDebtSplit && stDebtNum != null ? Math.min(100, Math.max(0, (stDebtNum / totalDebtNum) * 100)).toFixed(1) : null;
            const ltPct = hasValidDebtSplit && ltDebtNum != null ? Math.min(100, Math.max(0, (ltDebtNum / totalDebtNum) * 100)).toFixed(1) : null;

            return (
              <div className="space-y-4">
                {/* 1. Solvency & Leverage Ratios */}
                <div>
                  <h4 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">Solvency & Capital Structure</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Debt-to-Equity</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.debt_to_equity?.formatted || '—'}</div>
                      {stab?.debt_to_equity?.notes && (
                        <p className="text-[9px] text-zinc-500 mt-0.5 line-clamp-1" title={stab?.debt_to_equity?.notes}>{stab?.debt_to_equity?.notes}</p>
                      )}
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Debt-to-Assets</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.debt_to_assets?.formatted || '—'}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Equity Ratio</span>
                      <div className="text-base font-bold text-emerald-400 font-mono mt-1">{stab?.equity_ratio?.formatted || '—'}</div>
                      {stab?.equity_ratio?.notes && (
                        <p className="text-[9px] text-zinc-500 mt-0.5 line-clamp-1" title={stab?.equity_ratio?.notes}>{stab?.equity_ratio?.notes}</p>
                      )}
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Net Debt</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.net_debt?.formatted || '—'}</div>
                      <span className="text-[9px] text-zinc-500 font-mono block mt-0.5">{stab?.net_debt?.notes}</span>
                    </div>
                  </div>
                </div>

                {/* 2. Debt Obligations & Composition Section */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-white">Debt Composition & Obligations</h4>
                      <p className="text-[10px] text-zinc-400">Total debt obligations broken down by maturity</p>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-zinc-500 uppercase font-semibold block">Total Debt</span>
                      <span className="text-base font-bold text-white font-mono">{stab?.total_debt?.formatted || '—'}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-amber-400 uppercase font-semibold">Short-Term Debt</span>
                        {stPct != null && (
                          <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            {stPct}% of total
                          </span>
                        )}
                      </div>
                      <div className="text-sm font-bold text-white font-mono mt-1">{stab?.short_term_debt?.formatted || '—'}</div>
                      <p className="text-[9px] text-zinc-400 mt-1 leading-snug">{stab?.short_term_debt?.notes || 'Due within one operating cycle / one year'}</p>
                    </div>

                    <div className="p-3 rounded-lg bg-black/40 border border-white/[0.04]">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-indigo-400 uppercase font-semibold">Long-Term Debt</span>
                        {ltPct != null && (
                          <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                            {ltPct}% of total
                          </span>
                        )}
                      </div>
                      <div className="text-sm font-bold text-white font-mono mt-1">{stab?.long_term_debt?.formatted || '—'}</div>
                      <p className="text-[9px] text-zinc-400 mt-1 leading-snug">{stab?.long_term_debt?.notes || 'Obligations maturing beyond one year'}</p>
                    </div>
                  </div>

                  {/* Composition Bar */}
                  {hasValidDebtSplit && (stPct != null || ltPct != null) && (
                    <div className="space-y-1.5 pt-1">
                      <div className="w-full h-2 rounded-full bg-white/[0.06] overflow-hidden flex">
                        {stPct != null && parseFloat(stPct) > 0 && (
                          <div
                            style={{ width: `${stPct}%` }}
                            className="h-full bg-amber-500 transition-all duration-300"
                            title={`Short-term: ${stPct}%`}
                          />
                        )}
                        {ltPct != null && parseFloat(ltPct) > 0 && (
                          <div
                            style={{ width: `${ltPct}%` }}
                            className="h-full bg-indigo-500 transition-all duration-300"
                            title={`Long-term: ${ltPct}%`}
                          />
                        )}
                      </div>
                      <div className="flex items-center justify-between text-[9px] text-zinc-400 font-mono">
                        <span className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" /> Short-Term ({stPct ?? '0.0'}%)
                        </span>
                        <span className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 inline-block" /> Long-Term ({ltPct ?? '0.0'}%)
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* 3. Liquidity & Coverage Ratios */}
                <div>
                  <h4 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">Liquidity & Debt Service</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Current Ratio</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.current_ratio?.formatted || '—'}</div>
                      <p className="text-[10px] text-zinc-500 mt-0.5">{stab?.current_ratio?.notes}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Quick Ratio</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.quick_ratio?.formatted || '—'}</div>
                      <p className="text-[10px] text-zinc-500 mt-0.5">{stab?.quick_ratio?.notes}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Interest Coverage</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.interest_coverage?.formatted || '—'}</div>
                      <p className="text-[10px] text-zinc-500 mt-0.5">{stab?.interest_coverage?.notes}</p>
                    </div>
                  </div>
                </div>

                {/* 4. Balance Sheet Context Metrics */}
                <div>
                  <h4 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">Balance Sheet Overview</h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Total Assets</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.total_assets?.formatted || '—'}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Stockholders' Equity</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.stockholders_equity?.formatted || '—'}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Current Liabilities</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.current_liabilities?.formatted || '—'}</div>
                    </div>
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06]">
                      <span className="text-[10px] text-zinc-400 uppercase font-semibold">Total Liabilities</span>
                      <div className="text-base font-bold text-white font-mono mt-1">{stab?.total_liabilities?.formatted || '—'}</div>
                    </div>
                  </div>
                </div>

                {/* 5. Free Cash Flow */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-white">Free Cash Flow (FCF)</span>
                    <p className="text-[11px] text-zinc-400">{stab?.free_cash_flow?.notes || 'Operating Cash Flow minus Capital Expenditures'}</p>
                  </div>
                  <div className="text-lg font-bold font-mono text-emerald-400">
                    {stab?.free_cash_flow?.formatted || '—'}
                  </div>
                </div>

                {/* 6. Summary Narrative */}
                <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06]">
                  <p className="text-xs text-zinc-300 leading-relaxed">{stab?.summary_narrative}</p>
                </div>
              </div>
            );
          })()}

          {/* TAB 4: Valuation & Multiples */}
          {activeTab === 'valuation' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Trailing P/E */}
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-zinc-400 uppercase font-semibold">Trailing P/E</span>
                    {getStatusBadge(val?.trailing_pe?.status)}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">{val?.trailing_pe?.formatted || '—'}</div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">{val?.trailing_pe?.notes}</p>
                </div>

                {/* Forward P/E */}
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-zinc-400 uppercase font-semibold">Forward P/E</span>
                    {getStatusBadge(val?.forward_pe?.status)}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">{val?.forward_pe?.formatted || '—'}</div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">{val?.forward_pe?.notes}</p>
                </div>

                {/* Price to Book */}
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-zinc-400 uppercase font-semibold">Price to Book (P/B)</span>
                    {getStatusBadge(val?.price_to_book?.status)}
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">{val?.price_to_book?.formatted || '—'}</div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">{val?.price_to_book?.notes}</p>
                </div>

                {/* Return on Equity (ROE) */}
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-zinc-400 uppercase font-semibold">Return on Equity (ROE)</span>
                    {getStatusBadge(val?.return_on_equity?.status)}
                  </div>
                  <div className="text-2xl font-bold text-emerald-400 font-mono">{val?.return_on_equity?.formatted || '—'}</div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">{val?.return_on_equity?.notes}</p>
                </div>
              </div>

              {/* Optional Enhancements Section (Clearly segregated) */}
              {opt && (
                <div className="p-4 rounded-xl bg-gradient-to-r from-blue-950/20 to-purple-950/20 border border-blue-500/20 space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-blue-400" />
                    <h4 className="text-xs font-bold text-blue-300 uppercase tracking-wider">
                      Optional Valuation Enhancements
                    </h4>
                    <span className="text-[10px] text-blue-400/80 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
                      Secondary Indicators
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400">
                    {opt.notes || 'Supplemental valuation indicators segregated from mandatory fundamental criteria.'}
                  </p>
                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div className="p-3 rounded-lg bg-[#0a0a10]/80 border border-white/[0.06]">
                      <span className="text-[11px] text-zinc-400 uppercase font-semibold">Price to Sales (P/S)</span>
                      <div className="text-lg font-bold text-white font-mono mt-1">{opt.price_to_sales?.formatted || '—'}</div>
                      <span className="text-[10px] text-zinc-500 font-mono">{opt.price_to_sales?.notes}</span>
                    </div>
                    <div className="p-3 rounded-lg bg-[#0a0a10]/80 border border-white/[0.06]">
                      <span className="text-[11px] text-zinc-400 uppercase font-semibold">Dividend Yield</span>
                      <div className="text-lg font-bold text-white font-mono mt-1">{opt.dividend_yield?.formatted || '—'}</div>
                      <span className="text-[10px] text-zinc-500 font-mono">{opt.dividend_yield?.notes}</span>
                    </div>
                  </div>
                </div>
              )}

              <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06]">
                <p className="text-xs text-zinc-300 leading-relaxed">{val?.summary_narrative}</p>
              </div>
            </div>
          )}

          {/* TAB 5: Multi-Year Matrix & Historical Financial Trends */}
          {activeTab === 'historical' && (() => {
            const chartYears = [...(hist?.years || [])].reverse();
            const hasMultipleYears = chartYears.length >= 2;

            // Trend metrics extraction across chronological periods (oldest to newest)
            const firstYear = chartYears[0];
            const lastYear = chartYears[chartYears.length - 1];

            const revChange = hasMultipleYears && firstYear?.total_revenue && lastYear?.total_revenue
              ? lastYear.total_revenue - firstYear.total_revenue
              : null;
            const netChange = hasMultipleYears && firstYear?.net_income !== null && lastYear?.net_income !== null
              ? lastYear.net_income - firstYear.net_income
              : null;
            const omChange = hasMultipleYears && firstYear?.operating_margin_pct !== null && lastYear?.operating_margin_pct !== null
              ? lastYear.operating_margin_pct - firstYear.operating_margin_pct
              : null;
            const roeChange = hasMultipleYears && firstYear?.roe_pct !== null && lastYear?.roe_pct !== null
              ? lastYear.roe_pct - firstYear.roe_pct
              : null;

            // Chart scaling calculations
            const maxRev = Math.max(...chartYears.map((y) => y.total_revenue || y.revenue || 0), 1);
            const maxNet = Math.max(...chartYears.map((y) => Math.abs(y.net_income || 0)), 1);

            return (
              <div className="space-y-4">
                {/* Statement Currency Disclosures */}
                {stmtCurr !== curr && (
                  <div className="flex items-center gap-2 p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-blue-300">
                    <Info className="h-4 w-4 shrink-0 text-blue-400" />
                    <span>
                      Financial statement disclosures are reported in <strong>{stmtCurr}</strong> ({stmtCurrSym.trim()}) based on official regulatory filings, while live market trading quotes are denominated in <strong>{curr}</strong> ({currSym.trim()}).
                    </span>
                  </div>
                )}

                {/* Trend Summary Direction Badges */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-zinc-500 uppercase font-semibold">Revenue Trend</span>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {revChange === null ? 'Single Period' : revChange > 0 ? 'Expanding' : revChange < 0 ? 'Contracting' : 'Stable'}
                      </div>
                    </div>
                    <div className={`p-1.5 rounded-lg ${revChange === null ? 'bg-zinc-800 text-zinc-400' : revChange >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                      {revChange === null ? <Minus className="h-4 w-4" /> : revChange >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-zinc-500 uppercase font-semibold">Net Income Trend</span>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {netChange === null ? 'Single Period' : netChange > 0 ? 'Growing' : netChange < 0 ? 'Compressing' : 'Stable'}
                      </div>
                    </div>
                    <div className={`p-1.5 rounded-lg ${netChange === null ? 'bg-zinc-800 text-zinc-400' : netChange >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                      {netChange === null ? <Minus className="h-4 w-4" /> : netChange >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-zinc-500 uppercase font-semibold">Operating Margin</span>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {omChange === null ? 'Single Period' : omChange > 0.5 ? `+${omChange.toFixed(1)}% Expansion` : omChange < -0.5 ? `${omChange.toFixed(1)}% Contraction` : 'Stable'}
                      </div>
                    </div>
                    <div className={`p-1.5 rounded-lg ${omChange === null ? 'bg-zinc-800 text-zinc-400' : omChange >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                      {omChange === null ? <Minus className="h-4 w-4" /> : omChange >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-zinc-500 uppercase font-semibold">ROE Trajectory</span>
                      <div className="text-xs font-bold text-white mt-0.5">
                        {roeChange === null ? 'Single Period' : roeChange > 0 ? `+${roeChange.toFixed(1)}% Gained` : roeChange < 0 ? `${roeChange.toFixed(1)}% Compressed` : 'Stable'}
                      </div>
                    </div>
                    <div className={`p-1.5 rounded-lg ${roeChange === null ? 'bg-zinc-800 text-zinc-400' : roeChange >= 0 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                      {roeChange === null ? <Minus className="h-4 w-4" /> : roeChange >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    </div>
                  </div>
                </div>

                {/* 4 Interactive SVG Visualizations (Section 9F) */}
                {chartYears.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                    {/* Chart 1: Annual Revenue */}
                    <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white flex items-center gap-1.5">
                          <BarChart3 className="h-3.5 w-3.5 text-blue-400" />
                          Annual Revenue Trajectory
                        </span>
                        <span className="text-[10px] font-mono text-zinc-400">{stmtCurr}</span>
                      </div>
                      <div className="h-28 flex items-end justify-around gap-2 pt-4 px-2">
                        {chartYears.map((y) => {
                          const val = y.total_revenue || y.revenue || 0;
                          const heightPct = Math.max(Math.round((val / maxRev) * 100), 8);
                          const yr = y.period.split('-')[0];
                          return (
                            <div key={y.period} className="flex-1 flex flex-col items-center gap-1.5 group">
                              <span className="text-[9px] font-mono font-semibold text-zinc-300 opacity-90 group-hover:text-blue-400 transition-colors">
                                {formatStatementNumber(val)}
                              </span>
                              <div className="w-full bg-white/[0.03] rounded-t-md h-20 flex items-end">
                                <div
                                  style={{ height: `${heightPct}%` }}
                                  className="w-full bg-gradient-to-t from-blue-600/50 to-blue-400 rounded-t-md transition-all duration-500 hover:brightness-125"
                                />
                              </div>
                              <span className="text-[10px] font-mono text-zinc-400 font-medium">FY{yr}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Chart 2: Annual Net Income */}
                    <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white flex items-center gap-1.5">
                          <BarChart3 className="h-3.5 w-3.5 text-emerald-400" />
                          Annual Net Income Trajectory
                        </span>
                        <span className="text-[10px] font-mono text-zinc-400">{stmtCurr}</span>
                      </div>
                      <div className="h-28 flex items-end justify-around gap-2 pt-4 px-2">
                        {chartYears.map((y) => {
                          const val = y.net_income || 0;
                          const isPos = val >= 0;
                          const heightPct = Math.max(Math.round((Math.abs(val) / maxNet) * 100), 8);
                          const yr = y.period.split('-')[0];
                          return (
                            <div key={y.period} className="flex-1 flex flex-col items-center gap-1.5 group">
                              <span className={`text-[9px] font-mono font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>
                                {formatStatementNumber(val)}
                              </span>
                              <div className="w-full bg-white/[0.03] rounded-t-md h-20 flex items-end">
                                <div
                                  style={{ height: `${heightPct}%` }}
                                  className={`w-full rounded-t-md transition-all duration-500 ${isPos ? 'bg-gradient-to-t from-emerald-600/50 to-emerald-400 hover:brightness-125' : 'bg-gradient-to-t from-rose-600/50 to-rose-400'}`}
                                />
                              </div>
                              <span className="text-[10px] font-mono text-zinc-400 font-medium">FY{yr}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Chart 3: Profitability Margins Comparison */}
                    <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white flex items-center gap-1.5">
                          <Activity className="h-3.5 w-3.5 text-purple-400" />
                          Profitability Margins Trend (%)
                        </span>
                        <div className="flex items-center gap-2 text-[9px] font-mono">
                          <span className="flex items-center gap-1 text-cyan-400"><span className="h-2 w-2 rounded-full bg-cyan-400" />Gross</span>
                          <span className="flex items-center gap-1 text-purple-400"><span className="h-2 w-2 rounded-full bg-purple-400" />Operating</span>
                          <span className="flex items-center gap-1 text-emerald-400"><span className="h-2 w-2 rounded-full bg-emerald-400" />Net</span>
                        </div>
                      </div>
                      <div className="h-28 flex items-end justify-around gap-3 pt-3 px-1">
                        {chartYears.map((y) => {
                          const yr = y.period.split('-')[0];
                          const gm = y.gross_margin_pct ?? 0;
                          const om = y.operating_margin_pct ?? 0;
                          const nm = y.net_margin_pct ?? 0;
                          const maxM = Math.max(gm, om, nm, 50);
                          return (
                            <div key={y.period} className="flex-1 flex flex-col items-center gap-1">
                              <div className="flex items-end justify-center gap-1 h-20 w-full px-1">
                                <div title={`Gross: ${gm}%`} style={{ height: `${Math.max(Math.round((gm / maxM) * 100), 6)}%` }} className="w-1/3 bg-cyan-400/80 rounded-t-sm" />
                                <div title={`Operating: ${om}%`} style={{ height: `${Math.max(Math.round((om / maxM) * 100), 6)}%` }} className="w-1/3 bg-purple-500/80 rounded-t-sm" />
                                <div title={`Net: ${nm}%`} style={{ height: `${Math.max(Math.round((nm / maxM) * 100), 6)}%` }} className="w-1/3 bg-emerald-400/80 rounded-t-sm" />
                              </div>
                              <span className="text-[10px] font-mono text-zinc-400 font-medium">FY{yr}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Chart 4: Return on Capital (ROA & ROE) */}
                    <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white flex items-center gap-1.5">
                          <Scale className="h-3.5 w-3.5 text-amber-400" />
                          Returns on Capital Trend (%)
                        </span>
                        <div className="flex items-center gap-2 text-[9px] font-mono">
                          <span className="flex items-center gap-1 text-amber-400"><span className="h-2 w-2 rounded-full bg-amber-400" />ROA</span>
                          <span className="flex items-center gap-1 text-rose-400"><span className="h-2 w-2 rounded-full bg-rose-400" />ROE</span>
                        </div>
                      </div>
                      <div className="h-28 flex items-end justify-around gap-3 pt-3 px-1">
                        {chartYears.map((y) => {
                          const yr = y.period.split('-')[0];
                          const roa = y.roa_pct ?? 0;
                          const roe = y.roe_pct ?? 0;
                          const maxR = Math.max(roa, roe, 30);
                          return (
                            <div key={y.period} className="flex-1 flex flex-col items-center gap-1">
                              <div className="flex items-end justify-center gap-1.5 h-20 w-full px-2">
                                <div title={`ROA: ${roa}%`} style={{ height: `${Math.max(Math.round((roa / maxR) * 100), 6)}%` }} className="w-1/2 bg-amber-400/80 rounded-t-sm" />
                                <div title={`ROE: ${roe}%`} style={{ height: `${Math.max(Math.round((roe / maxR) * 100), 6)}%` }} className="w-1/2 bg-rose-500/80 rounded-t-sm" />
                              </div>
                              <span className="text-[10px] font-mono text-zinc-400 font-medium">FY{yr}</span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {/* Multi-Year Statement Comparison Matrix Table */}
                <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-white/[0.03] text-zinc-400 uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Financial Metric</th>
                        {(hist?.years || []).map((y) => (
                          <th key={y.period} className="py-2.5 px-3 text-right">
                            <div className="text-white font-bold">{y.period}</div>
                            {y.revenue_growth_yoy !== null && y.revenue_growth_yoy !== undefined ? (
                              <div className={`text-[9px] font-semibold ${y.revenue_growth_yoy >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                Rev YoY {y.revenue_growth_yoy >= 0 ? `+${y.revenue_growth_yoy.toFixed(1)}%` : `${y.revenue_growth_yoy.toFixed(1)}%`}
                              </div>
                            ) : (
                              <div className="text-[9px] text-zinc-500 font-normal">Base Year</div>
                            )}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                      {/* 1. Total Revenue */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2.5 px-3 font-semibold text-white">Total Revenue</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2.5 px-3 text-right font-bold text-white">
                            {formatStatementNumber(y.total_revenue ?? y.revenue)}
                          </td>
                        ))}
                      </tr>

                      {/* 2. Gross Profit */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-300">Gross Profit</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right">
                            {formatStatementNumber(y.gross_profit)}
                          </td>
                        ))}
                      </tr>

                      {/* 3. Gross Margin % */}
                      <tr className="hover:bg-white/[0.02] bg-white/[0.01]">
                        <td className="py-1.5 px-3 text-zinc-400 text-[11px]">Gross Margin (%)</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-1.5 px-3 text-right text-[11px] text-cyan-300">
                            {y.gross_margin_pct !== null && y.gross_margin_pct !== undefined ? `${y.gross_margin_pct.toFixed(2)}%` : '—'}
                          </td>
                        ))}
                      </tr>

                      {/* 4. Operating Income */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-300">Operating Income</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right">
                            {formatStatementNumber(y.operating_income)}
                          </td>
                        ))}
                      </tr>

                      {/* 5. Operating Margin % */}
                      <tr className="hover:bg-white/[0.02] bg-white/[0.01]">
                        <td className="py-1.5 px-3 text-zinc-400 text-[11px]">Operating Margin (%)</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-1.5 px-3 text-right text-[11px] text-purple-300">
                            {y.operating_margin_pct !== null && y.operating_margin_pct !== undefined ? `${y.operating_margin_pct.toFixed(2)}%` : '—'}
                          </td>
                        ))}
                      </tr>

                      {/* 6. Net Income */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2.5 px-3 font-semibold text-emerald-400">Net Income</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2.5 px-3 text-right font-bold text-emerald-400">
                            {formatStatementNumber(y.net_income)}
                          </td>
                        ))}
                      </tr>

                      {/* 7. Net Margin % */}
                      <tr className="hover:bg-white/[0.02] bg-white/[0.01]">
                        <td className="py-1.5 px-3 text-zinc-400 text-[11px]">Net Margin (%)</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-1.5 px-3 text-right text-[11px] text-emerald-300">
                            {y.net_margin_pct !== null && y.net_margin_pct !== undefined ? `${y.net_margin_pct.toFixed(2)}%` : '—'}
                          </td>
                        ))}
                      </tr>

                      {/* 8. Net Income YoY Growth % */}
                      <tr className="hover:bg-white/[0.02] bg-white/[0.01]">
                        <td className="py-1.5 px-3 text-zinc-400 text-[11px]">Net Income YoY Growth</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-1.5 px-3 text-right text-[11px]">
                            {y.net_income_growth_yoy !== null && y.net_income_growth_yoy !== undefined ? (
                              <span className={y.net_income_growth_yoy >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                                {y.net_income_growth_yoy >= 0 ? `+${y.net_income_growth_yoy.toFixed(1)}%` : `${y.net_income_growth_yoy.toFixed(1)}%`}
                              </span>
                            ) : (
                              <span className="text-zinc-500">—</span>
                            )}
                          </td>
                        ))}
                      </tr>

                      {/* 9. Diluted EPS */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-300">Diluted EPS</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right font-medium text-white">
                            {y.diluted_eps !== null && y.diluted_eps !== undefined ? `${stmtCurrSym}${y.diluted_eps.toFixed(2)}` : '—'}
                          </td>
                        ))}
                      </tr>

                      {/* 10. Operating Cash Flow */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-400">Operating Cash Flow</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right text-zinc-300">
                            {formatStatementNumber(y.operating_cash_flow)}
                          </td>
                        ))}
                      </tr>

                      {/* 11. Free Cash Flow */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-400">Free Cash Flow</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right text-zinc-300">
                            {formatStatementNumber(y.free_cash_flow)}
                          </td>
                        ))}
                      </tr>

                      {/* 12. Total Assets */}
                      <tr className="hover:bg-white/[0.02] border-t border-white/[0.08]">
                        <td className="py-2 px-3 text-zinc-300">Total Assets</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right">
                            {formatStatementNumber(y.total_assets)}
                          </td>
                        ))}
                      </tr>

                      {/* 13. Total Liabilities */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-300">Total Liabilities</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right">
                            {formatStatementNumber(y.total_liabilities)}
                          </td>
                        ))}
                      </tr>

                      {/* 14. Total Debt */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-300">Total Debt</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right">
                            {formatStatementNumber(y.total_debt)}
                          </td>
                        ))}
                      </tr>

                      {/* 15. Stockholders' Equity */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2 px-3 text-zinc-300">Shareholder Equity</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2 px-3 text-right">
                            {formatStatementNumber(y.stockholders_equity ?? y.total_equity)}
                          </td>
                        ))}
                      </tr>

                      {/* 16. Return on Assets (ROA) */}
                      <tr className="hover:bg-white/[0.02] border-t border-white/[0.08]">
                        <td className="py-2.5 px-3 font-semibold text-amber-400">Return on Assets (ROA)</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2.5 px-3 text-right font-bold text-amber-400 font-mono">
                            {y.roa_pct !== null && y.roa_pct !== undefined ? `${y.roa_pct.toFixed(2)}%` : '—'}
                          </td>
                        ))}
                      </tr>

                      {/* 17. Return on Equity (ROE) */}
                      <tr className="hover:bg-white/[0.02]">
                        <td className="py-2.5 px-3 font-semibold text-emerald-400">Return on Equity (ROE)</td>
                        {(hist?.years || []).map((y) => (
                          <td key={y.period} className="py-2.5 px-3 text-right font-bold text-emerald-400 font-mono">
                            {y.roe_pct !== null && y.roe_pct !== undefined ? `${y.roe_pct.toFixed(2)}%` : '—'}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Safe CAGR Disclosures */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  <div className="p-3 rounded-lg bg-[#09090e] border border-white/[0.06]">
                    <span className="text-[11px] text-zinc-400 uppercase font-semibold">Revenue CAGR</span>
                    <div className="text-base font-bold text-white font-mono mt-0.5">{rev?.revenue_cagr?.formatted || '—'}</div>
                    <p className="text-[10px] text-zinc-500 mt-1">{rev?.revenue_cagr?.notes}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-[#09090e] border border-white/[0.06]">
                    <span className="text-[11px] text-zinc-400 uppercase font-semibold">Net Income CAGR</span>
                    <div className="text-base font-bold text-white font-mono mt-0.5">{rev?.net_income_cagr?.formatted || '—'}</div>
                    <p className="text-[10px] text-zinc-500 mt-1">{rev?.net_income_cagr?.notes}</p>
                  </div>
                </div>

                {/* Multi-Year Factual Trend Narrative */}
                <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex items-start gap-2.5">
                  <Sparkles className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-zinc-300 leading-relaxed font-sans">{hist?.summary_narrative}</p>
                </div>
              </div>
            );
          })()}

          {/* TAB 6: Peer Benchmarking */}
          {activeTab === 'peers' && (() => {
            const peerItems = peer?.peers || [];
            const nonTargetPeers = peerItems.filter((p) => !p.is_target && p.ticker !== peer?.target_ticker);
            const targetRow = peerItems.find((p) => p.is_target || p.ticker === peer?.target_ticker);

            const formatMarketCap = (cap) => {
              if (cap === null || cap === undefined || isNaN(cap) || cap <= 0) return '—';
              if (curr === 'INR') {
                const crore = cap / 1e7;
                if (crore >= 1e5) return `₹${(crore / 1e5).toFixed(2)}L Cr`;
                return `₹${crore.toFixed(0)} Cr`;
              }
              if (cap >= 1e12) return `$${(cap / 1e12).toFixed(2)}T`;
              if (cap >= 1e9) return `$${(cap / 1e9).toFixed(2)}B`;
              if (cap >= 1e6) return `$${(cap / 1e6).toFixed(2)}M`;
              return `${currSym}${Math.round(cap).toLocaleString()}`;
            };

            const getPositionColor = (pos, type) => {
              const p = (pos || '').toLowerCase();
              if (type === 'valuation') {
                if (p.includes('discount')) return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
                if (p.includes('premium')) return 'bg-rose-500/10 text-rose-300 border-rose-500/25';
                if (p.includes('loss')) return 'bg-zinc-500/10 text-zinc-400 border-zinc-500/25';
                return 'bg-sky-500/10 text-sky-300 border-sky-500/25';
              }
              if (type === 'profitability') {
                if (p.includes('above') || p.includes('outperforming')) return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
                if (p.includes('below') || p.includes('underperforming')) return 'bg-amber-500/10 text-amber-300 border-amber-500/25';
                return 'bg-sky-500/10 text-sky-300 border-sky-500/25';
              }
              if (type === 'leverage') {
                if (p.includes('conservative')) return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
                if (p.includes('elevated')) return 'bg-rose-500/10 text-rose-300 border-rose-500/25';
                return 'bg-sky-500/10 text-sky-300 border-sky-500/25';
              }
              if (type === 'strength') {
                if (p.includes('strong')) return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/25';
                if (p.includes('vulnerable')) return 'bg-rose-500/10 text-rose-300 border-rose-500/25';
                return 'bg-sky-500/10 text-sky-300 border-sky-500/25';
              }
              return 'bg-zinc-500/10 text-zinc-300 border-white/[0.08]';
            };

            // Chart data preparation: Target + Non-target peers + Median
            const chartDataItems = [];
            if (targetRow) {
              chartDataItems.push({
                label: targetRow.ticker,
                isTarget: true,
                isMedian: false,
                pe: targetRow.pe_ratio,
                pb: targetRow.pb_ratio,
                roe: targetRow.roe,
                roa: targetRow.roa,
                netMargin: targetRow.net_margin,
              });
            }
            nonTargetPeers.forEach((p) => {
              chartDataItems.push({
                label: p.ticker.replace('.NS', '').replace('.BO', ''),
                isTarget: false,
                isMedian: false,
                pe: p.pe_ratio,
                pb: p.pb_ratio,
                roe: p.roe,
                roa: p.roa,
                netMargin: p.net_margin,
              });
            });
            if (peer?.peer_median_pe != null || peer?.peer_median_roe != null) {
              chartDataItems.push({
                label: 'Median',
                isTarget: false,
                isMedian: true,
                pe: peer?.peer_median_pe,
                pb: peer?.peer_median_pb,
                roe: peer?.peer_median_roe,
                roa: peer?.peer_median_roa,
                netMargin: peer?.peer_median_net_margin,
              });
            }

            // Valuation Chart Scaling
            const maxPeVal = Math.max(...chartDataItems.map((d) => d.pe || 0), 30);
            const maxPbVal = Math.max(...chartDataItems.map((d) => d.pb || 0), 10);

            // Profitability Chart Scaling
            const maxProfVal = Math.max(...chartDataItems.map((d) => Math.max(d.roe || 0, d.roa || 0, d.netMargin || 0)), 30);

            return (
              <div className="space-y-4">
                {/* 1. Multi-Dimensional Positioning Badges */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[10px] text-zinc-400 uppercase font-semibold">Relative Valuation</span>
                    <div className="mt-1">
                      <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border inline-block ${getPositionColor(peer?.relative_valuation_position, 'valuation')}`}>
                        {peer?.relative_valuation_position || 'In Line'}
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[10px] text-zinc-400 uppercase font-semibold">Relative Profitability</span>
                    <div className="mt-1">
                      <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border inline-block ${getPositionColor(peer?.relative_profitability_position, 'profitability')}`}>
                        {peer?.relative_profitability_position || 'In Line'}
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[10px] text-zinc-400 uppercase font-semibold">Relative Leverage</span>
                    <div className="mt-1">
                      <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border inline-block ${getPositionColor(peer?.relative_leverage_position, 'leverage')}`}>
                        {peer?.relative_leverage_position || 'In Line'}
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[10px] text-zinc-400 uppercase font-semibold">Financial Strength</span>
                    <div className="mt-1 flex items-center justify-between">
                      <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded border inline-block ${getPositionColor(peer?.relative_financial_strength_position, 'strength')}`}>
                        {peer?.relative_financial_strength_position || 'In Line'}
                      </span>
                      <span className="text-[9px] font-mono text-zinc-400">
                        {nonTargetPeers.length} Peers
                      </span>
                    </div>
                  </div>
                </div>

                {/* 2. Visual Comparative Charts */}
                {chartDataItems.length > 1 && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                    {/* Valuation Multiples Chart (P/E & P/B) */}
                    <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white flex items-center gap-1.5">
                          <BarChart3 className="h-3.5 w-3.5 text-cyan-400" />
                          Valuation Multiples Comparison
                        </span>
                        <div className="flex items-center gap-2 text-[9px] font-mono">
                          <span className="flex items-center gap-1 text-cyan-400">
                            <span className="h-2 w-2 rounded-full bg-cyan-400" /> Trailing P/E
                          </span>
                          <span className="flex items-center gap-1 text-purple-400">
                            <span className="h-2 w-2 rounded-full bg-purple-400" /> P/B
                          </span>
                        </div>
                      </div>
                      <div className="h-32 flex items-end justify-around gap-2 pt-3 px-1 border-b border-white/[0.04]">
                        {chartDataItems.map((item, idx) => {
                          const peVal = item.pe ?? 0;
                          const pbVal = item.pb ?? 0;
                          const peH = peVal > 0 ? Math.max(Math.round((peVal / maxPeVal) * 85), 6) : 0;
                          const pbH = pbVal > 0 ? Math.max(Math.round((pbVal / maxPbVal) * 85), 6) : 0;

                          return (
                            <div key={idx} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                              <div className="flex items-end justify-center gap-1 h-24 w-full px-1">
                                <div
                                  title={`${item.label} Trailing P/E: ${item.pe ? item.pe.toFixed(1) : 'N/A'}`}
                                  style={{ height: `${peH}%` }}
                                  className={`w-1/2 rounded-t-sm transition-all duration-300 ${
                                    item.isTarget
                                      ? 'bg-cyan-400 ring-1 ring-cyan-300'
                                      : item.isMedian
                                      ? 'bg-rose-400/80 border-dashed border-t border-rose-300'
                                      : 'bg-cyan-500/60 hover:bg-cyan-400'
                                  }`}
                                />
                                <div
                                  title={`${item.label} P/B: ${item.pb ? item.pb.toFixed(1) : 'N/A'}`}
                                  style={{ height: `${pbH}%` }}
                                  className={`w-1/2 rounded-t-sm transition-all duration-300 ${
                                    item.isTarget
                                      ? 'bg-purple-400 ring-1 ring-purple-300'
                                      : item.isMedian
                                      ? 'bg-rose-400/80 border-dashed border-t border-rose-300'
                                      : 'bg-purple-500/60 hover:bg-purple-400'
                                  }`}
                                />
                              </div>
                              <span
                                className={`text-[10px] font-mono truncate max-w-[65px] ${
                                  item.isTarget
                                    ? 'text-rose-400 font-bold'
                                    : item.isMedian
                                    ? 'text-amber-400 font-bold'
                                    : 'text-zinc-400'
                                }`}
                              >
                                {item.label}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>

                    {/* Profitability & Returns Chart (ROE, ROA & Net Margin) */}
                    <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex flex-col justify-between">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-bold text-white flex items-center gap-1.5">
                          <Activity className="h-3.5 w-3.5 text-emerald-400" />
                          Returns & Margins Comparison (%)
                        </span>
                        <div className="flex items-center gap-2 text-[9px] font-mono">
                          <span className="flex items-center gap-1 text-emerald-400">
                            <span className="h-2 w-2 rounded-full bg-emerald-400" /> ROE
                          </span>
                          <span className="flex items-center gap-1 text-amber-400">
                            <span className="h-2 w-2 rounded-full bg-amber-400" /> ROA
                          </span>
                          <span className="flex items-center gap-1 text-cyan-400">
                            <span className="h-2 w-2 rounded-full bg-cyan-400" /> Net %
                          </span>
                        </div>
                      </div>
                      <div className="h-32 flex items-end justify-around gap-2 pt-3 px-1 border-b border-white/[0.04]">
                        {chartDataItems.map((item, idx) => {
                          const roeVal = item.roe ?? 0;
                          const roaVal = item.roa ?? 0;
                          const nmVal = item.netMargin ?? 0;

                          const roeH = roeVal > 0 ? Math.max(Math.round((roeVal / maxProfVal) * 85), 6) : 0;
                          const roaH = roaVal > 0 ? Math.max(Math.round((roaVal / maxProfVal) * 85), 6) : 0;
                          const nmH = nmVal > 0 ? Math.max(Math.round((nmVal / maxProfVal) * 85), 6) : 0;

                          return (
                            <div key={idx} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                              <div className="flex items-end justify-center gap-0.5 h-24 w-full px-0.5">
                                <div
                                  title={`${item.label} ROE: ${item.roe ? `${item.roe.toFixed(1)}%` : 'N/A'}`}
                                  style={{ height: `${roeH}%` }}
                                  className={`w-1/3 rounded-t-sm transition-all duration-300 ${
                                    item.isTarget
                                      ? 'bg-emerald-400 ring-1 ring-emerald-300'
                                      : item.isMedian
                                      ? 'bg-rose-400/80'
                                      : 'bg-emerald-500/60 hover:bg-emerald-400'
                                  }`}
                                />
                                <div
                                  title={`${item.label} ROA: ${item.roa ? `${item.roa.toFixed(1)}%` : 'N/A'}`}
                                  style={{ height: `${roaH}%` }}
                                  className={`w-1/3 rounded-t-sm transition-all duration-300 ${
                                    item.isTarget
                                      ? 'bg-amber-400 ring-1 ring-amber-300'
                                      : item.isMedian
                                      ? 'bg-rose-400/80'
                                      : 'bg-amber-500/60 hover:bg-amber-400'
                                  }`}
                                />
                                <div
                                  title={`${item.label} Net Margin: ${item.netMargin ? `${item.netMargin.toFixed(1)}%` : 'N/A'}`}
                                  style={{ height: `${nmH}%` }}
                                  className={`w-1/3 rounded-t-sm transition-all duration-300 ${
                                    item.isTarget
                                      ? 'bg-cyan-400 ring-1 ring-cyan-300'
                                      : item.isMedian
                                      ? 'bg-rose-400/80'
                                      : 'bg-cyan-500/60 hover:bg-cyan-400'
                                  }`}
                                />
                              </div>
                              <span
                                className={`text-[10px] font-mono truncate max-w-[65px] ${
                                  item.isTarget
                                    ? 'text-rose-400 font-bold'
                                    : item.isMedian
                                    ? 'text-amber-400 font-bold'
                                    : 'text-zinc-400'
                                }`}
                              >
                                {item.label}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}

                {/* 3. Comprehensive Peer Benchmarking Table (11 Columns) */}
                <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-white/[0.03] text-zinc-400 uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="py-2.5 px-3">Ticker / Company</th>
                        <th className="py-2.5 px-3 text-right">Market Cap</th>
                        <th className="py-2.5 px-3 text-right">Trailing P/E</th>
                        <th className="py-2.5 px-3 text-right">Forward P/E</th>
                        <th className="py-2.5 px-3 text-right">P/B</th>
                        <th className="py-2.5 px-3 text-right">ROE</th>
                        <th className="py-2.5 px-3 text-right">ROA</th>
                        <th className="py-2.5 px-3 text-right">Op Margin</th>
                        <th className="py-2.5 px-3 text-right">Net Margin</th>
                        <th className="py-2.5 px-3 text-right">D/E</th>
                        <th className="py-2.5 px-3 text-right">Rev YoY</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                      {/* 1. Target Company Row (Always First) */}
                      {targetRow && (
                        <tr
                          key={targetRow.ticker}
                          className="bg-rose-500/10 border-l-2 border-rose-500 font-semibold text-white hover:bg-white/[0.02] transition-colors"
                        >
                          <td className="py-2.5 px-3">
                            <div className="flex items-center gap-1.5">
                              <span className="text-rose-400 font-bold">{targetRow.ticker}</span>
                              <span className="text-[9px] bg-rose-500/20 text-rose-300 px-1.5 py-0.2 rounded border border-rose-500/30">
                                Target
                              </span>
                            </div>
                            <div className="text-[10px] text-zinc-400 truncate max-w-[150px]">{targetRow.company_name}</div>
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-300">
                            {formatMarketCap(targetRow.market_cap)}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {targetRow.pe_ratio != null ? `${targetRow.pe_ratio.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-300">
                            {targetRow.forward_pe != null ? `${targetRow.forward_pe.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-300">
                            {targetRow.pb_ratio != null ? `${targetRow.pb_ratio.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium text-emerald-400">
                            {targetRow.roe != null ? `${targetRow.roe.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-amber-300">
                            {targetRow.roa != null ? `${targetRow.roa.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-purple-300">
                            {targetRow.operating_margin != null ? `${targetRow.operating_margin.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-cyan-300">
                            {targetRow.net_margin != null ? `${targetRow.net_margin.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {targetRow.debt_to_equity != null ? `${targetRow.debt_to_equity.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {targetRow.revenue_growth_yoy != null ? (
                              <span className={targetRow.revenue_growth_yoy >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                                {targetRow.revenue_growth_yoy >= 0 ? `+${targetRow.revenue_growth_yoy.toFixed(1)}%` : `${targetRow.revenue_growth_yoy.toFixed(1)}%`}
                              </span>
                            ) : (
                              <span className="text-zinc-500">—</span>
                            )}
                          </td>
                        </tr>
                      )}

                      {/* 2. Peer Companies Rows (Follow Target Company) */}
                      {nonTargetPeers.map((p) => (
                        <tr
                          key={p.ticker}
                          className="hover:bg-white/[0.02] transition-colors"
                        >
                          <td className="py-2.5 px-3">
                            <div className="flex items-center gap-1.5">
                              <span className="text-zinc-200">{p.ticker}</span>
                            </div>
                            <div className="text-[10px] text-zinc-400 truncate max-w-[150px]">{p.company_name}</div>
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-300">
                            {formatMarketCap(p.market_cap)}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {p.pe_ratio != null ? `${p.pe_ratio.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-300">
                            {p.forward_pe != null ? `${p.forward_pe.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-300">
                            {p.pb_ratio != null ? `${p.pb_ratio.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right font-medium text-emerald-400">
                            {p.roe != null ? `${p.roe.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-amber-300">
                            {p.roa != null ? `${p.roa.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-purple-300">
                            {p.operating_margin != null ? `${p.operating_margin.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right text-cyan-300">
                            {p.net_margin != null ? `${p.net_margin.toFixed(2)}%` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {p.debt_to_equity != null ? `${p.debt_to_equity.toFixed(2)}x` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {p.revenue_growth_yoy != null ? (
                              <span className={p.revenue_growth_yoy >= 0 ? 'text-emerald-400 font-semibold' : 'text-rose-400 font-semibold'}>
                                {p.revenue_growth_yoy >= 0 ? `+${p.revenue_growth_yoy.toFixed(1)}%` : `${p.revenue_growth_yoy.toFixed(1)}%`}
                              </span>
                            ) : (
                              <span className="text-zinc-500">—</span>
                            )}
                          </td>
                        </tr>
                      ))}

                      {/* 3. Industry Median Benchmark Row (At the Bottom) */}
                      {peer?.peer_median_pe !== null && peer?.peer_median_pe !== undefined && (
                        <tr className="bg-rose-950/25 border-t-2 border-rose-500/30 font-bold text-rose-300">
                          <td className="py-2.5 px-3">
                            <span className="font-bold text-amber-300">MEDIAN</span>
                            <span className="text-[10px] text-zinc-400 ml-1.5 font-normal">Industry Benchmark</span>
                          </td>
                          <td className="py-2.5 px-3 text-right text-zinc-500">—</td>
                          <td className="py-2.5 px-3 text-right">{peer.peer_median_pe.toFixed(2)}x</td>
                          <td className="py-2.5 px-3 text-right">{peer.peer_median_forward_pe != null ? `${peer.peer_median_forward_pe.toFixed(2)}x` : '—'}</td>
                          <td className="py-2.5 px-3 text-right">{peer.peer_median_pb != null ? `${peer.peer_median_pb.toFixed(2)}x` : '—'}</td>
                          <td className="py-2.5 px-3 text-right text-emerald-300">{peer.peer_median_roe != null ? `${peer.peer_median_roe.toFixed(2)}%` : '—'}</td>
                          <td className="py-2.5 px-3 text-right text-amber-300">{peer.peer_median_roa != null ? `${peer.peer_median_roa.toFixed(2)}%` : '—'}</td>
                          <td className="py-2.5 px-3 text-right text-purple-300">{peer.peer_median_operating_margin != null ? `${peer.peer_median_operating_margin.toFixed(2)}%` : '—'}</td>
                          <td className="py-2.5 px-3 text-right text-cyan-300">{peer.peer_median_net_margin != null ? `${peer.peer_median_net_margin.toFixed(2)}%` : '—'}</td>
                          <td className="py-2.5 px-3 text-right">{peer.peer_median_debt_to_equity != null ? `${peer.peer_median_debt_to_equity.toFixed(2)}x` : '—'}</td>
                          <td className="py-2.5 px-3 text-right">{peer.peer_median_revenue_growth != null ? `${peer.peer_median_revenue_growth >= 0 ? '+' : ''}${peer.peer_median_revenue_growth.toFixed(1)}%` : '—'}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* 4. Multi-Metric Factual Summary Narrative */}
                <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex items-start gap-2.5">
                  <Sparkles className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-zinc-300 leading-relaxed font-sans">{peer?.summary_narrative}</p>
                </div>
              </div>
            );
          })()}

          {/* TAB 7: Data Integrity Audit */}
          {activeTab === 'integrity' && (() => {
            // 1. Resolve multi-period balance audits with backward-compatibility fallback to hist.years
            const multiPeriodAudits = (audit?.multi_period_balance_audits && audit.multi_period_balance_audits.length > 0)
              ? audit.multi_period_balance_audits
              : (hist?.years && hist.years.length > 0)
              ? hist.years
                  .filter(y => y.total_assets && y.total_liabilities !== null && y.stockholders_equity !== null)
                  .map(y => {
                    const sumLE = (y.total_liabilities || 0) + (y.stockholders_equity || 0);
                    const diff = Math.abs((y.total_assets || 0) - sumLE);
                    const discPct = y.total_assets ? Number(((diff / y.total_assets) * 100).toFixed(2)) : 0;
                    return {
                      period: y.period,
                      total_assets: y.total_assets,
                      total_liabilities: y.total_liabilities,
                      stockholders_equity: y.stockholders_equity,
                      discrepancy_amount: diff,
                      discrepancy_pct: discPct,
                      equation_holds: discPct <= 2.0,
                      status: discPct <= 2.0 ? 'balanced' : 'discrepancy'
                    };
                  })
              : [];

            const evaluatedBsPeriods = multiPeriodAudits.filter(b => b.equation_holds !== null && b.equation_holds !== undefined);
            const evaluatedBsPeriodsCount = evaluatedBsPeriods.length;
            const hasEvaluatedBs = evaluatedBsPeriodsCount > 0;
            const bsHolds = hasEvaluatedBs && (
              audit?.balance_sheet_equation_holds !== undefined && audit?.balance_sheet_equation_holds !== null
                ? (audit.balance_sheet_equation_holds && evaluatedBsPeriods.every(b => b.equation_holds === true))
                : evaluatedBsPeriods.every(b => b.equation_holds === true)
            );
            const latestDiscPct = evaluatedBsPeriods[0]?.discrepancy_pct ?? audit?.balance_sheet_discrepancy_pct ?? null;

            // 2. Resolve currency integrity with rigorous cross-currency comparison
            const tradingCurr = (audit?.trading_currency || curr || 'USD').toUpperCase();
            const reportingCurr = (audit?.reporting_currency || stmtCurr || tradingCurr).toUpperCase();
            const isCurrencyMismatch = (audit?.currency_mismatch_detected === true) || (tradingCurr !== reportingCurr);

            // 3. Resolve audited periods count
            const auditedPeriodsList = (audit?.periods_audited && audit.periods_audited.length > 0)
              ? audit.periods_audited
              : (hist?.periods && hist.periods.length > 0)
              ? hist.periods
              : multiPeriodAudits.map(b => b.period);
            const periodsAuditedCount = auditedPeriodsList.length;

            return (
              <div className="space-y-4">
                {/* 1. Four Top KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                  {/* 1. Accounting Equation Audit */}
                  <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-2 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Accounting Equation</span>
                        {!hasEvaluatedBs ? (
                          <span className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-1.5 py-0.5 rounded border border-white/[0.06]">
                            Not Evaluated
                          </span>
                        ) : bsHolds ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                            <CheckCircle2 className="h-3 w-3" />
                            Balanced
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                            <AlertTriangle className="h-3 w-3" />
                            Discrepancy
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-mono text-white font-medium">Assets = Liab + Equity</div>
                      <div className="text-lg font-bold font-mono text-white mt-1">
                        {hasEvaluatedBs && latestDiscPct !== null && latestDiscPct !== undefined
                          ? `${latestDiscPct.toFixed(2)}%`
                          : '—'}
                      </div>
                    </div>
                    <p className="text-[10px] text-zinc-500 font-mono">
                      {hasEvaluatedBs
                        ? `${evaluatedBsPeriodsCount} balance sheet period${evaluatedBsPeriodsCount === 1 ? '' : 's'} evaluated`
                        : '0 balance sheet periods evaluated (insufficient data)'}
                    </p>
                  </div>

                {/* 2. Data Quality Score & Tier */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Quality Score</span>
                      <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${
                        (audit?.data_quality_tier || 'High Quality') === 'High Quality'
                          ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/25'
                          : (audit?.data_quality_tier) === 'Acceptable'
                          ? 'text-sky-400 bg-sky-500/10 border-sky-500/25'
                          : (audit?.data_quality_tier) === 'Caveats'
                          ? 'text-amber-400 bg-amber-500/10 border-amber-500/25'
                          : 'text-rose-400 bg-rose-500/10 border-rose-500/25'
                      }`}>
                        {audit?.data_quality_tier || 'High Quality'}
                      </span>
                    </div>
                    <div className="flex items-baseline gap-1.5 mt-1">
                      <span className="text-2xl font-bold font-mono text-white">
                        {audit?.data_quality_score !== undefined && audit?.data_quality_score !== null
                          ? Math.round(audit.data_quality_score)
                          : 100}
                      </span>
                      <span className="text-xs font-mono text-zinc-500">/ 100</span>
                    </div>
                  </div>
                  <div className="w-full bg-white/[0.05] rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        (audit?.data_quality_score || 0) >= 85
                          ? 'bg-emerald-500'
                          : (audit?.data_quality_score || 0) >= 70
                          ? 'bg-sky-500'
                          : (audit?.data_quality_score || 0) >= 50
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(0, audit?.data_quality_score || 0))}%` }}
                    />
                  </div>
                </div>

                {/* 3. Currency Integrity */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Currency Integrity</span>
                      {isCurrencyMismatch ? (
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                          <AlertTriangle className="h-3 w-3" />
                          Variance
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                          <CheckCircle2 className="h-3 w-3" />
                          Unified
                        </span>
                      )}
                    </div>
                    <div className="text-xs font-mono text-white font-medium">
                      Trading: <span className="text-zinc-300 font-bold">{tradingCurr}</span>
                    </div>
                    <div className="text-xs font-mono text-white font-medium mt-0.5">
                      Reporting: <span className="text-zinc-300 font-bold">{reportingCurr}</span>
                    </div>
                  </div>
                  <p className="text-[10px] text-zinc-500 font-mono">
                    {isCurrencyMismatch
                      ? `Cross-currency variance: ${tradingCurr} trading vs ${reportingCurr} reporting`
                      : `Unified currency verified (${tradingCurr})`}
                  </p>
                </div>

                {/* 4. Period Alignment & Sanity */}
                <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Period & Sanity</span>
                      <span className={`text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded border ${
                        periodsAuditedCount === 0
                          ? 'text-zinc-500 bg-zinc-800 border-white/[0.06]'
                          : (audit?.period_alignment_status || 'aligned') === 'aligned'
                          ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
                          : 'text-amber-400 bg-amber-500/10 border-amber-500/20'
                      }`}>
                        {periodsAuditedCount === 0 ? 'NO DATA' : (audit?.period_alignment_status || 'aligned').toUpperCase()}
                      </span>
                    </div>
                    <div className="text-xs font-mono text-zinc-300">
                      Periods Audited: <span className="font-bold text-white">{periodsAuditedCount}</span>
                    </div>
                    <div className="text-xs font-mono text-zinc-300 mt-0.5">
                      Sanity Alerts: <span className={`font-bold ${(audit?.suspicious_values_detected?.length || 0) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {audit?.suspicious_values_detected?.length || 0}
                      </span>
                    </div>
                  </div>
                  <p className="text-[10px] text-zinc-500 font-mono">
                    {periodsAuditedCount === 0
                      ? 'No historical periods available to audit'
                      : (audit?.suspicious_values_detected?.length || 0) === 0
                      ? 'Asset & revenue sanity verified'
                      : 'Anomalies flagged for review'}
                  </p>
                </div>
              </div>

              {/* 2. Audit Category Reliability Scores */}
              {audit?.category_scores && (
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                      Audit Category Reliability Scores
                    </h4>
                    <span className="text-[11px] font-mono text-zinc-400">
                      Overall Audit Status: <span className={`font-bold uppercase ${
                        audit?.overall_status === 'pass'
                          ? 'text-emerald-400'
                          : audit?.overall_status === 'caveats'
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}>{audit?.overall_status || 'PASS'}</span>
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {[
                      {
                        name: 'Completeness',
                        weight: '40% Weight',
                        score: audit.category_scores.completeness,
                        desc: 'Statements & line items presence',
                      },
                      {
                        name: 'Consistency',
                        weight: '30% Weight',
                        score: audit.category_scores.consistency,
                        desc: 'Balance equation & cross-checks',
                      },
                      {
                        name: 'Plausibility',
                        weight: '20% Weight',
                        score: audit.category_scores.plausibility,
                        desc: 'Assets > 0, cash, margin sanity',
                      },
                      {
                        name: 'Period Alignment',
                        weight: '10% Weight',
                        score: audit.category_scores.period_alignment,
                        desc: 'Temporal sync across statements',
                      },
                    ].map((cat) => (
                      <div key={cat.name} className="p-3 rounded-lg bg-[#0d0d15] border border-white/[0.04] space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-semibold text-zinc-300">{cat.name}</span>
                          <span className="text-[10px] font-mono text-zinc-500">{cat.weight}</span>
                        </div>
                        <div className="flex items-baseline justify-between">
                          <span className="text-lg font-bold font-mono text-white">{Math.round(cat.score ?? 100)}%</span>
                        </div>
                        <div className="w-full bg-white/[0.05] rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              (cat.score ?? 100) >= 85
                                ? 'bg-emerald-500'
                                : (cat.score ?? 100) >= 70
                                ? 'bg-sky-500'
                                : (cat.score ?? 100) >= 50
                                ? 'bg-amber-500'
                                : 'bg-rose-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.max(0, cat.score ?? 100))}%` }}
                          />
                        </div>
                        <p className="text-[10px] text-zinc-500 leading-tight">{cat.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Multi-Period Balance Sheet Verification Table */}
              {multiPeriodAudits && multiPeriodAudits.length > 0 && (
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <div>
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                        Multi-Period Balance Sheet Verification Table
                      </h4>
                      <p className="text-[11px] text-zinc-400 mt-0.5">
                        Mathematical accounting equation validation: Assets = Liabilities + Stockholders' Equity (tolerance: ≤ 2.0%).
                      </p>
                    </div>
                  </div>

                  <div className="overflow-x-auto rounded-lg border border-white/[0.06]">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="bg-white/[0.03] border-b border-white/[0.06] text-zinc-400 font-mono text-[11px]">
                          <th className="py-2.5 px-3 font-semibold">Fiscal Period</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Total Assets</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Total Liabilities</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Stockholders' Equity</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Liab + Equity</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Discrepancy ({reportingCurr})</th>
                          <th className="py-2.5 px-3 font-semibold text-right">Discrepancy %</th>
                          <th className="py-2.5 px-3 font-semibold text-center">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/[0.04] font-mono text-[11px]">
                        {multiPeriodAudits.map((item, idx) => {
                          const sumLE = (item.total_liabilities !== null && item.total_liabilities !== undefined && item.stockholders_equity !== null && item.stockholders_equity !== undefined)
                            ? item.total_liabilities + item.stockholders_equity
                            : null;
                          return (
                            <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                              <td className="py-2.5 px-3 font-bold text-zinc-200">{item.period}</td>
                              <td className="py-2.5 px-3 text-right text-zinc-300">{formatStatementNumber(item.total_assets)}</td>
                              <td className="py-2.5 px-3 text-right text-zinc-400">{formatStatementNumber(item.total_liabilities)}</td>
                              <td className="py-2.5 px-3 text-right text-zinc-400">{formatStatementNumber(item.stockholders_equity)}</td>
                              <td className="py-2.5 px-3 text-right text-zinc-300 font-semibold">{formatStatementNumber(sumLE)}</td>
                              <td className="py-2.5 px-3 text-right text-zinc-400">
                                {item.discrepancy_amount !== null && item.discrepancy_amount !== undefined
                                  ? formatStatementNumber(item.discrepancy_amount)
                                  : '—'}
                              </td>
                              <td className="py-2.5 px-3 text-right font-bold text-zinc-200">
                                {item.discrepancy_pct !== null && item.discrepancy_pct !== undefined
                                  ? `${item.discrepancy_pct.toFixed(2)}%`
                                  : '—'}
                              </td>
                              <td className="py-2.5 px-3 text-center">
                                {item.equation_holds === true ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                    <CheckCircle2 className="h-3 w-3" />
                                    Balanced
                                  </span>
                                ) : item.equation_holds === false ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                                    <AlertTriangle className="h-3 w-3" />
                                    Variance
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-mono text-zinc-500 bg-zinc-800 px-2 py-0.5 rounded border border-white/[0.06]">
                                    N/A
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* 4. Structured Audit Findings & Disclosures Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* Audit Findings & Inconsistencies */}
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                      Inconsistencies & Reconciliations
                    </h4>
                    <span className="text-[10px] font-mono text-zinc-400">
                      {audit?.inconsistent_items?.length || 0} issues
                    </span>
                  </div>
                  {audit?.inconsistent_items && audit.inconsistent_items.length > 0 ? (
                    <ul className="space-y-2 text-xs text-zinc-300">
                      {audit.inconsistent_items.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 p-2 rounded-lg bg-amber-500/5 border border-amber-500/15">
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-400 shrink-0 mt-0.5" />
                          <span className="leading-relaxed">{item}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/15 flex items-center gap-2 text-xs text-emerald-400">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>All cross-statement and breakdown reconciliations validated successfully.</span>
                    </div>
                  )}

                  {/* Suspicious Values if any */}
                  {audit?.suspicious_values_detected && audit.suspicious_values_detected.length > 0 && (
                    <div className="pt-2 border-t border-white/[0.06] space-y-2">
                      <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wide">
                        Plausibility & Sanity Alerts
                      </span>
                      <ul className="space-y-1.5 text-xs text-rose-300">
                        {audit.suspicious_values_detected.map((s, idx) => (
                          <li key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-rose-500/5 border border-rose-500/15">
                            <AlertTriangle className="h-3.5 w-3.5 text-rose-400 shrink-0 mt-0.5" />
                            <span>{s}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Missing Line Items & Currency Notes */}
                <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                      Completeness & Disclosures
                    </h4>
                    <span className="text-[10px] font-mono text-zinc-400">
                      {audit?.missing_line_items?.length || 0} unpopulated
                    </span>
                  </div>

                  {audit?.missing_line_items && audit.missing_line_items.length > 0 ? (
                    <div className="space-y-1.5">
                      <span className="text-[11px] text-zinc-400">Unpopulated or missing line items:</span>
                      <div className="flex flex-wrap gap-1.5">
                        {audit.missing_line_items.map((item, i) => (
                          <span key={i} className="text-[10px] font-mono text-zinc-300 bg-white/[0.04] px-2 py-0.5 rounded border border-white/[0.06]">
                            {item}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/15 flex items-center gap-2 text-xs text-emerald-400">
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                      <span>All 16 audited financial line items are populated across statements.</span>
                    </div>
                  )}

                  {/* Currency Disclosures */}
                  {(isCurrencyMismatch || audit?.currency_notes) && (
                    <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/15 flex items-start gap-2 text-xs text-amber-300">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
                      <span className="leading-relaxed">
                        {audit?.currency_notes || `Cross-currency reporting variance: Trading in ${tradingCurr} on exchange vs Financials reported in ${reportingCurr}. Valuation multiples (e.g., P/B) require unified currency conversions or ADR share ratio adjustments.`}
                      </span>
                    </div>
                  )}

                  {/* General Audit Warnings */}
                  {audit?.audit_warnings && audit.audit_warnings.length > 0 && (
                    <div className="space-y-1.5 pt-2 border-t border-white/[0.06]">
                      <span className="text-[11px] text-zinc-400 font-semibold uppercase">General Disclosures:</span>
                      <ul className="space-y-1 text-xs text-zinc-400">
                        {audit.audit_warnings.map((warn, i) => (
                          <li key={i} className="flex items-start gap-1.5">
                            <span className="text-zinc-500 mt-0.5">•</span>
                            <span className="leading-tight">{warn}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* 5. Factual Summary Narrative */}
              {audit?.summary_narrative && (
                <div className="p-3.5 rounded-xl bg-[#0a0a10] border border-white/[0.06] flex items-start gap-2.5">
                  <Sparkles className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <p className="text-xs text-zinc-300 leading-relaxed font-sans">{audit.summary_narrative}</p>
                </div>
              )}
            </div>
          );
        })()}
        </div>
      )}
    </div>
  );
}
