import React, { useState, useEffect, useCallback } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowUpDown,
  History,
  ExternalLink,
  Plus,
  RefreshCw,
  FileQuestion,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/common/StatusBadge';

export default function ResearchHistoryPage() {
  const { openResearchModal } = useOutletContext();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchHistory = useCallback(async (isSilent = false) => {
    if (!isSilent) setRefreshing(true);
    try {
      let url = `/research/history?sort=${sortOrder}`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;
      if (searchQuery.trim()) url += `&search=${encodeURIComponent(searchQuery.trim())}`;

      const res = await api.get(url);
      setTasks(res.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch research history:', err);
      setError('Could not retrieve research tasks from the server.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [sortOrder, statusFilter, searchQuery]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchHistory();
    }, 220);
    return () => clearTimeout(timer);
  }, [fetchHistory]);

  useEffect(() => {
    const hasInFlight = tasks.some(
      (t) => t.status === 'Pending' || t.status === 'Processing'
    );
    if (!hasInFlight) return;

    const interval = setInterval(() => {
      fetchHistory(true);
    }, 2500);

    return () => clearInterval(interval);
  }, [tasks, fetchHistory]);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-[#1E3A5F] font-semibold">
            PostgreSQL Dossier Store
          </span>
          <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <History className="w-6 h-6 text-[#0A624C]" />
            Research Dossier Archive
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Inspect persisted multi-agent stock analysis dossiers and Markdown exports
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchHistory(false)}
            className="p-2.5 bg-white border border-[#E4E1D8] rounded-xl text-slate-600 hover:text-[#0A624C] transition-colors"
            title="Refresh Archive"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => openResearchModal(null)}
            className="px-4 py-2.5 bg-[#0A624C] hover:bg-[#084C3B] text-white rounded-xl font-bold text-xs shadow-sm flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            New Dossier
          </button>
        </div>
      </div>

      <div className="glass-panel p-4 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter by ticker or company name..."
            className="w-full pl-10 pr-4 py-2 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-[#0A624C]"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-xs font-mono font-semibold text-slate-700 focus:outline-none"
            >
              <option value="">All Statuses</option>
              <option value="Completed">Completed</option>
              <option value="Processing">Processing</option>
              <option value="Pending">Pending</option>
              <option value="Failed">Failed</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-slate-400" />
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-3 py-2 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-xs font-mono font-semibold text-slate-700 focus:outline-none"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono">
          {error}
        </div>
      )}

      <div className="glass-panel rounded-3xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-6 h-6 border-2 border-[#0A624C] border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs font-mono text-slate-500">LOADING ARCHIVE...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] text-slate-400 flex items-center justify-center mx-auto mb-4">
              <FileQuestion className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-900">No research dossiers found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              {searchQuery || statusFilter
                ? 'No research tasks match your filter criteria.'
                : 'You have not executed any stock research tasks yet.'}
            </p>
            <button
              onClick={() => openResearchModal(null)}
              className="mt-4 px-4 py-2.5 bg-[#0A624C] hover:bg-[#084C3B] text-white rounded-xl text-xs font-bold inline-flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" /> Launch First Research
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-[#E4E1D8] text-[11px] font-mono uppercase text-slate-500 bg-[#FAF9F5]">
                  <th className="py-3.5 px-6">Security</th>
                  <th className="py-3.5 px-4">Exchange</th>
                  <th className="py-3.5 px-4">Horizon</th>
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-6 text-right">Dossier</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EDEAE0]">
                {tasks.map((task) => (
                  <tr key={task.task_id} className="hover:bg-[#FAF9F5] transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-mono font-bold text-slate-900">{task.ticker}</div>
                      <div className="text-xs text-slate-500 truncate max-w-[240px]">{task.company_name}</div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                        {task.market}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs font-mono text-slate-600">{task.analysis_period}</td>
                    <td className="py-4 px-4 text-xs font-mono text-slate-500 whitespace-nowrap">
                      {new Date(task.created_at).toLocaleString()}
                    </td>
                    <td className="py-4 px-4">
                      <StatusBadge status={task.status} />
                    </td>
                    <td className="py-4 px-6 text-right whitespace-nowrap">
                      {task.status === 'Completed' ? (
                        <Link
                          to={`/history/${task.task_id}/report`}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold text-white bg-[#0A624C] hover:bg-[#084C3B] transition-all"
                        >
                          <span>OPEN</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      ) : task.status === 'Processing' || task.status === 'Pending' ? (
                        <span className="text-xs font-mono text-slate-500 italic">Processing...</span>
                      ) : (
                        <span className="text-xs font-mono text-rose-600">Unavailable</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
