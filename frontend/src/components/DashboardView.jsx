import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Layers,
  FileText,
  Clock,
  Target,
  PieChart,
  TrendingUp,
  Search,
  Filter,
  Info,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Calendar,
  X,
  LayoutGrid,
  List,
  MoreVertical,
  CheckCircle2,
  AlertCircle,
  ArrowUpRight,
  Sparkles,
  ExternalLink,
  RotateCw,
  Archive,
} from 'lucide-react';
import { api } from '../api/client';
import StockLogo from './StockLogo';

export default function DashboardView({
  onSelectSession,
  onNavigateToResearch,
  onNavigateToHistory,
}) {
  const [analytics, setAnalytics] = useState(null);
  const [recentSessions, setRecentSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [selectedSessionReport, setSelectedSessionReport] = useState(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters state
  const [statusFilter, setStatusFilter] = useState('all'); // 'all', 'in_progress', 'completed'
  const [sectorFilter, setSectorFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // User-controlled custom date range state (Req 2)
  const [customDateRange, setCustomDateRange] = useState({ start: '', end: '' });
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [tempStartDate, setTempStartDate] = useState('');
  const [tempEndDate, setTempEndDate] = useState('');
  const [dateError, setDateError] = useState('');
  const datePickerRef = useRef(null);

  // Functional Month Navigation Timeline state (Req 3)
  const [navMonthDate, setNavMonthDate] = useState(null);
  const [isMonthFilterActive, setIsMonthFilterActive] = useState(false);
  const [sliding, setSliding] = useState(false);
  const [slideDirection, setSlideDirection] = useState('next'); // 'prev' | 'next'

  // UI state for recent reports
  const [viewMode, setViewMode] = useState('list'); // 'list' | 'grid'
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close three-dot menu and date picker on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMoreMenuOpen(false);
      }
      if (datePickerRef.current && !datePickerRef.current.contains(e.target)) {
        setDatePickerOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsData, sessionsData] = await Promise.all([
        api.getWorkspaceAnalytics(),
        api.listSessions(20, 0),
      ]);
      setAnalytics(analyticsData);
      const sessions = sessionsData.sessions || [];
      setRecentSessions(sessions);

      // Select first session by default and initialize month navigation date
      if (sessions.length > 0) {
        setSelectedSessionId(sessions[0].id);
        const latestDate = new Date(sessions[0].created_at);
        setNavMonthDate(new Date(latestDate.getFullYear(), latestDate.getMonth(), 1));
      } else {
        setNavMonthDate(new Date());
      }
    } catch (err) {
      setError(err.message || 'Failed to load workspace dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // When selectedSessionId changes, load report detail for the right panel
  useEffect(() => {
    if (!selectedSessionId) {
      setSelectedSessionReport(null);
      return;
    }

    let isMounted = true;
    const loadSelectedReport = async () => {
      setLoadingReport(true);
      try {
        const report = await api.getReport(selectedSessionId);
        if (isMounted) setSelectedSessionReport(report);
      } catch {
        if (isMounted) setSelectedSessionReport(null);
      } finally {
        if (isMounted) setLoadingReport(false);
      }
    };

    loadSelectedReport();
    return () => {
      isMounted = false;
    };
  }, [selectedSessionId]);

  // KPI computations from real analytics
  const total = analytics?.total_sessions || 0;
  const completed = analytics?.status_counts?.completed || 0;
  const pending =
    (analytics?.status_counts?.pending || 0) +
    (analytics?.status_counts?.in_progress || 0);
  const avgConfidence = analytics?.average_confidence
    ? Math.round(analytics.average_confidence * 100)
    : 0;

  // Selected session object
  const selectedSession =
    recentSessions.find((s) => s.id === selectedSessionId) ||
    recentSessions[0] ||
    null;

  // Real session count for navMonthDate
  const sessionsInNavMonth = useMemo(() => {
    if (!navMonthDate) return 0;
    const year = navMonthDate.getFullYear();
    const month = String(navMonthDate.getMonth() + 1).padStart(2, '0');
    const monthKey = `${year}-${month}`;
    return recentSessions.filter(
      (s) => s.created_at && s.created_at.startsWith(monthKey)
    ).length;
  }, [navMonthDate, recentSessions]);

  // Month navigation handlers with smooth slide animation
  const handlePrevMonth = () => {
    setSlideDirection('prev');
    setSliding(true);
    setTimeout(() => {
      setNavMonthDate((prev) => {
        const base = prev || new Date();
        return new Date(base.getFullYear(), base.getMonth() - 1, 1);
      });
      setIsMonthFilterActive(true);
      setCustomDateRange({ start: '', end: '' });
      setTempStartDate('');
      setTempEndDate('');
      setSliding(false);
    }, 150);
  };

  const handleNextMonth = () => {
    setSlideDirection('next');
    setSliding(true);
    setTimeout(() => {
      setNavMonthDate((prev) => {
        const base = prev || new Date();
        return new Date(base.getFullYear(), base.getMonth() + 1, 1);
      });
      setIsMonthFilterActive(true);
      setCustomDateRange({ start: '', end: '' });
      setTempStartDate('');
      setTempEndDate('');
      setSliding(false);
    }, 150);
  };

  // Date range handlers
  const handleApplyDateRange = () => {
    if (!tempStartDate || !tempEndDate) {
      setDateError('Please select both start and end dates.');
      return;
    }
    if (tempEndDate < tempStartDate) {
      setDateError('End date cannot be earlier than start date.');
      return;
    }
    setDateError('');
    setCustomDateRange({ start: tempStartDate, end: tempEndDate });
    setIsMonthFilterActive(false); // Custom range overrides single month
    setDatePickerOpen(false);
  };

  const handleClearDateRange = () => {
    setTempStartDate('');
    setTempEndDate('');
    setDateError('');
    setCustomDateRange({ start: '', end: '' });
    setDatePickerOpen(false);
  };

  // Active filter status
  const hasCustomDateRange = Boolean(customDateRange.start && customDateRange.end);
  const activeFilterCount =
    (statusFilter !== 'all' ? 1 : 0) +
    (sectorFilter !== 'all' ? 1 : 0) +
    (hasCustomDateRange ? 1 : 0) +
    (isMonthFilterActive ? 1 : 0) +
    (searchQuery.trim() ? 1 : 0);

  const handleResetFilters = () => {
    setStatusFilter('all');
    setSectorFilter('all');
    setCustomDateRange({ start: '', end: '' });
    setTempStartDate('');
    setTempEndDate('');
    setDateError('');
    setIsMonthFilterActive(false);
    setSearchQuery('');
  };

  // Recommendation Formatter (e.g. STRONG_BUY -> Strong Buy)
  const formatRecommendation = (rec) => {
    if (!rec) return 'Unavailable';
    return rec
      .replace(/_/g, ' ')
      .toLowerCase()
      .split(' ')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  // Extract clean 2-3 line substantive executive narrative preview
  const formatExecutivePreview = (summary) => {
    if (!summary) return 'Executive summary unavailable for this report.';

    const lines = summary.split('\n').map((l) => l.trim()).filter(Boolean);

    // If an explicit Investment Thesis is present, prioritize its narrative
    const thesisLine = lines.find((l) =>
      l.toLowerCase().startsWith('investment thesis:')
    );
    if (thesisLine) {
      return thesisLine.replace(/^investment thesis:\s*/i, '');
    }

    // Otherwise strip boilerplate headers and redundant metadata lines
    const narrativeLines = lines.filter((l) => {
      const lower = l.toLowerCase();
      if (lower.startsWith('fincrew investment committee')) return false;
      if (lower.startsWith('consensus rating:')) return false;
      if (lower.startsWith('executive summary')) return false;
      return true;
    });

    if (narrativeLines.length > 0) {
      return narrativeLines
        .map((l) => l.replace(/^\d+\.\s*/, ''))
        .join(' ');
    }

    return summary;
  };

  // Filtered recent sessions list
  const filteredSessions = recentSessions.filter((s) => {
    // Status tab filter
    if (statusFilter === 'in_progress' && s.status !== 'IN_PROGRESS' && s.status !== 'PENDING') {
      return false;
    }
    if (statusFilter === 'completed' && s.status !== 'COMPLETED') {
      return false;
    }

    // Custom Date Range filter (Req 2)
    if (customDateRange.start && customDateRange.end && s.created_at) {
      const sessionDate = s.created_at.slice(0, 10);
      if (sessionDate < customDateRange.start || sessionDate > customDateRange.end) {
        return false;
      }
    }

    // Month filter (when active and custom date range is not applied, Req 3)
    if (!hasCustomDateRange && isMonthFilterActive && navMonthDate && s.created_at) {
      const year = navMonthDate.getFullYear();
      const month = String(navMonthDate.getMonth() + 1).padStart(2, '0');
      const monthKey = `${year}-${month}`;
      if (!s.created_at.startsWith(monthKey)) {
        return false;
      }
    }

    // Sector filter
    if (sectorFilter !== 'all') {
      const reportSec =
        s.sector ||
        (s.id === selectedSessionReport?.session_id
          ? selectedSessionReport?.fundamental_data?.market_research?.sector
          : null);
      if (reportSec && !reportSec.toLowerCase().includes(sectorFilter.toLowerCase())) {
        return false;
      }
    }

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTicker = s.ticker?.toLowerCase().includes(q);
      const matchCompany = s.company_name?.toLowerCase().includes(q);
      if (!matchTicker && !matchCompany) return false;
    }

    return true;
  });

  // Relative Date Formatter
  const formatRelativeDate = (dateStr) => {
    if (!dateStr) return 'Recent';
    try {
      const d = new Date(dateStr);
      const now = new Date();
      const diffMs = now - d;
      const diffHours = diffMs / (1000 * 60 * 60);

      if (diffHours < 24 && now.getDate() === d.getDate()) return 'Today';
      if (diffHours < 48 && now.getDate() - d.getDate() === 1) return 'Yesterday';

      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    } catch {
      return 'Recent';
    }
  };

  // Market Cap formatter helper
  const formatMarketCap = (val) => {
    if (val == null || isNaN(val) || val <= 0) return 'Unavailable';
    if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
    if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`;
    return `$${Number(val).toLocaleString()}`;
  };

  // Dynamic Sector list from analytics (no hardcoded fallback percentages)
  const rawSectors = analytics?.sector_percentages || {};
  const sectorEntries = Object.entries(rawSectors);
  const sectorList =
    sectorEntries.length > 0
      ? sectorEntries.map(([k, v]) => ({ name: k, pct: Math.round(v) }))
      : [];

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn select-none">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div className="lg:col-span-8 h-48 bg-white rounded-3xl animate-pulse shadow-xs" />
          <div className="lg:col-span-4 h-48 bg-white rounded-3xl animate-pulse shadow-xs" />
        </div>
        <div className="h-12 bg-white/60 rounded-full animate-pulse" />
        <div className="h-96 bg-[#17191F] rounded-3xl animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fadeIn select-none">
      {/* 1. TOP ANALYTICS ROW (Split into 2 white cards) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Card: 4 KPI Metrics + Activity Timeline */}
        <div className="lg:col-span-8 bg-white rounded-3xl p-6 sm:p-7 border border-[#DCE7F6] shadow-xs flex flex-col justify-between space-y-6">
          {/* Top 4 Metrics Columns */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {/* 1. Total Sessions */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center text-gray-700">
                  <Layers className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-[#64748B]">Total Sessions</span>
              </div>
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-2xl sm:text-3xl font-black text-[#111318]">
                  {total}
                </span>
              </div>
            </div>

            {/* 2. Completed Reports */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center text-gray-700">
                  <FileText className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-[#64748B]">Completed</span>
              </div>
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-2xl sm:text-3xl font-black text-[#111318]">
                  {completed}
                </span>
              </div>
            </div>

            {/* 3. Active / Pending */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center text-gray-700">
                  <Clock className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-[#64748B]">Active / Pending</span>
              </div>
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-2xl sm:text-3xl font-black text-[#111318]">
                  {pending}
                </span>
              </div>
            </div>

            {/* 4. Avg. Confidence */}
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gray-100 flex items-center justify-center text-gray-700">
                  <Target className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-[#64748B]">Avg. Confidence</span>
              </div>
              <div className="flex items-baseline gap-2 pt-1">
                <span className="text-2xl sm:text-3xl font-black text-[#111318]">
                  {avgConfidence}%
                </span>
              </div>
            </div>
          </div>

          {/* Functional Horizontal Month Navigation (Req 3) */}
          <div className="pt-3 border-t border-gray-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-gray-500" />
              <span className="text-xs font-bold text-[#64748B]">Month Timeline</span>
              {isMonthFilterActive && (
                <span className="px-2 py-0.5 rounded-full bg-[#C5F500] text-[#111318] text-[10px] font-black animate-fadeIn">
                  Filtering List
                </span>
              )}
            </div>

            <div className="flex items-center gap-1.5 bg-gray-50 p-1.5 rounded-2xl border border-gray-200/70 shadow-2xs">
              <button
                type="button"
                onClick={handlePrevMonth}
                className="w-8 h-8 rounded-xl bg-white hover:bg-gray-100 text-gray-700 flex items-center justify-center transition shadow-2xs cursor-pointer active:scale-95"
                title="Previous month"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <div
                onClick={() => {
                  setIsMonthFilterActive((prev) => !prev);
                  if (!isMonthFilterActive) {
                    setCustomDateRange({ start: '', end: '' });
                    setTempStartDate('');
                    setTempEndDate('');
                  }
                }}
                className={`px-3.5 py-1.5 rounded-xl cursor-pointer select-none transition-all flex items-center gap-2 ${
                  isMonthFilterActive
                    ? 'bg-white ring-2 ring-[#C5F500] shadow-xs'
                    : 'bg-white/80 hover:bg-white'
                }`}
                title={isMonthFilterActive ? 'Click to show all months' : 'Click to filter by this month'}
              >
                <div
                  className={`w-2 h-2 rounded-full transition-all ${
                    isMonthFilterActive ? 'bg-[#16A34A] scale-125' : 'bg-gray-300'
                  }`}
                />
                <div
                  className={`transition-all duration-200 transform ${
                    sliding
                      ? slideDirection === 'next'
                        ? '-translate-x-2 opacity-30'
                        : 'translate-x-2 opacity-30'
                      : 'translate-x-0 opacity-100'
                  }`}
                >
                  <span className="font-extrabold text-xs text-[#111318] whitespace-nowrap">
                    {navMonthDate
                      ? navMonthDate.toLocaleDateString('en-US', {
                          month: 'long',
                          year: 'numeric',
                        })
                      : 'November 2026'}
                  </span>
                  <span className="text-[10px] font-semibold text-gray-500 ml-1.5">
                    ({sessionsInNavMonth} {sessionsInNavMonth === 1 ? 'report' : 'reports'})
                  </span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleNextMonth}
                className="w-8 h-8 rounded-xl bg-white hover:bg-gray-100 text-gray-700 flex items-center justify-center transition shadow-2xs cursor-pointer active:scale-95"
                title="Next month"
              >
                <ChevronRight className="w-4 h-4" />
              </button>

              {isMonthFilterActive && (
                <button
                  type="button"
                  onClick={() => setIsMonthFilterActive(false)}
                  className="px-2 py-1 text-[10px] font-bold text-gray-500 hover:text-gray-900 transition cursor-pointer"
                  title="Show all months"
                >
                  Show All
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Card: Sector Exposure Progress Bars */}
        <div className="lg:col-span-4 bg-white rounded-3xl p-6 sm:p-7 border border-[#DCE7F6] shadow-xs flex flex-col justify-between space-y-4">
          <div className="flex items-center gap-2">
            <PieChart className="w-4.5 h-4.5 text-[#111318]" />
            <h3 className="text-base font-black text-[#111318] tracking-tight">
              Sector Exposure
            </h3>
          </div>

          <div className="space-y-3 pt-1">
            {sectorList.length > 0 ? (
              sectorList.slice(0, 5).map((sec) => (
                <div key={sec.name} className="flex items-center gap-3 text-xs">
                  <span
                    className="min-w-[130px] flex-shrink-0 font-bold text-[#111318] truncate"
                    title={sec.name}
                  >
                    {sec.name}
                  </span>
                  <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
                    <div
                      className="h-full bg-[#C5F500] rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(100, Math.max(0, sec.pct))}%` }}
                    />
                  </div>
                  <span className="w-10 text-right font-extrabold text-[#64748B]">
                    {sec.pct}%
                  </span>
                </div>
              ))
            ) : (
              <div className="py-6 text-center text-xs text-gray-400 font-medium">
                No sector exposure data available yet.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 2. ACTIVE FILTERS & SEARCH ROW (Req 1, 2, 6) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Sector Filter Dropdown */}
          <div className="relative h-10">
            <select
              value={sectorFilter}
              onChange={(e) => setSectorFilter(e.target.value)}
              className="appearance-none h-10 pl-3.5 pr-8 rounded-full bg-white border border-[#DCE7F6] text-xs font-bold text-[#111318] shadow-xs focus:outline-none focus:ring-1 focus:ring-[#C5F500] cursor-pointer"
            >
              <option value="all">All Sectors</option>
              {sectorList.map((sec) => (
                <option key={sec.name} value={sec.name.toLowerCase()}>
                  {sec.name}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* User-Controlled Custom Date Range Selector (Req 2) */}
          <div className="relative" ref={datePickerRef}>
            <button
              type="button"
              onClick={() => setDatePickerOpen((prev) => !prev)}
              className={`h-10 px-4 rounded-full bg-white border text-xs font-bold flex items-center gap-2 cursor-pointer transition shadow-xs ${
                hasCustomDateRange
                  ? 'border-[#C5F500] text-[#111318] ring-1 ring-[#C5F500]'
                  : 'border-[#DCE7F6] text-gray-600 hover:text-[#111318] hover:border-gray-300'
              }`}
            >
              <Calendar className="w-4 h-4 text-gray-500" />
              <span>
                {hasCustomDateRange
                  ? `${customDateRange.start} → ${customDateRange.end}`
                  : 'Select date range'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
            </button>

            {datePickerOpen && (
              <div className="absolute left-0 top-12 w-80 bg-white border border-[#DCE7F6] rounded-2xl shadow-2xl p-4 z-40 animate-fadeIn space-y-3.5">
                <div className="flex items-center justify-between pb-2 border-b border-gray-100">
                  <span className="text-xs font-black text-[#111318]">Custom Date Range</span>
                  <button
                    type="button"
                    onClick={() => setDatePickerOpen(false)}
                    className="w-6 h-6 rounded-full hover:bg-gray-100 text-gray-400 hover:text-gray-700 flex items-center justify-center cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>

                {dateError && (
                  <div className="p-2 rounded-xl bg-rose-50 border border-rose-200 text-[11px] font-semibold text-rose-600">
                    {dateError}
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2.5">
                  <div>
                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={tempStartDate}
                      onChange={(e) => {
                        setTempStartDate(e.target.value);
                        setDateError('');
                      }}
                      className="w-full h-9 px-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-[#111318] focus:outline-none focus:ring-1 focus:ring-[#C5F500]"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-1">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={tempEndDate}
                      min={tempStartDate || undefined}
                      onChange={(e) => {
                        setTempEndDate(e.target.value);
                        setDateError('');
                      }}
                      className="w-full h-9 px-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-[#111318] focus:outline-none focus:ring-1 focus:ring-[#C5F500]"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <button
                    type="button"
                    onClick={handleApplyDateRange}
                    disabled={!tempStartDate || !tempEndDate}
                    className="flex-1 h-9 rounded-xl bg-[#C5F500] hover:bg-[#b8e600] active:scale-98 text-[#111318] font-black text-xs transition cursor-pointer disabled:opacity-40 shadow-xs"
                  >
                    Apply Range
                  </button>
                  <button
                    type="button"
                    onClick={handleClearDateRange}
                    className="px-3.5 h-9 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold text-xs transition cursor-pointer"
                  >
                    Clear
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Active Filter Indicator & Reset (Req 6 - Only shown when filters are active!) */}
          {activeFilterCount > 0 && (
            <div className="flex items-center gap-1.5 animate-fadeIn">
              <div className="flex items-center gap-1.5 h-10 px-3.5 rounded-full bg-[#C5F500]/20 border border-[#C5F500]/50 text-xs font-bold text-[#111318] select-none">
                <span>Filters active</span>
                <span className="w-4 h-4 rounded-full bg-[#C5F500] text-[#111318] text-[10px] font-black flex items-center justify-center">
                  {activeFilterCount}
                </span>
              </div>
              <button
                type="button"
                onClick={handleResetFilters}
                className="flex items-center gap-1 h-10 px-3.5 rounded-full bg-white border border-[#DCE7F6] text-xs font-bold text-rose-500 hover:bg-rose-50 hover:border-rose-200 transition shadow-xs cursor-pointer"
                title="Reset all filters"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reset</span>
              </button>
            </div>
          )}
        </div>

        {/* Search Input Box */}
        <div className="relative sm:w-72">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search stocks, reports..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full h-10 pl-10 pr-9 rounded-full bg-white border border-[#DCE7F6] text-xs font-semibold text-[#111318] placeholder-gray-400 shadow-xs focus:outline-none focus:ring-2 focus:ring-[#C5F500]/50 transition-all"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 hover:text-gray-600 flex items-center justify-center cursor-pointer"
              title="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* 3. RECENT RESEARCH REPORTS DARK CHARCOAL PANEL */}
      <div className="bg-[#17191F] text-white rounded-3xl p-6 sm:p-7 shadow-xl border border-[#232731] space-y-6">
        {/* Header Bar */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-gray-800">
          <div className="flex items-center gap-2.5">
            <TrendingUp className="w-5 h-5 text-[#C5F500]" />
            <h2 className="text-lg font-black tracking-tight text-white">
              Recent Research Reports
            </h2>
          </div>

          <div className="flex items-center gap-3">
            {/* Filter Tabs: All Reports / In Progress / Completed */}
            <div className="flex items-center bg-[#232731] p-1 rounded-full text-xs font-bold text-gray-300">
              <button
                onClick={() => setStatusFilter('all')}
                className={`px-3 py-1.5 rounded-full transition cursor-pointer ${
                  statusFilter === 'all'
                    ? 'bg-white/15 text-white'
                    : 'hover:text-white'
                }`}
              >
                All Reports
              </button>
              <button
                onClick={() => setStatusFilter('in_progress')}
                className={`px-3 py-1.5 rounded-full flex items-center gap-1.5 transition cursor-pointer ${
                  statusFilter === 'in_progress'
                    ? 'bg-[#C5F500] text-[#111318]'
                    : 'hover:text-white'
                }`}
              >
                <span>In Progress</span>
                <span className="px-1.5 py-0.2 rounded-full bg-white/20 text-[10px]">
                  {pending}
                </span>
              </button>
              <button
                onClick={() => setStatusFilter('completed')}
                className={`px-3 py-1.5 rounded-full flex items-center gap-1.5 transition cursor-pointer ${
                  statusFilter === 'completed'
                    ? 'bg-white/15 text-white'
                    : 'hover:text-white'
                }`}
              >
                <span>Completed</span>
                <span className="px-1.5 py-0.2 rounded-full bg-white/20 text-[10px]">
                  {completed}
                </span>
              </button>
            </div>

            {/* View Mode Toggle: List vs Grid */}
            <button
              onClick={() => setViewMode((prev) => (prev === 'list' ? 'grid' : 'list'))}
              title={viewMode === 'list' ? 'Switch to Grid View' : 'Switch to List View'}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition cursor-pointer ${
                viewMode === 'grid'
                  ? 'bg-[#C5F500] text-[#111318]'
                  : 'bg-[#232731] text-gray-300 hover:text-white'
              }`}
            >
              {viewMode === 'list' ? (
                <LayoutGrid className="w-4 h-4" />
              ) : (
                <List className="w-4 h-4" />
              )}
            </button>

            {/* More Options Dropdown Menu */}
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMoreMenuOpen((prev) => !prev)}
                title="More options"
                className={`w-8 h-8 rounded-full flex items-center justify-center transition cursor-pointer ${
                  moreMenuOpen
                    ? 'bg-white/20 text-white'
                    : 'bg-[#232731] text-gray-300 hover:text-white'
                }`}
              >
                <MoreVertical className="w-4 h-4" />
              </button>

              {moreMenuOpen && (
                <div className="absolute right-0 top-10 w-52 bg-[#1E222B] border border-white/10 rounded-2xl shadow-2xl py-2 z-30 animate-fadeIn text-xs">
                  <button
                    onClick={() => {
                      setMoreMenuOpen(false);
                      fetchDashboardData();
                    }}
                    className="w-full px-4 py-2.5 text-left text-gray-200 hover:bg-white/10 hover:text-white flex items-center gap-2.5 transition cursor-pointer"
                  >
                    <RotateCw className="w-3.5 h-3.5 text-[#C5F500]" />
                    <span>Refresh Reports</span>
                  </button>
                  <button
                    onClick={() => {
                      setMoreMenuOpen(false);
                      if (onNavigateToHistory) onNavigateToHistory();
                      else onSelectSession(null, 'history');
                    }}
                    className="w-full px-4 py-2.5 text-left text-gray-200 hover:bg-white/10 hover:text-white flex items-center gap-2.5 transition cursor-pointer"
                  >
                    <Archive className="w-3.5 h-3.5 text-[#C5F500]" />
                    <span>Research Archives</span>
                  </button>
                  <button
                    onClick={() => {
                      setMoreMenuOpen(false);
                      onNavigateToResearch();
                    }}
                    className="w-full px-4 py-2.5 text-left text-gray-200 hover:bg-white/10 hover:text-white flex items-center gap-2.5 transition cursor-pointer"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-[#C5F500]" />
                    <span>New Stock Analysis</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Empty State */}
        {filteredSessions.length === 0 ? (
          <div className="py-16 text-center space-y-4">
            <div className="w-14 h-14 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-gray-400 mx-auto">
              <Layers className="w-7 h-7" />
            </div>
            <h4 className="text-base font-bold text-white">No research reports found</h4>
            <p className="text-xs text-gray-400 max-w-sm mx-auto">
              {hasCustomDateRange
                ? `No reports found between ${customDateRange.start} and ${customDateRange.end}.`
                : isMonthFilterActive && navMonthDate
                ? `No reports found for ${navMonthDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}.`
                : searchQuery
                ? `No reports matching "${searchQuery}". Clear your search query to view all sessions.`
                : sectorFilter !== 'all'
                ? `No reports found in the ${sectorFilter} sector.`
                : 'Initiate autonomous research on any stock ticker to generate institutional dossiers.'}
            </p>
            {activeFilterCount > 0 ? (
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-5 py-2.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-bold inline-flex items-center gap-2 cursor-pointer shadow-sm transition"
              >
                <X className="w-3.5 h-3.5" />
                <span>Reset Filters</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={onNavigateToResearch}
                className="px-5 py-2.5 rounded-full bg-[#C5F500] text-[#111318] text-xs font-black inline-flex items-center gap-2 cursor-pointer shadow-sm hover:bg-[#b8e600]"
              >
                <Sparkles className="w-4 h-4" />
                <span>Start First Stock Analysis</span>
              </button>
            )}
          </div>
        ) : (
          /* Split Layout: Left Selectable List/Grid + Right Report Details Panel */
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Selectable Sessions (approx 38% width) */}
            <div className="lg:col-span-5 max-h-[460px] overflow-y-auto pr-1">
              {viewMode === 'list' ? (
                <div className="space-y-2">
                  {filteredSessions.map((session) => {
                    const isSelected = session.id === selectedSession?.id;
                    const isCompleted = session.status === 'COMPLETED';
                    const isFailed = session.status === 'FAILED';

                    return (
                      <div
                        key={session.id}
                        onClick={() => setSelectedSessionId(session.id)}
                        className={`p-3.5 rounded-2xl flex items-center justify-between gap-3 cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-white/15 ring-1 ring-white/20 shadow-md'
                            : 'bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <StockLogo ticker={session.ticker} size="sm" />
                          <div className="min-w-0">
                            <div className="font-extrabold text-sm text-white truncate flex items-center gap-1.5">
                              <span>{session.ticker}</span>
                              <span className="text-gray-400 font-normal">•</span>
                              <span className="text-gray-300 font-medium truncate text-xs">
                                {session.company_name || session.ticker}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          {isCompleted && (
                            <span className="px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-[11px] font-bold">
                              Completed
                            </span>
                          )}
                          {!isCompleted && !isFailed && (
                            <span className="px-2.5 py-1 rounded-full bg-[#C5F500] text-[#111318] text-[11px] font-black">
                              In Progress
                            </span>
                          )}
                          {isFailed && (
                            <span className="px-2.5 py-1 rounded-full bg-rose-500/20 text-rose-400 text-[11px] font-bold">
                              Failed
                            </span>
                          )}

                          <span className="text-[11px] text-gray-400 hidden sm:block">
                            {formatRelativeDate(session.created_at)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {filteredSessions.map((session) => {
                    const isSelected = session.id === selectedSession?.id;
                    const isCompleted = session.status === 'COMPLETED';
                    const isFailed = session.status === 'FAILED';

                    return (
                      <div
                        key={session.id}
                        onClick={() => setSelectedSessionId(session.id)}
                        className={`p-3 rounded-2xl flex flex-col justify-between gap-2.5 cursor-pointer transition-all ${
                          isSelected
                            ? 'bg-white/15 ring-2 ring-[#C5F500] shadow-md'
                            : 'bg-white/5 hover:bg-white/10'
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <StockLogo ticker={session.ticker} size="sm" />
                          <div className="min-w-0 flex-1">
                            <div className="font-black text-sm text-white leading-tight">
                              {session.ticker}
                            </div>
                            <div className="text-[11px] text-gray-300 truncate">
                              {session.company_name || session.ticker}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-1 border-t border-white/5">
                          {isCompleted && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                              Completed
                            </span>
                          )}
                          {!isCompleted && !isFailed && (
                            <span className="px-2 py-0.5 rounded-full bg-[#C5F500] text-[#111318] text-[10px] font-black">
                              In Progress
                            </span>
                          )}
                          {isFailed && (
                            <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 text-[10px] font-bold">
                              Failed
                            </span>
                          )}

                          <span className="text-[10px] text-gray-400">
                            {formatRelativeDate(session.created_at)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Right Report Details Panel (approx 62% width) */}
            <div className="lg:col-span-7 bg-[#233342]/90 backdrop-blur-md rounded-2xl p-5 sm:p-6 border border-white/10 text-white space-y-4">
              {selectedSession ? (
                <>
                  {/* Top Header of Detail Panel */}
                  <div className="space-y-1">
                    <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">
                      Report Details
                    </span>

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
                      <div className="flex items-center gap-3">
                        <StockLogo ticker={selectedSession.ticker} size="md" />
                        <div>
                          <h3 className="text-xl sm:text-2xl font-black text-white">
                            {selectedSession.ticker} • {selectedSession.company_name || selectedSession.ticker}
                          </h3>
                        </div>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-gray-300">
                        <div>
                          <span className="text-gray-400 block text-[10px]">Sector</span>
                          <span className="font-bold text-white">
                            {selectedSessionReport?.fundamental_data?.market_research?.sector ||
                              selectedSessionReport?.fundamental_data?.market_research?.supporting_data?.sector ||
                              'Unavailable'}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 pl-3 border-l border-white/10">
                          <div className="w-7 h-7 rounded-full bg-[#C5F500] text-[#111318] font-bold flex items-center justify-center text-xs">
                            AI
                          </div>
                          <div>
                            <span className="text-gray-400 block text-[10px]">Analyst</span>
                            <span className="font-bold text-white truncate">FinCrew Committee</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 4 Quantitative Metrics Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                    {/* Market Cap */}
                    <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                        Market Cap
                      </span>
                      <div className="font-black text-sm sm:text-base text-white">
                        {formatMarketCap(
                          selectedSessionReport?.fundamental_data?.market_research?.supporting_data?.market_cap ??
                          selectedSessionReport?.fundamental_data?.market_research?.market_cap
                        )}
                      </div>
                    </div>

                    {/* Price with Implied Upside if available */}
                    <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                        Price
                      </span>
                      <div className="font-black text-sm sm:text-base text-white flex items-center gap-1.5 flex-wrap">
                        <span>
                          {selectedSessionReport?.current_price != null
                            ? `$${selectedSessionReport.current_price.toFixed(2)}`
                            : 'Unavailable'}
                        </span>
                        {selectedSessionReport?.current_price != null &&
                          selectedSessionReport?.target_price != null &&
                          selectedSessionReport.current_price > 0 && (
                            <span
                              className={`text-[10px] font-bold ${
                                selectedSessionReport.target_price >= selectedSessionReport.current_price
                                  ? 'text-[#C5F500]'
                                  : 'text-rose-400'
                              }`}
                            >
                              {selectedSessionReport.target_price >= selectedSessionReport.current_price
                                ? '▲ +'
                                : '▼ '}
                              {(
                                ((selectedSessionReport.target_price - selectedSessionReport.current_price) /
                                  selectedSessionReport.current_price) *
                                100
                              ).toFixed(1)}
                              %
                            </span>
                          )}
                      </div>
                    </div>

                    {/* Confidence */}
                    <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                        Confidence
                      </span>
                      <div className="font-black text-sm sm:text-base text-white">
                        {selectedSessionReport?.confidence_score != null
                          ? `${Math.round(selectedSessionReport.confidence_score * 100)}%`
                          : 'Unavailable'}
                      </div>
                    </div>

                    {/* Recommendation Pill */}
                    <div className="p-3.5 rounded-xl bg-white/5 border border-white/5 space-y-1">
                      <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                        Rating
                      </span>
                      <div>
                        {selectedSessionReport?.recommendation ? (
                          <span className="px-2.5 py-1 rounded-full bg-[#C5F500] text-[#111318] font-black text-xs inline-flex items-center gap-1">
                            <span>
                              {formatRecommendation(selectedSessionReport.recommendation)}
                            </span>
                            <ArrowUpRight className="w-3 h-3 stroke-[3]" />
                          </span>
                        ) : (
                          <span className="text-sm font-bold text-gray-400">Unavailable</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Research Summary Box with Clean Narrative Preview */}
                  <div className="space-y-2 pt-1">
                    <div className="flex items-center gap-2 text-xs font-bold text-gray-300">
                      <FileText className="w-3.5 h-3.5 text-[#C5F500]" />
                      <span>Research Summary</span>
                    </div>
                    <p className="text-xs sm:text-sm text-gray-200 leading-relaxed bg-white/5 p-4 rounded-xl border border-white/5 line-clamp-3 font-normal">
                      {formatExecutivePreview(
                        selectedSessionReport?.executive_summary ||
                          (selectedSession.status === 'COMPLETED'
                            ? 'Executive summary unavailable for this report.'
                            : 'Research pipeline is currently running. Full consensus report will be available once complete.')
                      )}
                    </p>
                  </div>

                  {/* Action Button: View Full Report */}
                  <div className="pt-2">
                    <button
                      onClick={() => onSelectSession(selectedSession.id, 'report')}
                      className="w-full sm:w-auto h-11 px-7 rounded-full bg-[#C5F500] hover:bg-[#b8e600] active:scale-98 text-[#111318] font-black text-xs sm:text-sm flex items-center justify-center gap-2 transition-all shadow-md cursor-pointer"
                    >
                      <FileText className="w-4 h-4 stroke-[2.5]" />
                      <span>View Full Report</span>
                    </button>
                  </div>
                </>
              ) : (
                <div className="py-12 text-center text-gray-400 text-xs">
                  Select a research report from the list to preview summary.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
