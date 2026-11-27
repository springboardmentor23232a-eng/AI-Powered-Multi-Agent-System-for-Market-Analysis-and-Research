import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import Plotly from 'plotly.js-dist-min';
import {
  Zap,
  RefreshCw,
  ArrowUpRight,
  Compass,
  Bookmark,
  Database,
  PieChart,
  Activity,
  FileCheck2,
  Search,
  Play,
  Layers,
  Clock,
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/common/StatusBadge';

function MarketMixChart({ recentResearch = [], watchlistPreview = [] }) {
  const chartRef = useRef(null);

  useEffect(() => {
    const el = chartRef.current;
    if (!el) return;

    const counts = { NASDAQ: 0, NYSE: 0, NSE: 0, BSE: 0 };
    [...recentResearch, ...watchlistPreview].forEach((item) => {
      const m = (item.market || '').toUpperCase();
      if (m in counts) counts[m] += 1;
    });

    const labels = Object.keys(counts);
    const values = Object.values(counts);
    const total = values.reduce((a, b) => a + b, 0);

    const plotData =
      total > 0
        ? [
            {
              type: 'pie',
              hole: 0.64,
              labels,
              values,
              textinfo: 'label+percent',
              textfont: { family: 'JetBrains Mono, monospace', size: 11, color: '#1e293b' },
              marker: {
                colors: ['#0A624C', '#1E3A5F', '#D97706', '#0284C7'],
                line: { color: '#FFFFFF', width: 2 },
              },
              hovertemplate: '%{label}: %{value} items (%{percent})<extra></extra>',
            },
          ]
        : [
            {
              type: 'pie',
              hole: 0.64,
              labels: ['NASDAQ', 'NSE', 'NYSE', 'BSE'],
              values: [1, 1, 1, 1],
              textinfo: 'label',
              textfont: { family: 'JetBrains Mono, monospace', size: 10, color: '#64748b' },
              marker: {
                colors: ['#EFECE4', '#E4E1D8', '#EFECE4', '#E4E1D8'],
                line: { color: '#FFFFFF', width: 2 },
              },
              hoverinfo: 'label',
            },
          ];

    Plotly.react(
      el,
      plotData,
      {
        height: 215,
        margin: { t: 10, b: 10, l: 10, r: 10 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        showlegend: false,
        annotations: [
          {
            text: total > 0 ? `<b>${total}</b><br><span style="font-size:10px;color:#64748b">COVERAGE</span>` : '<b>READY</b>',
            showarrow: false,
            font: { family: 'JetBrains Mono, monospace', size: 15, color: '#0f172a' },
          },
        ],
      },
      { displayModeBar: false, responsive: true }
    );

    return () => {
      if (el) Plotly.purge(el);
    };
  }, [recentResearch, watchlistPreview]);

  return <div ref={chartRef} className="w-full" />;
}

export default function DashboardOverviewPage() {
  const { user, preferences } = useAuth();
  const { openResearchModal } = useOutletContext();
  const navigate = useNavigate();

  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [quickTicker, setQuickTicker] = useState('');

  const fetchOverview = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    try {
      const res = await api.get('/research/dashboard/overview');
      setOverview(res.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard overview:', err);
      setError('Could not connect to PostgreSQL backend to fetch dashboard telemetry.');
    } finally {
      setLoading(false);
      if (isManualRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  const handleQuickExplore = (e) => {
    e.preventDefault();
    if (!quickTicker.trim()) return;
    const mkt = preferences?.preferred_market || 'NASDAQ';
    navigate(`/explorer?ticker=${encodeURIComponent(quickTicker.trim().toUpperCase())}&market=${encodeURIComponent(mkt)}`);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 h-64 rounded-3xl bg-[#EDEAE0]" />
          <div className="lg:col-span-4 h-64 rounded-3xl bg-[#EDEAE0]" />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 rounded-2xl bg-[#EDEAE0]" />
          ))}
        </div>
      </div>
    );
  }

  const total = overview?.total_research || 0;
  const completed = overview?.completed_research || 0;
  const pending = overview?.pending_research || 0;
  const failed = overview?.failed_research || 0;
  const savedCount = overview?.total_saved_stocks || 0;
  const completionPct = total > 0 ? Math.round((completed / total) * 100) : 100;

  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (completionPct / 100) * circumference;

  const pipelineNodes = [
    { step: '01', name: 'OHLCV Collector', desc: 'Validation & Provenance', icon: Database, color: 'text-emerald-700 border-emerald-200 bg-emerald-50' },
    { step: '02', name: 'Fundamental Agent', desc: 'P/E, P/B, ROE & Peers', icon: PieChart, color: 'text-sky-700 border-sky-200 bg-sky-50' },
    { step: '03', name: 'Technical Agent', desc: 'SMA, EMA, RSI, MACD', icon: Activity, color: 'text-amber-700 border-amber-200 bg-amber-50' },
    { step: '04', name: 'Dossier Compiler', desc: 'PostgreSQL + Markdown', icon: FileCheck2, color: 'text-indigo-700 border-indigo-200 bg-indigo-50' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => fetchOverview(true)} className="underline font-bold hover:text-rose-950">
            RETRY
          </button>
        </div>
      )}

      {/* HERO BENTO DECK */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Executive Studio Console */}
        <div className="lg:col-span-8 glass-panel rounded-3xl p-6 sm:p-7 relative overflow-hidden flex flex-col justify-between gap-6">
          <div className="absolute -right-24 -top-24 w-72 h-72 rounded-full bg-emerald-100/60 blur-3xl pointer-events-none" />

          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 relative z-10">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-[#0A624C] text-[11px] font-mono font-bold mb-3">
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                QUANTITATIVE RESEARCH DESK
              </div>
              <h1 className="font-display text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
                Good evening, <span className="text-[#0A624C]">{user?.full_name || 'Analyst'}</span>
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 max-w-xl">
                Orchestrate validated market data collection, fundamental ratio synthesis, and interactive technical charting.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchOverview(true)}
                className="p-2.5 rounded-xl bg-[#F6F5F0] hover:bg-[#EDEAE0] border border-[#E4E1D8] text-slate-600 hover:text-[#0A624C] transition-colors"
                title="Refresh Telemetry"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={() => openResearchModal(null)}
                className="px-4 py-2.5 rounded-xl bg-[#0A624C] hover:bg-[#084C3B] text-white font-bold text-xs shadow-sm shadow-emerald-900/15 flex items-center gap-1.5 transition-all"
              >
                <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
                Run Full Pipeline
              </button>
            </div>
          </div>

          {/* Instant Ticker Jump Bar */}
          <form onSubmit={handleQuickExplore} className="relative z-10 flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                value={quickTicker}
                onChange={(e) => setQuickTicker(e.target.value)}
                placeholder={`Quick launch ticker on ${preferences?.preferred_market || 'NASDAQ'} (AAPL, NVDA, INFY, RELIANCE)...`}
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-[#FAF9F5] border border-[#DCD8CD] text-xs font-mono text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-[#0A624C] focus:ring-2 focus:ring-emerald-600/15"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2.5 rounded-xl bg-[#1E3A5F] hover:bg-[#162C49] text-white text-xs font-mono font-semibold flex items-center justify-center gap-1.5 transition-colors shadow-sm"
            >
              <Compass className="w-3.5 h-3.5" />
              INSPECT CHARTS
            </button>
          </form>

          {/* Multi-Agent Constellation Nodes */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 relative z-10">
            {pipelineNodes.map((node) => {
              const Icon = node.icon;
              return (
                <div
                  key={node.step}
                  className="p-3 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] flex flex-col gap-2"
                >
                  <div className="flex items-center justify-between">
                    <div className={`p-1.5 rounded-lg border ${node.color}`}>
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-[10px] font-mono text-slate-400">NODE {node.step}</span>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-900">{node.name}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{node.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Radial Pipeline Reliability Gauge */}
        <div className="lg:col-span-4 glass-panel rounded-3xl p-6 flex flex-col justify-between gap-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-slate-400">
                Pipeline Reliability
              </span>
              <h2 className="font-display text-base font-bold text-slate-900">Execution Telemetry</h2>
            </div>
            <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-[#0A624C] border border-emerald-200">
              LIVE DB
            </span>
          </div>

          <div className="flex items-center gap-5 py-2">
            <div className="relative w-28 h-28 flex-shrink-0">
              <svg className="w-28 h-28 -rotate-90" viewBox="0 0 110 110">
                <circle
                  cx="55"
                  cy="55"
                  r={radius}
                  stroke="#EDEAE0"
                  strokeWidth="10"
                  fill="transparent"
                />
                <circle
                  cx="55"
                  cy="55"
                  r={radius}
                  stroke="#0A624C"
                  strokeWidth="10"
                  strokeLinecap="round"
                  fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="font-mono text-xl font-bold text-slate-900">{completionPct}%</span>
                <span className="text-[9px] font-mono text-slate-500 uppercase">Success</span>
              </div>
            </div>

            <div className="flex-1 space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Total Runs</span>
                <span className="font-bold text-slate-900">{total}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-emerald-700">Completed</span>
                <span className="font-bold text-emerald-700">{completed}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-amber-700">In-Flight</span>
                <span className="font-bold text-amber-700">{pending}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-rose-700">Failed</span>
                <span className="font-bold text-rose-700">{failed}</span>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-[#E4E1D8] grid grid-cols-2 gap-2 text-center">
            <Link
              to="/watchlist"
              className="p-2.5 rounded-xl bg-[#FAF9F5] hover:bg-[#EFECE4] border border-[#E4E1D8] transition-colors"
            >
              <span className="block font-mono text-lg font-bold text-[#1E3A5F]">{savedCount}</span>
              <span className="text-[10px] font-mono text-slate-500 uppercase">Watchlist Radar</span>
            </Link>
            <Link
              to="/preferences"
              className="p-2.5 rounded-xl bg-[#FAF9F5] hover:bg-[#EFECE4] border border-[#E4E1D8] transition-colors"
            >
              <span className="block font-mono text-sm font-bold text-amber-700 mt-0.5">
                {preferences?.preferred_market || 'NASDAQ'}
              </span>
              <span className="text-[10px] font-mono text-slate-500 uppercase block mt-1">
                {preferences?.analysis_period || '1 Year'}
              </span>
            </Link>
          </div>
        </div>
      </div>

      {/* MAIN ASYMMETRIC WORKSPACE */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Chronological Agent Dossier Timeline */}
        <div className="lg:col-span-7 glass-panel rounded-3xl p-6 flex flex-col">
          <div className="flex items-center justify-between pb-4 border-b border-[#E4E1D8]">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#0A624C] font-semibold">
                Execution Stream
              </span>
              <h2 className="font-display text-lg font-bold text-slate-900">Recent Research Dossiers</h2>
            </div>
            <Link
              to="/history"
              className="text-xs font-mono font-bold text-[#0A624C] hover:text-emerald-800 flex items-center gap-1"
            >
              FULL ARCHIVE <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 pt-5">
            {overview?.recent_research?.length === 0 ? (
              <div className="py-12 text-center space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-[#F6F5F0] border border-[#E4E1D8] text-slate-400 flex items-center justify-center mx-auto">
                  <Layers className="w-6 h-6" />
                </div>
                <p className="text-sm font-bold text-slate-900">No agent dossiers generated yet</p>
                <p className="text-xs text-slate-500 max-w-sm mx-auto">
                  Launch your first research pipeline to collect OHLCV data, compute fundamental multiples, and render technical charts.
                </p>
                <button
                  onClick={() => openResearchModal(null)}
                  className="px-4 py-2 rounded-xl bg-[#0A624C] hover:bg-[#084C3B] text-white text-xs font-bold transition-colors"
                >
                  Launch First Run
                </button>
              </div>
            ) : (
              <div className="relative pl-6 space-y-4 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-[#E4E1D8]">
                {overview?.recent_research?.map((task) => {
                  const dotColor =
                    task.status === 'Completed'
                      ? 'bg-emerald-600 ring-emerald-100'
                      : task.status === 'Failed'
                      ? 'bg-rose-600 ring-rose-100'
                      : 'bg-amber-500 ring-amber-100';
                  return (
                    <div
                      key={task.task_id}
                      className="relative p-4 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] hover:border-emerald-600/35 hover:bg-white transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <span className={`absolute -left-[22px] top-6 w-3 h-3 rounded-full ring-4 ${dotColor}`} />
                      <div className="min-w-0 space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-sm font-bold text-slate-900">{task.ticker}</span>
                          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-white text-[#1E3A5F] border border-[#DCD8CD]">
                            {task.market}
                          </span>
                          <span className="text-[10px] font-mono text-slate-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.analysis_period}
                          </span>
                          <StatusBadge status={task.status} />
                        </div>
                        <p className="text-xs text-slate-600 truncate">{task.company_name}</p>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <button
                          type="button"
                          onClick={() => navigate(`/explorer?ticker=${task.ticker}&market=${task.market}`)}
                          className="px-3 py-1.5 rounded-xl text-[11px] font-mono font-semibold bg-white hover:bg-[#EFECE4] text-slate-700 border border-[#DCD8CD] transition-colors"
                        >
                          CHARTS
                        </button>
                        {task.status === 'Completed' && (
                          <Link
                            to={`/history/${task.task_id}/report`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-[11px] font-mono font-bold bg-[#0A624C] hover:bg-[#084C3B] text-white transition-all"
                          >
                            DOSSIER <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: Exchange Coverage Donut + Watchlist Radar */}
        <div className="lg:col-span-5 space-y-5">
          <div className="glass-panel rounded-3xl p-6">
            <div className="flex items-center justify-between mb-1">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-[#1E3A5F] font-semibold">
                  Exchange Allocation
                </span>
                <h3 className="font-display text-base font-bold text-slate-900">Market Coverage Mix</h3>
              </div>
              <span className="text-[10px] font-mono text-slate-400">NSE • BSE • US</span>
            </div>
            <MarketMixChart
              recentResearch={overview?.recent_research || []}
              watchlistPreview={overview?.watchlist_preview || []}
            />
          </div>

          <div className="glass-panel rounded-3xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[#E4E1D8]">
              <div>
                <span className="text-[10px] font-mono uppercase tracking-widest text-amber-700 font-semibold">
                  Tracked Equities
                </span>
                <h3 className="font-display text-base font-bold text-slate-900">Watchlist Radar</h3>
              </div>
              <Link
                to="/watchlist"
                className="text-xs font-mono font-bold text-[#0A624C] hover:text-emerald-800 flex items-center gap-1"
              >
                MANAGE <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {overview?.watchlist_preview?.length === 0 ? (
              <div className="py-6 text-center space-y-3">
                <Bookmark className="w-7 h-7 text-slate-400 mx-auto" />
                <p className="text-xs text-slate-500">No securities pinned to your radar yet.</p>
                <Link
                  to="/watchlist"
                  className="inline-block px-4 py-2 rounded-xl bg-[#FAF9F5] hover:bg-[#EFECE4] text-xs font-mono font-semibold text-[#0A624C] border border-[#DCD8CD]"
                >
                  + ADD SECURITIES
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-2.5">
                {overview?.watchlist_preview?.map((stock) => (
                  <div
                    key={stock.saved_stock_id}
                    className="p-3.5 rounded-2xl glass-card flex items-center justify-between gap-2"
                  >
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-bold text-slate-900">{stock.ticker}</span>
                        <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                          {stock.market}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 truncate mt-0.5">{stock.company_name}</p>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <button
                        type="button"
                        onClick={() => navigate(`/explorer?ticker=${stock.ticker}&market=${stock.market}`)}
                        className="px-2.5 py-1.5 rounded-lg text-[10px] font-mono font-semibold bg-[#FAF9F5] hover:bg-[#EFECE4] text-[#1E3A5F] border border-[#DCD8CD]"
                      >
                        CHARTS
                      </button>
                      <button
                        type="button"
                        onClick={() => openResearchModal(stock)}
                        className="p-1.5 rounded-lg bg-emerald-50 hover:bg-[#0A624C] text-[#0A624C] hover:text-white border border-emerald-200 transition-colors"
                        title="Launch Research Pipeline"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
