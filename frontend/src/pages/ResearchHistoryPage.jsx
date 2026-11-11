import React, { useState, useEffect } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import {
  Search,
  Filter,
  ArrowUpDown,
  History,
  ExternalLink,
  Plus,
  RefreshCw,
  AlertCircle,
  FileQuestion,
  Calendar,
} from 'lucide-react';
import api from '../api/client';
import StatusBadge from '../components/common/StatusBadge';

export default function ResearchHistoryPage() {
  const { openResearchModal } = useOutletContext();

  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Filters & Sorting
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');

  const fetchHistory = async (isSilent = false) => {
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
  };

  useEffect(() => {
    fetchHistory();
  }, [statusFilter, sortOrder]);

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchHistory();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Periodic polling if any tasks are in flight (Pending or Processing)
  useEffect(() => {
    const hasInFlight = tasks.some(
      (t) => t.status === 'Pending' || t.status === 'Processing'
    );
    if (!hasInFlight) return;

    const interval = setInterval(() => {
      fetchHistory(true);
    }, 2500);

    return () => clearInterval(interval);
  }, [tasks, statusFilter, sortOrder, searchQuery]);

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <History className="w-6 h-6 text-blue-600" />
            Research History
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse and open previous automated multi-agent stock analysis dossiers
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchHistory(false)}
            className="p-2.5 bg-white border border-slate-200 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-sm transition-colors"
            title="Refresh History"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => openResearchModal(null)}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold text-sm shadow-md shadow-blue-600/20 transition-all flex items-center gap-2"
          >
            <Plus className="w-4 h-4 stroke-[2.5]" />
            New Research
          </button>
        </div>
      </div>

      {/* Control Bar: Search & Filters */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ticker or company name..."
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all"
          />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all"
            >
              <option value="">All Statuses</option>
              <option value="Completed">Completed</option>
              <option value="Processing">Processing</option>
              <option value="Pending">Pending</option>
              <option value="Failed">Failed</option>
            </select>
          </div>

          {/* Sort Order */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-slate-400" />
            <select
              value={sortOrder}
              onChange={(e) => setSortOrder(e.target.value)}
              className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all"
            >
              <option value="desc">Newest First</option>
              <option value="asc">Oldest First</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium">
          {error}
        </div>
      )}

      {/* History Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-slate-500 font-medium">Loading research history records...</p>
          </div>
        ) : tasks.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-4">
              <FileQuestion className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-800">No research records found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 leading-relaxed">
              {searchQuery || statusFilter
                ? 'No research tasks match your active filter criteria. Try clearing search or filters.'
                : 'You have not executed any stock research tasks yet. Initiate your first research using the button below.'}
            </p>
            {searchQuery || statusFilter ? (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('');
                }}
                className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
              >
                Clear Filters
              </button>
            ) : (
              <button
                onClick={() => openResearchModal(null)}
                className="mt-4 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-colors inline-flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" /> Start First Research
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 bg-slate-50/70">
                  <th className="py-3.5 px-6">Company / Ticker</th>
                  <th className="py-3.5 px-4">Market</th>
                  <th className="py-3.5 px-4">Analysis Period</th>
                  <th className="py-3.5 px-4">Research Date</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-6 text-right">Report</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {tasks.map((task) => (
                  <tr key={task.task_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-extrabold text-slate-900 flex items-center gap-2">
                        <span>{task.ticker}</span>
                      </div>
                      <div className="text-xs text-slate-500 truncate max-w-[240px]">
                        {task.company_name}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                        {task.market}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs text-slate-600">
                      {task.analysis_period}
                    </td>
                    <td className="py-4 px-4 text-xs text-slate-500 whitespace-nowrap">
                      {new Date(task.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex flex-col items-start gap-1">
                        <StatusBadge status={task.status} />
                        {task.status === 'Failed' && task.error_message && (
                          <span
                            className="text-[11px] text-rose-600 max-w-[200px] truncate"
                            title={task.error_message}
                          >
                            {task.error_message}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6 text-right whitespace-nowrap">
                      {task.status === 'Completed' ? (
                        <Link
                          to={`/history/${task.task_id}/report`}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-sm shadow-blue-600/20 transition-all hover:scale-[1.02]"
                        >
                          <span>Open Report</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      ) : task.status === 'Processing' || task.status === 'Pending' ? (
                        <span className="text-xs font-semibold text-slate-400 italic">
                          Generating...
                        </span>
                      ) : (
                        <span className="text-xs font-medium text-rose-500">
                          Unavailable
                        </span>
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

