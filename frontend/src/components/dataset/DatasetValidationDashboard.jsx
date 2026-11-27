import React, { useState } from 'react';
import {
  Database,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Download,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Clock,
  Filter,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';

const QUICK_TICKERS = ['INFY.NS', 'TCS.NS', 'RELIANCE.NS', 'AAPL', 'MSFT', 'NVDA'];
const VALID_PERIODS = ['1mo', '3mo', '6mo', '1y', '2y', '5y', 'max'];

export default function DatasetValidationDashboard({ initialTicker } = {}) {
  const [tickerInput, setTickerInput] = useState(initialTicker || 'INFY.NS');
  const [period, setPeriod] = useState('1y');
  const [market, setMarket] = useState(() => {
    const sym = initialTicker || 'INFY.NS';
    if (sym.endsWith('.NS')) return 'NSE';
    if (sym.endsWith('.BO')) return 'BSE';
    return 'NASDAQ';
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'issues' | 'validated' | 'raw' | 'provenance'
  const [issueFilter, setIssueFilter] = useState('ALL'); // 'ALL' | 'ERROR' | 'WARNING'
  const [isExpanded, setIsExpanded] = useState(true);

  const handleQuickSelect = (sym) => {
    setTickerInput(sym);
    if (sym.endsWith('.NS')) setMarket('NSE');
    else if (sym.endsWith('.BO')) setMarket('BSE');
    else setMarket('NASDAQ');
  };

  const handleTriggerValidation = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    const cleanSym = tickerInput.trim().toUpperCase();
    if (!cleanSym) {
      setError('Please enter a valid stock ticker symbol.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/dataset/collect-and-validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ticker: cleanSym,
          period: period,
          market: market,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Failed to collect and validate dataset for ${cleanSym}`);
      }

      const json = await res.json();
      setReport(json);
    } catch (err) {
      setError(err.message || 'An error occurred during dataset collection and validation.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = (format) => {
    if (!report?.report_id) return;
    const url = `/api/dataset/reports/${report.report_id}/download?format=${format}`;
    window.open(url, '_blank');
  };

  const quality = report?.quality_metrics;
  const valSummary = report?.validated_summary;
  const rawSnap = report?.raw_snapshot;
  const aiNarrative = report?.ai_explanation;
  const issues = report?.issues || [];

  const filteredIssues = issues.filter((i) => {
    if (issueFilter === 'ALL') return true;
    return i.severity === issueFilter;
  });

  const getStatusBadge = (status) => {
    if (status === 'PASSED') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 shadow-sm">
          <CheckCircle2 className="h-3.5 w-3.5" />
          PASSED (Institutional Standard)
        </span>
      );
    }
    if (status === 'WARNING') {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-950/60 text-amber-400 border border-amber-800/60 shadow-sm">
          <AlertTriangle className="h-3.5 w-3.5" />
          WARNING (Documented Corrections)
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-950/60 text-rose-400 border border-rose-800/60 shadow-sm">
        <XCircle className="h-3.5 w-3.5" />
        FAILED (Unusable Dataset)
      </span>
    );
  };

  return (
    <section id="dataset-validation-section" className="space-y-4">
      {/* ── Outer Card ── */}
      <div className="glass-card p-5 sm:p-6 border border-white/[0.08] bg-[#0d0d13]/90 rounded-2xl space-y-5">
        {/* Header & Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-400 shadow-crimson-sm shrink-0">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-tight uppercase">
                  Module 2 Task 6 — Dataset Collection & Validation Agent
                </h3>
                <span className="text-[10px] font-mono font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                  Automated Pipeline
                </span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Automated multi-market OHLCV ingestion, 10-rule deterministic validation engine, and factual AI explanations.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setIsExpanded(!isExpanded)}
              className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
            >
              {isExpanded ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5" />
                  <span>Collapse</span>
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5" />
                  <span>Expand</span>
                </>
              )}
            </button>
          </div>
        </div>

        {isExpanded && (
          <div className="space-y-5 animate-fade-in">
            {/* Input & Trigger Toolbar */}
            <form onSubmit={handleTriggerValidation} className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                {/* Ticker Input */}
                <div className="md:col-span-2 space-y-1">
                  <label htmlFor="ticker-input" className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Stock Ticker / Symbol
                  </label>
                  <div className="relative">
                    <input
                      id="ticker-input"
                      type="text"
                      value={tickerInput}
                      onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
                      placeholder="e.g. INFY.NS, TCS.BO, AAPL, IBM"
                      disabled={loading}
                      className="w-full bg-[#12121a] border border-white/[0.08] focus:border-rose-500 rounded-lg px-3 py-2 text-xs font-mono text-white placeholder-zinc-500 transition-colors"
                    />
                  </div>
                </div>

                {/* Period Selector */}
                <div className="space-y-1">
                  <label htmlFor="period-selector" className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                    Historical Period
                  </label>
                  <select
                    id="period-selector"
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    disabled={loading}
                    className="w-full bg-[#12121a] border border-white/[0.08] focus:border-rose-500 rounded-lg px-3 py-2 text-xs font-mono text-white transition-colors"
                  >
                    {VALID_PERIODS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Action Trigger */}
                <div className="flex items-end">
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full btn-primary py-2 px-4 text-xs font-semibold flex items-center justify-center gap-2 h-[35px]"
                  >
                    {loading ? (
                      <>
                        <Spinner className="h-3.5 w-3.5 text-white" />
                        <span>Running Agent…</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="h-3.5 w-3.5" />
                        <span>Collect & Validate</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Preset Quick Chips */}
              <div className="flex flex-wrap items-center gap-1.5 pt-1">
                <span className="text-[10px] text-zinc-500 uppercase font-mono mr-1">Quick Presets:</span>
                {QUICK_TICKERS.map((sym) => (
                  <button
                    key={sym}
                    type="button"
                    onClick={() => handleQuickSelect(sym)}
                    disabled={loading}
                    className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors ${
                      tickerInput === sym
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-white/[0.03] text-zinc-400 hover:text-white hover:bg-white/[0.08] border border-white/[0.04]'
                    }`}
                  >
                    {sym}
                  </button>
                ))}
              </div>
            </form>

            {/* Error Banner */}
            {error && <AlertBanner type="error" message={error} />}

            {/* Report Display */}
            {report && (
              <div className="space-y-5 animate-fade-in">
                {/* Provenance Header & Status Bar */}
                <div className="p-4 rounded-xl bg-gradient-to-r from-rose-950/20 via-[#11111a] to-blue-950/20 border border-white/[0.08] flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-lg font-bold text-white font-mono tracking-tight">
                        {report.company_name} ({report.ticker})
                      </span>
                      {getStatusBadge(report.validation_status)}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-zinc-400 font-mono">
                      <span>Provider: <strong className="text-zinc-200">{report.active_provider}</strong></span>
                      <span>•</span>
                      <span>Market: <strong className="text-zinc-200">{report.market}</strong></span>
                      <span>•</span>
                      <span>Latency: <strong className="text-zinc-200">{report.latency_ms}ms</strong></span>
                      <span>•</span>
                      <span>Retrieved: <strong className="text-zinc-200">{new Date(report.retrieval_timestamp).toLocaleString()}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleDownload('json')}
                      className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
                      title="Download complete validation audit report as JSON"
                    >
                      <Download className="h-3.5 w-3.5 text-zinc-400" />
                      <span>Report (JSON)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDownload('csv')}
                      className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
                      title="Download validated OHLCV dataset as CSV"
                    >
                      <Download className="h-3.5 w-3.5 text-zinc-400" />
                      <span>Data (CSV)</span>
                    </button>
                  </div>
                </div>

                {/* 4-Card Bento Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {/* Card 1: Data Quality Score */}
                  <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Quality Score</span>
                      <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div className="mt-2">
                      <div className="text-2xl font-bold font-mono text-white">
                        {quality?.data_quality_score?.toFixed(1)}
                        <span className="text-xs text-zinc-500 font-normal"> / 100</span>
                      </div>
                      <div className="w-full bg-white/[0.05] rounded-full h-1.5 mt-2">
                        <div
                          className={`h-1.5 rounded-full transition-all ${
                            quality?.data_quality_score >= 95
                              ? 'bg-emerald-500'
                              : quality?.data_quality_score >= 70
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, quality?.data_quality_score || 0))}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono mt-2">Deterministic Formula</span>
                  </div>

                  {/* Card 2: Total Raw vs Valid Records */}
                  <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Valid Trading Sessions</span>
                    <div className="mt-2">
                      <div className="text-2xl font-bold font-mono text-white">
                        {quality?.valid_records}
                        <span className="text-xs text-zinc-500 font-normal"> / {quality?.total_raw_records}</span>
                      </div>
                      <div className="text-xs text-emerald-400 mt-1 font-mono">
                        {quality?.total_raw_records > 0
                          ? `${((quality.valid_records / quality.total_raw_records) * 100).toFixed(1)}% Accepted`
                          : '—'}
                      </div>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono mt-2">
                      {quality?.excluded_records} Excluded Records
                    </span>
                  </div>

                  {/* Card 3: Duplicate Dates */}
                  <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">Duplicate Dates</span>
                    <div className="mt-2">
                      <div className="text-2xl font-bold font-mono text-white">
                        {quality?.duplicate_dates_count}
                      </div>
                      <div className={`text-xs mt-1 font-mono ${quality?.duplicate_dates_count > 0 ? 'text-amber-400' : 'text-zinc-400'}`}>
                        {quality?.duplicate_dates_count > 0 ? 'Canonical Kept' : 'Zero Duplicates'}
                      </div>
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono mt-2">Fully Logged & Preserved</span>
                  </div>

                  {/* Card 4: 52-Week Metrics Status */}
                  <div className="p-3.5 rounded-xl bg-[#09090e] border border-white/[0.06] flex flex-col justify-between">
                    <span className="text-[11px] text-zinc-400 uppercase tracking-wider font-semibold">52-Week Metrics</span>
                    <div className="mt-2">
                      {valSummary?.fifty_two_week_metrics?.status === 'verified' ? (
                        <div>
                          <div className="text-xs font-mono font-bold text-white">
                            H: {valSummary.fifty_two_week_metrics.high} | L: {valSummary.fifty_two_week_metrics.low}
                          </div>
                          <span className="text-[10px] text-emerald-400 font-mono">
                            Verified ({valSummary.fifty_two_week_metrics.valid_trading_days} days)
                          </span>
                        </div>
                      ) : (
                        <div>
                          <div className="text-xs font-mono font-semibold text-zinc-400">Unavailable</div>
                          <span className="text-[10px] text-zinc-500 font-mono">Requires &ge; 250 days</span>
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] text-zinc-500 font-mono mt-2">
                      Coverage: {valSummary?.fifty_two_week_metrics?.valid_trading_days || 0} Sessions
                    </span>
                  </div>
                </div>

                {/* AI Narrative Card */}
                {aiNarrative && (
                  <div className="p-4 rounded-xl bg-[#0a0a10] border border-white/[0.06] space-y-3">
                    <div className="flex items-center gap-2 pb-2 border-b border-white/[0.04]">
                      <Sparkles className="h-4 w-4 text-rose-400" />
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                        AI Data Quality & Anomaly Synthesis (Institutional Interpretation)
                      </h4>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs leading-relaxed">
                      <div className="space-y-1">
                        <span className="font-semibold text-zinc-300">Executive Summary:</span>
                        <p className="text-zinc-400">{aiNarrative.executive_summary}</p>
                      </div>
                      <div className="space-y-1">
                        <span className="font-semibold text-zinc-300">Market Anomaly Context:</span>
                        <p className="text-zinc-400">{aiNarrative.market_anomaly_interpretation}</p>
                      </div>
                      <div className="space-y-1">
                        <span className="font-semibold text-zinc-300">Cleaning Transparency:</span>
                        <p className="text-zinc-400">{aiNarrative.cleaning_transparency_notes}</p>
                      </div>
                      <div className="space-y-1">
                        <span className="font-semibold text-zinc-300">Research Readiness:</span>
                        <p className="text-zinc-400">{aiNarrative.research_readiness_assessment}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Detailed Navigation Tabs */}
                <div className="flex flex-wrap items-center gap-1.5 pb-2 border-b border-white/[0.06]">
                  {[
                    { id: 'overview', label: `Issues & Audit Log (${issues.length})`, icon: AlertTriangle },
                    { id: 'validated', label: `Clean Valid Dataset (${valSummary?.valid_records_count || 0})`, icon: CheckCircle2 },
                    { id: 'raw', label: `Raw Snapshot (${rawSnap?.total_records || 0})`, icon: Database },
                    { id: 'provenance', label: 'Provider Attempt Log', icon: Clock },
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

                {/* TAB 1: Issues & Audit Log */}
                {activeTab === 'overview' && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between pb-2">
                      <div className="flex items-center gap-1 text-xs text-zinc-400">
                        <Filter className="h-3.5 w-3.5" />
                        <span>Filter by Severity:</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {['ALL', 'ERROR', 'WARNING'].map((f) => (
                          <button
                            key={f}
                            type="button"
                            onClick={() => setIssueFilter(f)}
                            className={`px-2 py-0.5 text-[10px] font-mono rounded ${
                              issueFilter === f
                                ? 'bg-white/[0.1] text-white font-bold border border-white/[0.2]'
                                : 'text-zinc-500 hover:text-zinc-300'
                            }`}
                          >
                            {f}
                          </button>
                        ))}
                      </div>
                    </div>

                    {filteredIssues.length > 0 ? (
                      <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                        <table className="w-full text-left text-xs font-mono">
                          <thead className="bg-white/[0.03] text-zinc-400 uppercase tracking-wider text-[10px]">
                            <tr>
                              <th className="py-2.5 px-3">Row</th>
                              <th className="py-2.5 px-3">Date</th>
                              <th className="py-2.5 px-3">Column</th>
                              <th className="py-2.5 px-3">Issue Type</th>
                              <th className="py-2.5 px-3">Severity</th>
                              <th className="py-2.5 px-3">Action Taken</th>
                              <th className="py-2.5 px-3">Message</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                            {filteredIssues.map((issue, idx) => (
                              <tr key={idx} className="hover:bg-white/[0.02]">
                                <td className="py-2 px-3 text-zinc-400">{issue.row_index >= 0 ? issue.row_index : '—'}</td>
                                <td className="py-2 px-3 font-semibold text-white">{issue.date || '—'}</td>
                                <td className="py-2 px-3 text-zinc-300">{issue.column}</td>
                                <td className="py-2 px-3 text-rose-300">{issue.issue_type}</td>
                                <td className="py-2 px-3">
                                  <span
                                    className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                                      issue.severity === 'ERROR'
                                        ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                    }`}
                                  >
                                    {issue.severity}
                                  </span>
                                </td>
                                <td className="py-2 px-3 text-[11px] text-zinc-400">{issue.action_taken}</td>
                                <td className="py-2 px-3 text-xs text-zinc-300">{issue.message}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-[#09090e] border border-white/[0.06] text-center text-xs text-emerald-400 flex items-center justify-center gap-2">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Zero validation defects or warnings for this filter. Dataset is 100% clean.</span>
                      </div>
                    )}
                  </div>
                )}

                {/* TAB 2: Cleaned Valid Dataset */}
                {activeTab === 'validated' && (
                  <div className="space-y-3">
                    <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-white/[0.03] text-zinc-400 uppercase tracking-wider text-[10px]">
                          <tr>
                            <th className="py-2.5 px-3">Date</th>
                            <th className="py-2.5 px-3">Open</th>
                            <th className="py-2.5 px-3">High</th>
                            <th className="py-2.5 px-3">Low</th>
                            <th className="py-2.5 px-3">Close</th>
                            <th className="py-2.5 px-3">Volume</th>
                            <th className="py-2.5 px-3 text-right">Source Row</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                          {(valSummary?.candles_sample || []).map((c, i) => (
                            <tr key={i} className="hover:bg-white/[0.02]">
                              <td className="py-2 px-3 font-semibold text-white">{c.Date}</td>
                              <td className="py-2 px-3 text-zinc-300">{c.Open}</td>
                              <td className="py-2 px-3 text-emerald-400">{c.High}</td>
                              <td className="py-2 px-3 text-rose-400">{c.Low}</td>
                              <td className="py-2 px-3 font-bold text-white">{c.Close}</td>
                              <td className="py-2 px-3 text-zinc-400">{c.Volume?.toLocaleString()}</td>
                              <td className="py-2 px-3 text-right text-zinc-500 font-mono">#{c.source_row_id}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* TAB 3: Raw Snapshot Audit */}
                {activeTab === 'raw' && (
                  <div className="space-y-3">
                    <div className="p-3 rounded-xl bg-[#09090e] border border-white/[0.06] text-xs font-mono flex flex-wrap items-center justify-between gap-2">
                      <span className="text-zinc-400">
                        SHA-256 Checksum: <code className="text-rose-400 select-all">{rawSnap?.sha256_hash}</code>
                      </span>
                      <span className="text-zinc-500">Immutable Raw Freeze</span>
                    </div>

                    <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-white/[0.03] text-zinc-400 uppercase tracking-wider text-[10px]">
                          <tr>
                            <th className="py-2.5 px-3">Raw ID</th>
                            {(rawSnap?.columns || []).map((col) => (
                              <th key={col} className="py-2.5 px-3">
                                {col}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                          {(rawSnap?.records_sample || []).map((r, i) => (
                            <tr key={i} className="hover:bg-white/[0.02]">
                              <td className="py-2 px-3 text-zinc-500">#{r._raw_row_id}</td>
                              {(rawSnap?.columns || []).map((col) => (
                                <td key={col} className="py-2 px-3">
                                  {r[col] !== null && r[col] !== undefined ? String(r[col]) : <span className="text-rose-500 font-bold">null</span>}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* TAB 4: Provider Provenance */}
                {activeTab === 'provenance' && (
                  <div className="space-y-3">
                    <div className="overflow-x-auto rounded-xl border border-white/[0.08]">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-white/[0.03] text-zinc-400 uppercase tracking-wider text-[10px]">
                          <tr>
                            <th className="py-2.5 px-3">Provider</th>
                            <th className="py-2.5 px-3">Market</th>
                            <th className="py-2.5 px-3">Status</th>
                            <th className="py-2.5 px-3">Latency</th>
                            <th className="py-2.5 px-3">Records</th>
                            <th className="py-2.5 px-3">Message</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                          {(report.provider_attempts || []).map((att, i) => (
                            <tr key={i} className="hover:bg-white/[0.02]">
                              <td className="py-2 px-3 font-semibold text-white">{att.provider}</td>
                              <td className="py-2 px-3 text-zinc-300">{att.market}</td>
                              <td className="py-2 px-3">
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                                    att.status === 'SUCCESS'
                                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                                  }`}
                                >
                                  {att.status}
                                </span>
                              </td>
                              <td className="py-2 px-3 text-zinc-300">{att.latency_ms ? `${att.latency_ms}ms` : '—'}</td>
                              <td className="py-2 px-3 text-zinc-300">{att.records_retrieved}</td>
                              <td className="py-2 px-3 text-zinc-400 text-xs">{att.message}</td>
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
    </section>
  );
}
