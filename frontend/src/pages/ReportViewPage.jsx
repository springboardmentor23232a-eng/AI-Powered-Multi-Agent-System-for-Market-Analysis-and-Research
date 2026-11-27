import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Building2,
  Calendar,
  TrendingUp,
  TrendingDown,
  ShieldCheck,
  Cpu,
  AlertTriangle,
  Download,
  Activity,
  PieChart,
  Database,
  FileText,
} from 'lucide-react';
import api from '../api/client';
import FundamentalPanel from '../components/analysis/FundamentalPanel';
import TechnicalPanel from '../components/analysis/TechnicalPanel';
import DataQualityPanel from '../components/analysis/DataQualityPanel';

export default function ReportViewPage() {
  const { taskId } = useParams();
  const navigate = useNavigate();

  const [task, setTask] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('overview');

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

  const handleDownloadMarkdown = async () => {
    try {
      const res = await api.get(`/research/${taskId}/export/markdown`, { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${task?.ticker || 'stock'}_${task?.market || 'market'}_research_report.md`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Markdown download failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="py-20 text-center space-y-4">
        <div className="w-8 h-8 border-2 border-[#0A624C] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs font-mono text-slate-500">
          RETRIEVING DOSSIER & MULTI-AGENT TELEMETRY...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12 max-w-xl mx-auto text-center space-y-4 glass-panel rounded-3xl p-8">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
          <AlertTriangle className="w-7 h-7" />
        </div>
        <h2 className="font-display text-xl font-bold text-slate-900">Unable to Display Dossier</h2>
        <p className="text-sm text-slate-600">{error}</p>
        <Link
          to="/history"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#0A624C] hover:bg-[#084C3B] text-white rounded-xl text-xs font-mono font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          BACK TO ARCHIVE
        </Link>
      </div>
    );
  }

  const content = report?.report_content || {};
  const meta = content.meta || {};
  const metrics = content.market_metrics || {};
  const pipeline = content.multi_agent_pipeline || {};
  const fundamental = content.fundamental_analysis || null;
  const technical = content.technical_analysis || null;
  const dataQuality = content.data_quality || null;
  const sources = content.sources || [];

  const isPositiveChange = (metrics.period_change_pct || 0) >= 0;

  return (
    <div className="space-y-6 pb-16 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button
          onClick={() => navigate('/history')}
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono font-semibold text-slate-600 hover:text-slate-900 bg-white border border-[#E4E1D8] hover:bg-[#FAF9F5] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          ARCHIVE
        </button>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadMarkdown}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-bold text-white bg-[#0A624C] hover:bg-[#084C3B] transition-all"
          >
            <Download className="w-3.5 h-3.5" />
            EXPORT .MD
          </button>
          <span className="font-mono text-xs font-bold px-2.5 py-1.5 rounded-lg bg-white border border-[#E4E1D8] text-slate-700">
            TASK-{task?.task_id}
          </span>
        </div>
      </div>

      {/* Header Banner */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl relative overflow-hidden">
        <div className="absolute -right-24 -top-24 w-64 h-64 rounded-full bg-emerald-100/60 blur-3xl pointer-events-none" />
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                {task?.market}
              </span>
              <span className="text-slate-400 text-xs">•</span>
              <span className="text-slate-600 text-xs font-mono">HORIZON: {task?.analysis_period}</span>
              {meta.pipeline_version && (
                <>
                  <span className="text-slate-400 text-xs">•</span>
                  <span className="text-xs font-mono text-[#1E3A5F] font-semibold">{meta.pipeline_version}</span>
                </>
              )}
            </div>
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-slate-900 flex items-baseline gap-3">
              <span>{task?.company_name}</span>
              <span className="text-xl text-[#0A624C] font-mono font-bold">({task?.ticker})</span>
            </h1>
            <p className="mt-1.5 text-xs font-mono text-slate-500 flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5" />
              {meta.generated_at
                ? new Date(meta.generated_at).toLocaleString()
                : new Date(task?.created_at).toLocaleString()}
            </p>
          </div>

          <div className="bg-[#FAF9F5] p-4 rounded-2xl border border-[#E4E1D8] text-right min-w-[210px]">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
              Current Market Price
            </span>
            <div className="font-mono text-2xl font-black text-slate-900 mt-0.5">
              {metrics.currency === 'INR' ? '₹' : '$'}
              {metrics.current_price !== undefined && metrics.current_price !== null ? metrics.current_price : 'N/A'}
            </div>
            {metrics.period_change_pct !== undefined && metrics.period_change_pct !== null && (
              <div
                className={`inline-flex items-center gap-1 text-xs font-mono font-bold mt-1 px-2.5 py-0.5 rounded-full ${
                  isPositiveChange
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}
              >
                {isPositiveChange ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                <span>
                  {isPositiveChange ? '+' : ''}
                  {metrics.period_change_pct}% ({task?.analysis_period})
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {[
          { id: 'overview', label: 'Executive Summary & Agents', icon: FileText },
          { id: 'fundamental', label: 'Fundamental Analysis', icon: PieChart },
          { id: 'technical', label: 'Technical Charts & Indicators', icon: Activity },
          { id: 'provenance', label: 'Data Validation & Sources', icon: Database },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveSection(tab.id)}
              className={`px-4 py-2.5 rounded-xl text-xs font-mono font-bold flex items-center gap-2 border transition-all ${
                activeSection === tab.id
                  ? 'bg-[#0A624C] text-white border-[#0A624C] shadow-sm'
                  : 'bg-white text-slate-600 border-[#E4E1D8] hover:text-slate-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeSection === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="glass-card p-5 rounded-2xl">
              <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">P/E Ratio</span>
              <div className="font-mono text-xl font-extrabold text-slate-900">
                {metrics.pe_ratio && metrics.pe_ratio !== 'N/A'
                  ? typeof metrics.pe_ratio === 'number'
                    ? metrics.pe_ratio.toFixed(2)
                    : metrics.pe_ratio
                  : 'N/A'}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">Valuation multiple</p>
            </div>

            <div className="glass-card p-5 rounded-2xl">
              <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">Market Cap</span>
              <div className="font-mono text-xl font-extrabold text-slate-900">
                {metrics.market_cap && typeof metrics.market_cap === 'number'
                  ? metrics.currency === 'INR'
                    ? `₹${(metrics.market_cap / 1e7).toFixed(1)} Cr`
                    : `$${(metrics.market_cap / 1e9).toFixed(2)}B`
                  : 'N/A'}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">Total equity value</p>
            </div>

            <div className="glass-card p-5 rounded-2xl">
              <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">52-Week Range</span>
              <div className="font-mono text-sm font-bold text-slate-900">
                {metrics.fifty_two_week_low ? `${metrics.currency === 'INR' ? '₹' : '$'}${metrics.fifty_two_week_low}` : 'N/A'} –{' '}
                {metrics.fifty_two_week_high ? `${metrics.currency === 'INR' ? '₹' : '$'}${metrics.fifty_two_week_high}` : 'N/A'}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">Annual price bounds</p>
            </div>

            <div className="glass-card p-5 rounded-2xl">
              <span className="text-[10px] font-mono text-slate-500 uppercase block mb-1">Sector / Industry</span>
              <div className="text-sm font-bold text-slate-900 truncate" title={metrics.sector}>
                {metrics.sector || 'General Equity'}
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5 truncate">{metrics.industry || 'Capital Markets'}</p>
            </div>
          </div>

          {(content.executive_summary || report?.summary) && (
            <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-3">
              <div className="flex items-center gap-2.5 pb-2 border-b border-[#E4E1D8]">
                <FileText className="w-5 h-5 text-[#0A624C]" />
                <h2 className="font-display text-base font-bold text-slate-900">Executive Research Summary</h2>
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">
                {content.executive_summary || report?.summary}
              </p>
            </div>
          )}

          <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-3">
            <div className="flex items-center gap-2.5 pb-2 border-b border-[#E4E1D8]">
              <Building2 className="w-5 h-5 text-[#1E3A5F]" />
              <h2 className="font-display text-base font-bold text-slate-900">Company Profile & Operations</h2>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed pt-1">
              {content.company_overview || 'No extended business summary provided by market feed.'}
            </p>
          </div>

          <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[#E4E1D8]">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-50 text-[#0A624C] border border-emerald-200">
                  <Cpu className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="font-display text-base font-bold text-slate-900">Multi-Agent Pipeline Execution</h2>
                  <p className="text-xs text-slate-500">
                    Specialized agents executed and persisted to PostgreSQL
                  </p>
                </div>
              </div>
              <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                PIPELINE VERIFIED
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pipeline.active_agents?.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="p-4 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-[#1E3A5F] flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-[#0A624C]" />
                      {agent.agent_id}
                    </span>
                    <div className="flex items-center gap-2">
                      {agent.execution_time_ms !== undefined && (
                        <span className="text-[10px] font-mono text-slate-500">{agent.execution_time_ms}ms</span>
                      )}
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                          agent.status === 'COMPLETED'
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}
                      >
                        {agent.status}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs font-bold text-slate-900">{agent.role}</p>
                  <p className="text-[11px] text-slate-600 leading-relaxed">{agent.summary}</p>
                </div>
              ))}
            </div>

            <div className="p-4 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] text-xs text-slate-700 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-[#0A624C] flex-shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                This dossier combines validated market data collection, quantitative fundamental analysis, and technical indicator evaluations stored with full provenance in PostgreSQL.
              </p>
            </div>
          </div>
        </div>
      )}

      {activeSection === 'fundamental' && (
        fundamental ? (
          <FundamentalPanel fundamental={fundamental} />
        ) : (
          <div className="p-8 glass-panel rounded-3xl text-center text-sm text-slate-500">
            Fundamental analysis data was not recorded for this legacy task. Re-run research to generate full fundamental metrics.
          </div>
        )
      )}

      {activeSection === 'technical' && (
        technical ? (
          <TechnicalPanel technical={technical} />
        ) : (
          <div className="p-8 glass-panel rounded-3xl text-center text-sm text-slate-500">
            Technical analysis data was not recorded for this legacy task. Re-run research to generate interactive technical charts.
          </div>
        )
      )}

      {activeSection === 'provenance' && (
        <DataQualityPanel dataQuality={dataQuality} sources={sources} />
      )}
    </div>
  );
}
