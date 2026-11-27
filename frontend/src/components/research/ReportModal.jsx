import React, { useState, useEffect } from 'react';
import {
  X,
  FileText,
  TrendingUp,
  ShieldCheck,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';
import FinancialStatementsView from './FinancialStatementsView';
import FundamentalAnalysisView from './FundamentalAnalysisView';

export default function ReportModal({ taskId, onClose, onLoadStock }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  useEffect(() => {
    if (!taskId) return;
    let isMounted = true;
    const controller = new AbortController();

    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/research/tasks/${taskId}`, {
          credentials: 'include',
          signal: controller.signal,
        });
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || 'Failed to load research report.');
        }
        const json = await res.json();
        if (isMounted) {
          setData(json);
        }
      } catch (err) {
        if (err.name !== 'AbortError' && isMounted) {
          setError(err.message || 'An error occurred while loading report details.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchDetail();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [taskId]);

  const task = data?.task;
  const report = data?.report;
  const overview = report?.overview_data;
  const history = report?.history_data;
  const financials = report?.report_content?.financial_statements;
  const fundamental = report?.report_content?.fundamental_analysis;

  const isPriceUp = overview?.current_price >= overview?.previous_close;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto bg-black/75 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-modal-title"
    >
      <div
        className="glass-card relative w-full max-w-4xl max-h-[90vh] overflow-y-auto p-6 sm:p-8 bg-[#0d0d14]/95 border border-white/[0.1] shadow-2xl shadow-black rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-start justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-rose-950/60 to-black/80 border border-rose-500/30 text-rose-500 shadow-crimson-sm">
              <FileText className="h-6 w-6 text-rose-500" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase font-semibold text-rose-400 tracking-wider">
                  Verified Research Report #{taskId}
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
                  <CheckCircle2 className="h-3 w-3" />
                  Completed
                </span>
              </div>
              <h2 id="report-modal-title" className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                {task?.company_name || 'Stock Research Report'}
              </h2>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.08] transition-colors"
            aria-label="Close report modal"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="mt-6 space-y-6">
          {error && <AlertBanner message={error} variant="error" />}

          {loading && (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Spinner className="h-8 w-8 text-rose-500" />
              <p className="text-sm text-zinc-400">Loading saved research findings from database…</p>
            </div>
          )}

          {!loading && overview && (
            <>
              {/* Overview Snapshot */}
              <div className="glass-card p-5 bg-[#13131b]/90 border border-white/[0.08] flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-bold text-white bg-white/[0.08] px-2.5 py-0.5 rounded border border-white/[0.15]">
                      {task?.ticker}
                    </span>
                    <span className="text-xs text-zinc-300 font-medium">
                      Market: {task?.market} • Period: {task?.requested_period}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 mt-1">
                    {overview.sector} {overview.industry ? `• ${overview.industry}` : ''}
                  </p>
                  <p className="text-[11px] text-zinc-500 mt-0.5 font-mono">
                    Research recorded: {task?.created_at ? new Date(task.created_at).toLocaleString() : 'N/A'}
                  </p>
                </div>

                <div className="text-left sm:text-right">
                  <div className="text-2xl font-mono font-extrabold text-white flex items-center sm:justify-end gap-1.5">
                    <span>
                      {overview.currency === 'INR' ? '₹' : '$'}
                      {overview.current_price?.toLocaleString() || 'N/A'}
                    </span>
                    {isPriceUp ? (
                      <ArrowUpRight className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <ArrowDownRight className="h-5 w-5 text-rose-400" />
                    )}
                  </div>
                  <span className="text-xs text-zinc-400">
                    Previous Close: {overview.currency === 'INR' ? '₹' : '$'}{overview.previous_close || 'N/A'}
                  </span>
                </div>
              </div>

              {/* Fundamental Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="glass-card p-3.5 bg-[#13131b]/80 border border-white/[0.08]">
                  <span className="text-[11px] text-zinc-400 font-medium">Day Range</span>
                  <p className="text-sm font-mono font-bold text-white mt-1">
                    {overview.day_low || 'N/A'} - {overview.day_high || 'N/A'}
                  </p>
                </div>
                <div className="glass-card p-3.5 bg-[#13131b]/80 border border-white/[0.08]">
                  <span className="text-[11px] text-zinc-400 font-medium">52-Week Range</span>
                  <p className="text-sm font-mono font-bold text-white mt-1">
                    {overview.fifty_two_week_low || 'N/A'} - {overview.fifty_two_week_high || 'N/A'}
                  </p>
                </div>
                <div className="glass-card p-3.5 bg-[#13131b]/80 border border-white/[0.08]">
                  <span className="text-[11px] text-zinc-400 font-medium">P/E Ratio</span>
                  <p className="text-sm font-mono font-bold text-rose-400 mt-1">
                    {overview.pe_ratio || 'N/A'}
                  </p>
                </div>
                <div className="glass-card p-3.5 bg-[#13131b]/80 border border-white/[0.08]">
                  <span className="text-[11px] text-zinc-400 font-medium">Volume</span>
                  <p className="text-sm font-mono font-bold text-white mt-1">
                    {overview.volume ? overview.volume.toLocaleString() : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Data Pipeline Verification Telemetry */}
              {history?.validation && (
                <div className="glass-card p-4 border border-rose-950/40 bg-[#120e14]/60">
                  <div className="flex items-center gap-2 mb-2.5">
                    <ShieldCheck className="h-4 w-4 text-rose-400" />
                    <h4 className="text-xs font-bold text-white">
                      Market Data Quality Telemetry (Persisted Artifact)
                    </h4>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                    <div className="bg-[#0a0a0f] p-2.5 rounded-lg border border-white/[0.06]">
                      <span className="text-zinc-400">Total Raw:</span>
                      <p className="font-bold text-white">{history.validation.total_raw_records}</p>
                    </div>
                    <div className="bg-[#0a0a0f] p-2.5 rounded-lg border border-white/[0.06]">
                      <span className="text-zinc-400">Clean Records:</span>
                      <p className="font-bold text-emerald-400">{history.validation.cleaned_records}</p>
                    </div>
                    <div className="bg-[#0a0a0f] p-2.5 rounded-lg border border-white/[0.06]">
                      <span className="text-zinc-400">Duplicates Filtered:</span>
                      <p className="font-bold text-white">{history.validation.duplicates_removed}</p>
                    </div>
                    <div className="bg-[#0a0a0f] p-2.5 rounded-lg border border-white/[0.06]">
                      <span className="text-zinc-400">Order Integrity:</span>
                      <p className="font-bold text-rose-400">
                        {history.validation.is_chronological ? 'Strict Ascending' : 'Reordered'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Historical Candles Sample */}
              {history?.candles && history.candles.length > 0 && (
                <div className="glass-card p-4 border border-white/[0.08]">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2.5">
                    Verified OHLCV Trading Candles Sample ({history.candles.length} Days)
                  </h4>
                  <div className="overflow-x-auto max-h-48 rounded-xl border border-white/[0.08]">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-white/[0.03] text-zinc-400 sticky top-0 uppercase tracking-wider text-[10px]">
                        <tr>
                          <th className="py-2.5 px-3">Date</th>
                          <th className="py-2.5 px-3">Open</th>
                          <th className="py-2.5 px-3">High</th>
                          <th className="py-2.5 px-3">Low</th>
                          <th className="py-2.5 px-3">Close</th>
                          <th className="py-2.5 px-3">Volume</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
                        {history.candles.slice(-10).reverse().map((c, idx) => {
                          const openNum = typeof (c.open ?? c.Open) === 'number' ? (c.open ?? c.Open) : Number(c.open ?? c.Open);
                          const highNum = typeof (c.high ?? c.High) === 'number' ? (c.high ?? c.High) : Number(c.high ?? c.High);
                          const lowNum = typeof (c.low ?? c.Low) === 'number' ? (c.low ?? c.Low) : Number(c.low ?? c.Low);
                          const closeNum = typeof (c.close ?? c.Close) === 'number' ? (c.close ?? c.Close) : Number(c.close ?? c.Close);
                          const volNum = typeof (c.volume ?? c.Volume) === 'number' ? (c.volume ?? c.Volume) : Number(c.volume ?? c.Volume);

                          const dateStr = c.date ?? c.Date ?? 'N/A';
                          const openStr = !Number.isNaN(openNum) && Number.isFinite(openNum) ? openNum.toFixed(2) : 'N/A';
                          const highStr = !Number.isNaN(highNum) && Number.isFinite(highNum) ? highNum.toFixed(2) : 'N/A';
                          const lowStr = !Number.isNaN(lowNum) && Number.isFinite(lowNum) ? lowNum.toFixed(2) : 'N/A';
                          const closeStr = !Number.isNaN(closeNum) && Number.isFinite(closeNum) ? closeNum.toFixed(2) : 'N/A';
                          const volStr = !Number.isNaN(volNum) && Number.isFinite(volNum) ? Math.round(volNum).toLocaleString() : 'N/A';

                          return (
                            <tr key={c.date ?? c.Date ?? idx} className="hover:bg-white/[0.03] transition-colors">
                              <td className="py-2 px-3 font-semibold text-zinc-300">{dateStr}</td>
                              <td className="py-2 px-3">{openStr}</td>
                              <td className="py-2 px-3 text-emerald-400">{highStr}</td>
                              <td className="py-2 px-3 text-rose-400">{lowStr}</td>
                              <td className="py-2 px-3 font-bold text-white">{closeStr}</td>
                              <td className="py-2 px-3 text-zinc-400">{volStr}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Business Summary */}
              {overview.business_summary && (
                <div className="glass-card p-4 border border-white/[0.08]">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-1.5">
                    Company Profile & Operations Summary
                  </h4>
                  <p className="text-xs text-zinc-300 leading-relaxed max-h-36 overflow-y-auto">
                    {overview.business_summary}
                  </p>
                </div>
              )}

              {/* Financial Statements (if archived in report) */}
              {financials && (
                <FinancialStatementsView
                  financials={financials}
                  currency={overview?.currency || financials?.currency || 'USD'}
                  ticker={task?.ticker}
                />
              )}

              {/* Fundamental Analysis (Module 3 - if archived in report) */}
              {fundamental && (
                <FundamentalAnalysisView
                  fundamental={fundamental}
                  currency={overview?.currency || fundamental?.currency || 'USD'}
                  ticker={task?.ticker}
                />
              )}

              {/* Data Limitations & Disclaimers (Task 4 Compliance) */}
              {report?.limitations && (
                <div className="glass-card p-4 border border-rose-950/40 bg-rose-950/15">
                  <div className="flex items-center gap-2 mb-1.5">
                    <AlertTriangle className="h-4 w-4 text-rose-400" />
                    <h4 className="text-xs font-bold text-rose-300 uppercase tracking-wider">
                      Data Limitations & Disclaimers
                    </h4>
                  </div>
                  <p className="text-xs text-zinc-300 leading-relaxed">
                    {report.limitations}
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="mt-6 pt-4 border-t border-white/[0.08] flex flex-wrap items-center justify-between gap-3">
          <span className="text-xs text-zinc-500 font-mono">
            Report stored in PostgreSQL table <code className="text-rose-400">research_reports</code>
          </span>

          <div className="flex items-center gap-2">
            {onLoadStock && task?.ticker && (
              <button
                type="button"
                onClick={() => {
                  onLoadStock(task.ticker, task.requested_period);
                  onClose();
                }}
                className="btn-primary text-xs py-2 px-4 flex items-center gap-1.5"
              >
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Load in Active Dashboard</span>
              </button>
            )}
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary text-xs py-2 px-4"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

