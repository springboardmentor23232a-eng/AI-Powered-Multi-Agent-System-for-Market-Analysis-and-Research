import React, { useState, useEffect } from 'react';
import {
  Layers,
  FileText,
  Clock,
  XCircle,
  Search,
  Calendar,
  ExternalLink,
  Download,
  Trash2,
  Loader2,
  X,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { api } from '../api/client';
import StockLogo from './StockLogo';
import ExportModal from './ExportModal';

export default function HistoryView({ onSelectReport, onNavigateToResearch }) {
  const [sessions, setSessions] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL'); // 'ALL', 'COMPLETED', 'IN_PROGRESS', 'FAILED'

  // Deletion modal state
  const [sessionToDelete, setSessionToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Export modal state
  const [exportSession, setExportSession] = useState(null);

  const fetchHistoryData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sessionsData, analyticsData] = await Promise.all([
        api.listSessions(100, 0),
        api.getWorkspaceAnalytics().catch(() => null),
      ]);
      setSessions(sessionsData.sessions || []);
      setAnalytics(analyticsData);
    } catch (err) {
      setError(err.message || 'Failed to load research history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistoryData();
  }, []);

  const handleDeleteSession = async () => {
    if (!sessionToDelete) return;
    setDeleting(true);
    try {
      await api.deleteSession(sessionToDelete.id);
      setSessions((prev) => prev.filter((s) => s.id !== sessionToDelete.id));
      setSessionToDelete(null);
    } catch (err) {
      alert(err.message || 'Failed to delete research session.');
    } finally {
      setDeleting(false);
    }
  };

  // Metrics counts
  const totalCount = analytics?.total_sessions ?? sessions.length;
  const completedCount =
    analytics?.status_counts?.completed ??
    sessions.filter((s) => s.status === 'COMPLETED').length;
  const inProgressCount =
    analytics?.status_counts
      ? (analytics.status_counts.in_progress || 0) + (analytics.status_counts.pending || 0)
      : sessions.filter((s) => s.status === 'IN_PROGRESS' || s.status === 'PENDING').length;
  const failedCount =
    analytics?.status_counts?.failed ??
    sessions.filter((s) => s.status === 'FAILED').length;

  // Filtered sessions
  const filteredSessions = sessions.filter((s) => {
    const q = searchQuery.toLowerCase().trim();
    const matchesSearch =
      !q ||
      s.ticker.toLowerCase().includes(q) ||
      (s.company_name && s.company_name.toLowerCase().includes(q));

    if (!matchesSearch) return false;
    if (statusFilter === 'ALL') return true;
    if (statusFilter === 'IN_PROGRESS') {
      return s.status === 'IN_PROGRESS' || s.status === 'PENDING';
    }
    return s.status === statusFilter;
  });

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      const day = d.getDate();
      const month = d.toLocaleString('en-US', { month: 'short' });
      const year = d.getFullYear();
      const time = d.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      });
      return `${day} ${month} ${year}, ${time}`;
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6 sm:space-y-7 animate-fadeIn">
      {/* 4 Dynamic KPI Cards matching Reference Screenshot 3 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
        {/* Total Sessions */}
        <div className="p-5 sm:p-6 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-500 block">Total Sessions</span>
              <div className="flex items-baseline gap-2.5 mt-0.5">
                <span className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
                  {totalCount}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Completed */}
        <div className="p-5 sm:p-6 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-500 block">Completed</span>
              <div className="flex items-baseline gap-2.5 mt-0.5">
                <span className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
                  {completedCount}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* In Progress */}
        <div className="p-5 sm:p-6 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-500 block">In Progress</span>
              <div className="flex items-baseline gap-2.5 mt-0.5">
                <span className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
                  {inProgressCount}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Failed */}
        <div className="p-5 sm:p-6 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0">
              <XCircle className="w-5 h-5" />
            </div>
            <div>
              <span className="text-xs font-bold text-gray-500 block">Failed</span>
              <div className="flex items-baseline gap-2.5 mt-0.5">
                <span className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
                  {failedCount}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Search Pill */}
        <div className="relative flex-1 max-w-lg">
          <input
            type="text"
            placeholder="Search by ticker or company name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-12 pl-11 pr-10 rounded-full bg-white border border-gray-200/80 text-sm font-semibold text-[#111318] placeholder-gray-400 focus:outline-none focus:border-[#17191F] shadow-[0_2px_12px_rgba(0,0,0,0.02)] transition"
          />
          <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Status Filter Segmented Capsule */}
        <div className="flex items-center gap-1 p-1 rounded-full bg-white border border-gray-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.02)] shrink-0 overflow-x-auto">
          {[
            { id: 'ALL', label: 'All Sessions' },
            { id: 'COMPLETED', label: 'Completed' },
            { id: 'IN_PROGRESS', label: 'In Progress' },
            { id: 'FAILED', label: 'Failed' },
          ].map((tab) => {
            const isActive = statusFilter === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-4 py-2 rounded-full text-xs font-black transition cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'bg-[#C5F500] text-[#111318] shadow-xs'
                    : 'text-gray-500 hover:text-[#111318]'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={fetchHistoryData}
            className="font-bold underline cursor-pointer flex items-center gap-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* Sessions Table Card */}
      <div className="rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 overflow-hidden">
        {loading ? (
          <div className="py-24 text-center space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-[#17191F] mx-auto" />
            <p className="text-xs text-gray-500 font-bold">Loading research sessions...</p>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className="py-20 text-center space-y-4">
            <div className="w-14 h-14 rounded-2xl bg-gray-100/80 border border-gray-200/60 text-gray-400 mx-auto flex items-center justify-center">
              <FileText className="w-7 h-7" />
            </div>
            <div>
              <h4 className="text-base font-black text-[#111318]">
                {searchQuery || statusFilter !== 'ALL'
                  ? 'No matching sessions found'
                  : 'No research sessions yet'}
              </h4>
              <p className="text-xs text-gray-500 max-w-sm mx-auto mt-1 leading-relaxed">
                {searchQuery || statusFilter !== 'ALL'
                  ? 'Try modifying your search query or switching the status filter tab.'
                  : 'Initiate your first autonomous multi-agent equity analysis to start building your library.'}
              </p>
            </div>
            {(!searchQuery && statusFilter === 'ALL') && (
              <button
                onClick={onNavigateToResearch}
                className="h-10 px-5 rounded-full bg-[#C5F500] hover:bg-[#b5e200] text-[#111318] text-xs font-black transition cursor-pointer shadow-xs inline-flex items-center gap-2"
              >
                <span>New Stock Analysis</span>
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto -mx-6 sm:-mx-7 px-6 sm:px-7">
            <table className="w-full text-left text-sm border-collapse min-w-[700px]">
              <thead>
                <tr className="border-b border-gray-100 text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  <th className="pb-3.5 px-3">Ticker</th>
                  <th className="pb-3.5 px-3">Company</th>
                  <th className="pb-3.5 px-3">Status</th>
                  <th className="pb-3.5 px-3">Date</th>
                  <th className="pb-3.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filteredSessions.map((s) => {
                  const isCompleted = s.status === 'COMPLETED';
                  const isFailed = s.status === 'FAILED';
                  const isPending = s.status === 'PENDING' || s.status === 'IN_PROGRESS';

                  return (
                    <tr
                      key={s.id}
                      className="hover:bg-gray-50/70 transition-colors group"
                    >
                      {/* Ticker & Logo */}
                      <td className="py-4 px-3">
                        <div className="flex items-center gap-3">
                          <StockLogo ticker={s.ticker} size="sm" />
                          <span className="font-mono font-black text-sm text-[#111318] tracking-tight">
                            {s.ticker}
                          </span>
                        </div>
                      </td>

                      {/* Company Name */}
                      <td className="py-4 px-3 font-semibold text-sm text-gray-700">
                        {s.company_name || '—'}
                      </td>

                      {/* Status Badge Pill */}
                      <td className="py-4 px-3">
                        {isCompleted && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#E8F8EA] text-[#1E7E34] border border-[#C3E6CB]">
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#1E7E34]" />
                            <span>Completed</span>
                          </span>
                        )}
                        {isPending && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">
                            <Clock className="w-3.5 h-3.5 animate-spin text-amber-700" />
                            <span>In Progress</span>
                          </span>
                        )}
                        {isFailed && (
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-800 border border-rose-200">
                            <XCircle className="w-3.5 h-3.5 text-rose-600" />
                            <span>Failed</span>
                          </span>
                        )}
                      </td>

                      {/* Date */}
                      <td className="py-4 px-3">
                        <div className="flex items-center gap-2 text-xs font-medium text-gray-500">
                          <Calendar className="w-3.5 h-3.5 text-gray-400" />
                          <span>{formatDateTime(s.created_at)}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="py-4 px-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {isCompleted ? (
                            <>
                              <button
                                onClick={() => onSelectReport(s.id, 'report')}
                                className="h-8 px-3.5 rounded-xl bg-[#17191F] hover:bg-black active:scale-[0.98] text-white text-xs font-black transition inline-flex items-center gap-1.5 cursor-pointer shadow-xs"
                                title="View Complete Report"
                              >
                                <span>Report</span>
                                <ExternalLink className="w-3 h-3" />
                              </button>

                              <button
                                onClick={() =>
                                  setExportSession({
                                    id: s.id,
                                    ticker: s.ticker,
                                    companyName: s.company_name,
                                  })
                                }
                                className="h-8 w-8 rounded-xl border border-gray-200/90 hover:bg-gray-100 text-gray-700 transition flex items-center justify-center cursor-pointer shadow-2xs"
                                title="Export PDF, JSON, HTML, Markdown"
                              >
                                <Download className="w-3.5 h-3.5" />
                              </button>
                            </>
                          ) : isPending ? (
                            <button
                              onClick={() => onSelectReport(s.id, 'research')}
                              className="h-8 px-3.5 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-bold transition inline-flex items-center gap-1.5 cursor-pointer"
                              title="Track Analysis Progress"
                            >
                              <span>Track</span>
                              <Clock className="w-3 h-3" />
                            </button>
                          ) : (
                            <button
                              disabled
                              className="h-8 px-3.5 rounded-xl bg-gray-100 text-gray-400 text-xs font-bold opacity-60 cursor-not-allowed"
                            >
                              <span>Report</span>
                            </button>
                          )}

                          {/* Delete Session Button */}
                          <button
                            onClick={() => setSessionToDelete(s)}
                            className="h-8 w-8 rounded-xl border border-gray-200/90 hover:border-rose-200 hover:bg-rose-50 text-gray-400 hover:text-rose-600 transition flex items-center justify-center cursor-pointer shadow-2xs"
                            title="Delete Session"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {sessionToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-md bg-white rounded-[26px] p-6 shadow-2xl border border-gray-100 space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-11 h-11 rounded-2xl bg-rose-50 border border-rose-100 text-rose-600 flex items-center justify-center">
                <Trash2 className="w-5 h-5" />
              </div>
              <button
                onClick={() => setSessionToDelete(null)}
                className="w-8 h-8 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-700 flex items-center justify-center cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div>
              <h3 className="text-lg font-black text-[#111318]">
                Delete Research Session?
              </h3>
              <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">
                Are you sure you want to permanently delete session #{sessionToDelete.id} for{' '}
                <strong className="text-[#111318] font-black">{sessionToDelete.ticker}</strong>?
                This action cannot be undone and will delete the synthesized report from your workspace.
              </p>
            </div>

            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                onClick={() => setSessionToDelete(null)}
                disabled={deleting}
                className="px-4 py-2 rounded-xl text-xs font-bold text-gray-600 hover:bg-gray-100 cursor-pointer transition"
              >
                Cancel
              </button>

              <button
                onClick={handleDeleteSession}
                disabled={deleting}
                className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 active:scale-95 text-white text-xs font-black transition flex items-center gap-2 cursor-pointer disabled:opacity-50 shadow-xs"
              >
                {deleting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <span>Confirm Delete</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {exportSession && (
        <ExportModal
          sessionId={exportSession.id}
          ticker={exportSession.ticker}
          companyName={exportSession.companyName}
          onClose={() => setExportSession(null)}
        />
      )}
    </div>
  );
}
