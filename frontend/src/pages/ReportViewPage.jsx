import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  Calendar,
  Globe2,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Cpu,
  Layers,
  FileText,
  AlertTriangle,
  ExternalLink,
  DollarSign,
  Activity,
  BarChart3,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/common/StatusBadge';

export default function ReportViewPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();

  const [task, setTask] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReportData = async () => {
      try {
        const [taskRes, reportRes] = await Promise.all([
          api.get(`/research/${taskId}`),
          api.get(`/research/${taskId}/report`),
        ]);
        setTask(taskRes.data);
        setReport(reportRes.data);
      } catch (err) {
        console.error('Failed to load research report:', err);
        const msg = err.response?.data?.detail || 'Unable to open research report.';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchReportData();
  }, [taskId]);

  if (loading) {
    return (
      <div className="py-20 text-center space-y-4">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm text-slate-500 font-medium">
          Retrieving research dossier & multi-agent metrics...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12 max-w-xl mx-auto text-center space-y-4">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Unable to Display Report</h2>
        <p className="text-sm text-slate-600">{error}</p>
        <Link
          to="/history"
          className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-xl text-xs font-semibold hover:bg-slate-800 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Research History
        </Link>
      </div>
    );
  }

  const content = report?.report_content || {};
  const meta = content.meta || {};
  const metrics = content.market_metrics || {};
  const perf = content.period_performance || {};
  const pipeline = content.multi_agent_pipeline || {};

  const isPositiveChange = (metrics.period_change_pct || 0) >= 0;

  return (
    <div className="space-y-8 animate-fade-in pb-16 max-w-6xl mx-auto">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/history')}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-50 transition-colors shadow-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to History
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Dossier ID:</span>
          <span className="font-mono text-xs font-bold px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700">
            QA-TASK-{task?.task_id}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white p-6 sm:p-8 rounded-3xl shadow-xl shadow-slate-900/20 border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-400/30">
                {task?.market}
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-slate-300 text-xs font-medium">Horizon: {task?.analysis_period}</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight flex items-baseline gap-3">
              <span>{task?.company_name}</span>
              <span className="text-xl text-blue-400 font-mono font-bold">({task?.ticker})</span>
            </h1>
            <p className="mt-1 text-xs text-slate-400 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              Analyzed on{' '}
              {meta.generated_at
                ? new Date(meta.generated_at).toLocaleString()
                : new Date(task?.created_at).toLocaleString()}
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm p-4 rounded-2xl border border-white/10 text-right min-w-[200px]">
            <span className="text-xs text-slate-300 uppercase tracking-wider block font-medium">
              Current Market Price
            </span>
            <div className="text-2xl font-black text-white mt-0.5">
              {metrics.currency === 'INR' ? '₹' : '$'}
              {metrics.current_price !== undefined ? metrics.current_price : 'N/A'}
            </div>
            {metrics.period_change_pct !== undefined && metrics.period_change_pct !== null && (
              <div
                className={`inline-flex items-center gap-1 text-xs font-bold mt-1 px-2 py-0.5 rounded-full ${
                  isPositiveChange
                    ? 'bg-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/20 text-rose-300'
                }`}
              >
                {isPositiveChange ? (
                  <TrendingUp className="w-3 h-3 stroke-[3]" />
                ) : (
                  <TrendingDown className="w-3 h-3 stroke-[3]" />
                )}
                <span>
                  {isPositiveChange ? '+' : ''}
                  {metrics.period_change_pct}% ({task?.analysis_period})
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            P/E Ratio
          </span>
          <div className="text-xl font-extrabold text-slate-900">
            {metrics.pe_ratio && metrics.pe_ratio !== 'N/A'
              ? typeof metrics.pe_ratio === 'number'
                ? metrics.pe_ratio.toFixed(2)
                : metrics.pe_ratio
              : 'N/A'}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">Valuation multiple</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Market Capitalization
          </span>
          <div className="text-xl font-extrabold text-slate-900">
            {metrics.market_cap && typeof metrics.market_cap === 'number'
              ? metrics.currency === 'INR'
                ? `₹${(metrics.market_cap / 1e7).toFixed(1)} Cr`
                : `$${(metrics.market_cap / 1e9).toFixed(2)}B`
              : 'N/A'}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">Total equity value</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            52-Week Range
          </span>
          <div className="text-sm font-bold text-slate-900">
            {metrics.fifty_two_week_low ? `${metrics.currency === 'INR' ? '₹' : '$'}${metrics.fifty_two_week_low}` : 'N/A'} -{' '}
            {metrics.fifty_two_week_high ? `${metrics.currency === 'INR' ? '₹' : '$'}${metrics.fifty_two_week_high}` : 'N/A'}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">Annual price bounds</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Industry / Sector
          </span>
          <div className="text-sm font-bold text-slate-900 truncate" title={metrics.sector}>
            {metrics.sector || 'General Equity'}
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5 truncate">{metrics.industry || 'Capital Markets'}</p>
        </div>
      </div>

      {/* Company Business Overview */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-3">
        <div className="flex items-center gap-2.5 pb-2 border-b border-slate-100">
          <Building2 className="w-5 h-5 text-blue-600" />
          <h2 className="text-base font-bold text-slate-900">Company Profile & Operations</h2>
        </div>
        <p className="text-sm text-slate-700 leading-relaxed pt-1">
          {content.company_overview || 'No extended business summary provided by market feed.'}
        </p>
      </div>

      {/* Historical Trend Sample */}
      {perf.recent_history && perf.recent_history.length > 0 && (
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <BarChart3 className="w-5 h-5 text-indigo-600" />
              <h2 className="text-base font-bold text-slate-900">
                Recent Trading Trend ({task?.analysis_period} horizon)
              </h2>
            </div>
            <span className="text-xs text-slate-400 font-medium">Verified Historical Samples</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-xs font-semibold text-slate-400 border-b border-slate-100">
                  <th className="py-2.5 px-3">Date</th>
                  <th className="py-2.5 px-3">Close Price</th>
                  <th className="py-2.5 px-3">Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {perf.recent_history.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    <td className="py-2.5 px-3 text-xs text-slate-600 font-mono">{row.date}</td>
                    <td className="py-2.5 px-3 text-xs font-bold text-slate-900">
                      {metrics.currency === 'INR' ? '₹' : '$'}
                      {row.close}
                    </td>
                    <td className="py-2.5 px-3 text-xs text-slate-500 font-mono">
                      {row.volume.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Multi-Agent Architecture Execution Dossier */}
      <div className="bg-slate-900 text-white p-6 sm:p-8 rounded-3xl border border-slate-800 shadow-xl space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-blue-500/20 text-blue-400 border border-blue-500/30">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold">Multi-Agent Pipeline Orchestration</h2>
              <p className="text-xs text-slate-400">
                Modular multi-agent coordination architecture (Module 1 Integration Interface)
              </p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            Pipeline Verified
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pipeline.active_agents?.map((agent, index) => (
            <div
              key={agent.agent_id}
              className="p-4 rounded-2xl bg-slate-800/60 border border-slate-700/60 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-400 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  {agent.agent_id}
                </span>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    agent.status === 'COMPLETED'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                  }`}
                >
                  {agent.status}
                </span>
              </div>
              <p className="text-xs font-bold text-white">{agent.role}</p>
              <p className="text-[11px] text-slate-400 leading-relaxed">{agent.summary}</p>
            </div>
          ))}
        </div>

        <div className="p-4 rounded-2xl bg-blue-950/40 border border-blue-900/60 text-xs text-blue-200 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            This analytical dossier is generated by the Module 1 integration pipeline using real market data feeds. Additional autonomous multi-agent stock analysis modules (e.g. LLM Valuation Agents, SEC Filing Scrapers, Social Sentiment Swarms) connect directly into this service layer without architectural restructuring.
          </p>
        </div>
      </div>
    </div>
  );
}

