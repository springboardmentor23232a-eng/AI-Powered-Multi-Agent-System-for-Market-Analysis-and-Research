import React, { useState, useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import {
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  Bookmark,
  Plus,
  History,
  Sliders,
  ExternalLink,
  ArrowUpRight,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/common/StatusBadge';

export default function DashboardOverviewPage() {
  const { user } = useAuth();
  const { openResearchModal } = useOutletContext();

  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchOverview = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    try {
      const res = await api.get('/research/dashboard/overview');
      setOverview(res.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard overview:', err);
      setError('Could not connect to PostgreSQL backend to fetch dashboard analytics.');
    } finally {
      setLoading(false);
      if (isManualRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-24 bg-slate-200/60 rounded-3xl" />
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-200/60 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-72 bg-slate-200/60 rounded-3xl" />
          <div className="h-72 bg-slate-200/60 rounded-3xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 p-6 sm:p-8 text-white shadow-xl shadow-slate-950/20 border border-slate-800">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-300 text-xs font-semibold mb-3">
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-ping" />
              QuantAgent Active Workspace
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Welcome back, {user?.full_name || 'Stock Analyst'}
            </h1>
            <p className="mt-1.5 text-sm text-slate-300 max-w-xl leading-relaxed">
              Real-time multi-agent quantitative analytics and autonomous company intelligence.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => fetchOverview(true)}
              className="p-3 bg-white/10 hover:bg-white/20 active:bg-white/30 text-white rounded-xl transition-colors border border-white/10"
              title="Refresh Dashboard Data"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={() => openResearchModal(null)}
              className="px-5 py-3 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-xl font-semibold text-sm shadow-lg shadow-blue-600/30 transition-all flex items-center gap-2 hover:scale-[1.02]"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              Start New Research
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => fetchOverview(true)} className="underline hover:text-rose-900 font-bold">
            Retry
          </button>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Tasks */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Tasks</span>
            <div className="p-2 rounded-xl bg-slate-100 text-slate-700">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-slate-900">{overview?.total_research || 0}</div>
          <p className="text-[11px] text-slate-600 mt-1">Research executions</p>
        </div>

        {/* Completed */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Completed</span>
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-emerald-600">
            {overview?.completed_research || 0}
          </div>
          <p className="text-[11px] text-slate-600 mt-1">Ready for inspection</p>
        </div>

        {/* Pending / In-flight */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Pending</span>
            <div className="p-2 rounded-xl bg-amber-50 text-amber-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-amber-600">
            {overview?.pending_research || 0}
          </div>
          <p className="text-[11px] text-slate-600 mt-1">Agent pipeline working</p>
        </div>

        {/* Failed */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Failed</span>
            <div className="p-2 rounded-xl bg-rose-50 text-rose-600">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-rose-600">{overview?.failed_research || 0}</div>
          <p className="text-[11px] text-slate-600 mt-1">Validation/network errors</p>
        </div>

        {/* Saved Stocks */}
        <div className="col-span-2 lg:col-span-1 bg-white p-5 rounded-2xl border border-slate-200/80 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Watchlist</span>
            <div className="p-2 rounded-xl bg-blue-50 text-blue-600">
              <Bookmark className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-extrabold text-blue-600">
            {overview?.total_saved_stocks || 0}
          </div>
          <p className="text-[11px] text-slate-600 mt-1">Monitored securities</p>
        </div>
      </div>

      {/* Quick Actions Bar */}
      <div>
        <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-3">Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <button
            onClick={() => openResearchModal(null)}
            className="p-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:border-blue-500/50 hover:shadow-md transition-all text-left group"
          >
            <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Plus className="w-4 h-4 stroke-[2.5]" />
            </div>
            <p className="text-sm font-bold text-slate-900">Start New Research</p>
            <p className="text-xs text-slate-500 mt-0.5">Execute analysis task</p>
          </button>

          <Link
            to="/history"
            className="p-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:border-blue-500/50 hover:shadow-md transition-all text-left group block"
          >
            <div className="w-8 h-8 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <History className="w-4 h-4" />
            </div>
            <p className="text-sm font-bold text-slate-900">Research History</p>
            <p className="text-xs text-slate-500 mt-0.5">Inspect dossiers & reports</p>
          </Link>

          <Link
            to="/watchlist"
            className="p-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:border-blue-500/50 hover:shadow-md transition-all text-left group block"
          >
            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Bookmark className="w-4 h-4" />
            </div>
            <p className="text-sm font-bold text-slate-900">Manage Watchlist</p>
            <p className="text-xs text-slate-500 mt-0.5">Add & track companies</p>
          </Link>

          <Link
            to="/preferences"
            className="p-4 bg-white rounded-2xl border border-slate-200/80 shadow-sm hover:border-blue-500/50 hover:shadow-md transition-all text-left group block"
          >
            <div className="w-8 h-8 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
              <Sliders className="w-4 h-4" />
            </div>
            <p className="text-sm font-bold text-slate-900">Preferences</p>
            <p className="text-xs text-slate-500 mt-0.5">Market & horizon defaults</p>
          </Link>
        </div>
      </div>

      {/* Main Grid: Recent Activities & Watchlist Preview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Activities Table */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Recent Research Activities</h2>
              <p className="text-xs text-slate-500 mt-0.5">Live status from multi-agent pipeline</p>
            </div>
            <Link
              to="/history"
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              View All <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 overflow-x-auto">
            {overview?.recent_research?.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <FileText className="w-6 h-6" />
                </div>
                <p className="text-sm font-bold text-slate-700">No research activities found</p>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                  You haven't initiated any stock analysis tasks yet. Launch your first research task to view agent analysis here.
                </p>
                <button
                  onClick={() => openResearchModal(null)}
                  className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-colors"
                >
                  Start Research
                </button>
              </div>
            ) : (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 bg-slate-50/50">
                    <th className="py-3 px-6">Company / Ticker</th>
                    <th className="py-3 px-4">Market</th>
                    <th className="py-3 px-4">Period</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-6 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {overview?.recent_research?.map((task) => (
                    <tr key={task.task_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-4 px-6">
                        <div className="font-bold text-slate-900">{task.ticker}</div>
                        <div className="text-xs text-slate-500 truncate max-w-[200px]">
                          {task.company_name}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700">
                          {task.market}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-xs text-slate-600">{task.analysis_period}</td>
                      <td className="py-4 px-4">
                        <StatusBadge status={task.status} />
                      </td>
                      <td className="py-4 px-6 text-right">
                        {task.status === 'Completed' ? (
                          <Link
                            to={`/history/${task.task_id}/report`}
                            className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-600 hover:text-white transition-all"
                          >
                            <span>Report</span>
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        ) : (
                          <span className="text-xs text-slate-400">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Watchlist Preview */}
        <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Watchlist Preview</h2>
              <p className="text-xs text-slate-500 mt-0.5">Quick access to monitored stocks</p>
            </div>
            <Link
              to="/watchlist"
              className="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              Manage <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="p-6 flex-1 flex flex-col justify-between">
            {overview?.watchlist_preview?.length === 0 ? (
              <div className="py-8 text-center">
                <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
                  <Bookmark className="w-6 h-6" />
                </div>
                <p className="text-sm font-bold text-slate-700">Your watchlist is empty</p>
                <p className="text-xs text-slate-500 max-w-xs mx-auto mt-1">
                  Save US and Indian equities to your watchlist to launch one-click research tasks.
                </p>
                <Link
                  to="/watchlist"
                  className="mt-4 inline-block px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold transition-colors"
                >
                  Explore Stocks
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {overview?.watchlist_preview?.map((stock) => (
                  <div
                    key={stock.saved_stock_id}
                    className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 flex items-center justify-between hover:bg-blue-50/40 hover:border-blue-200 transition-all"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-extrabold text-slate-900 text-sm">{stock.ticker}</span>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white text-slate-600 border border-slate-200">
                          {stock.market}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 truncate mt-0.5 font-medium">
                        {stock.company_name}
                      </p>
                    </div>

                    <button
                      onClick={() => openResearchModal(stock)}
                      className="ml-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-blue-600 text-slate-700 hover:text-white border border-slate-200 hover:border-transparent transition-all shadow-sm"
                    >
                      Research
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6 pt-4 border-t border-slate-100 text-center">
              <Link
                to="/watchlist"
                className="text-xs font-semibold text-slate-600 hover:text-blue-600 transition-colors"
              >
                + Search & Save More Companies
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

