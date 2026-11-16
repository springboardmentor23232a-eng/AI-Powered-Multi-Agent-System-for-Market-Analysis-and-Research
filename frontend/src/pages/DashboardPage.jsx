/**
 * DashboardPage.jsx
 * SAI ANALYSIS — Multi-Agent Stock Research & Market Intelligence
 * 
 * Composition:
 * - Persistent left sidebar with logo, navigation tabs, engine status, and user profile pill
 * - Top navigation bar with greeting, quick search, notification bell, and primary research trigger
 * - Prominent stock lookup & execution controller with debounced autocomplete & period selector
 * - 4-Card Bento KPI Grid with real embedded SVG sparklines
 * - Large interactive SVG Stock Performance Chart with gradient fill & volume bars
 * - Research Intelligence & Pipeline Health panel with circular data integrity gauge
 * - Dual workspace: Recent Research Activity & Saved Stocks Watchlist
 * - Expandable verified OHLCV trading candles table
 * - Research report viewer modal
 */

import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  TrendingUp,
  Search,
  LogOut,
  Building2,
  ShieldCheck,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Clock,
  History,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Bookmark,
  Plus,
  Check,
  Bell,
  LayoutDashboard,
  Cpu,
  BarChart2,
  ChevronDown,
  ChevronUp,
  Sliders,
} from 'lucide-react';
import Spinner from '../components/ui/Spinner';
import AlertBanner from '../components/ui/AlertBanner';
import ReportModal from '../components/research/ReportModal';
import WatchlistSection from '../components/watchlist/WatchlistSection';

const QUICK_TICKERS = ['INFY.NS', 'TCS.NS', 'AAPL', 'MSFT', 'NVDA', 'RELIANCE.NS'];

// ── Real Data SVG Sparkline Component ───────────────────────────────────────
function Sparkline({ data = [], height = 38, width = 110, color = '#f43f5e' }) {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((val, idx) => {
    const x = (idx / (data.length - 1)) * (width - 6) + 3;
    const y = height - 5 - ((val - min) / range) * (height - 10);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const areaPoints = `3,${height} ${points} ${width - 3},${height}`;
  const gradId = `spark-${Math.abs(data[0] || 0)}-${data.length}`;

  return (
    <svg width={width} height={height} className="overflow-visible shrink-0" aria-hidden="true">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor="#060608" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#${gradId})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ── Interactive High-Definition Stock Performance Chart ──────
function StockPerformanceChart({ history, period, onPeriodChange, currency = 'USD' }) {
  const candles = history?.candles || [];
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (candles.length === 0) return null;

  const closes = candles.map((c) => c.close);
  const minPrice = Math.min(...closes);
  const maxPrice = Math.max(...closes);
  const priceRange = maxPrice - minPrice || 1;

  const volumes = candles.map((c) => c.volume);
  const maxVolume = Math.max(...volumes) || 1;

  const width = 800;
  const height = 280;
  const paddingTop = 25;
  const paddingBottom = 45;
  const paddingX = 25;
  const chartHeight = height - paddingTop - paddingBottom;

  const points = candles.map((c, i) => {
    const x = paddingX + (i / Math.max(candles.length - 1, 1)) * (width - 2 * paddingX);
    const y = paddingTop + (1 - (c.close - minPrice) / priceRange) * chartHeight;
    return { x, y, ...c };
  });

  const lineD = points.reduce((acc, p, i) => (i === 0 ? `M ${p.x},${p.y}` : `${acc} L ${p.x},${p.y}`), '');
  const areaD = `${lineD} L ${points[points.length - 1].x},${height - paddingBottom} L ${points[0].x},${height - paddingBottom} Z`;

  // X-axis date labels (sample 5 dates)
  const step = Math.max(Math.floor(candles.length / 5), 1);
  const dateIndices = [0, step, step * 2, step * 3, candles.length - 1].filter((idx, i, arr) => arr.indexOf(idx) === i && idx < candles.length);

  const activeCandle = hoveredIndex !== null ? points[hoveredIndex] : points[points.length - 1];
  const isUp = activeCandle?.close >= activeCandle?.open;

  const periods = [
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
    { label: '5Y', value: '5y' },
  ];

  return (
    <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col gap-4 relative overflow-hidden">
      {/* Chart Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white tracking-tight uppercase">
              Stock Performance Overview
            </h3>
            <span className="text-xs font-mono font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
              {candles.length} Trading Days
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Verified OHLCV trajectory • Provider: <span className="text-zinc-200 font-mono">{history.data_source || 'Market API'}</span>
          </p>
        </div>

        {/* Timeframe Selector Pills */}
        <div className="flex items-center gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/[0.08] self-start sm:self-auto">
          {periods.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => onPeriodChange(p.value)}
              className={`px-3 py-1 text-xs font-mono font-semibold rounded-lg transition-all ${
                period === p.value
                  ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-sm shadow-rose-950'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.05]'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Hover Active Stats Callout */}
      <div className="flex flex-wrap items-center justify-between text-xs font-mono px-2 py-1 bg-white/[0.02] rounded-lg border border-white/[0.04]">
        <div className="flex items-center gap-4">
          <span className="text-zinc-400">Date: <strong className="text-white">{activeCandle?.date}</strong></span>
          <span className="text-zinc-400">Close: <strong className={isUp ? 'text-emerald-400' : 'text-rose-400'}>{currency === 'INR' ? '₹' : '$'}{activeCandle?.close.toFixed(2)}</strong></span>
          <span className="text-zinc-400 hidden sm:inline">Open: <strong className="text-zinc-200">{activeCandle?.open.toFixed(2)}</strong></span>
          <span className="text-zinc-400 hidden sm:inline">High: <strong className="text-emerald-400">{activeCandle?.high.toFixed(2)}</strong></span>
          <span className="text-zinc-400 hidden sm:inline">Low: <strong className="text-rose-400">{activeCandle?.low.toFixed(2)}</strong></span>
        </div>
        <div className="text-zinc-400 hidden md:block">
          Volume: <strong className="text-white">{activeCandle?.volume.toLocaleString()}</strong>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto max-h-[300px] overflow-visible select-none"
          preserveAspectRatio="none"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="chartGradientMain" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#e11d48" stopOpacity="0.45" />
              <stop offset="60%" stopColor="#be123c" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#060608" stopOpacity="0" />
            </linearGradient>

            <linearGradient id="volBarGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#881337" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = paddingTop + pct * chartHeight;
            const price = maxPrice - pct * priceRange;
            return (
              <g key={idx}>
                <line
                  x1={paddingX}
                  y1={y}
                  x2={width - paddingX}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeDasharray="4 4"
                />
                <text
                  x={width - paddingX + 8}
                  y={y + 3}
                  fill="rgba(161, 161, 170, 0.6)"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="start"
                >
                  {currency === 'INR' ? '₹' : '$'}{price.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Volume Bars at Bottom */}
          {points.map((p, i) => {
            const barHeight = Math.max((p.volume / maxVolume) * 35, 2);
            const y = height - paddingBottom - barHeight;
            const barWidth = Math.max((width - 2 * paddingX) / candles.length - 2, 2);
            return (
              <rect
                key={`vol-${i}`}
                x={p.x - barWidth / 2}
                y={y}
                width={barWidth}
                height={barHeight}
                fill="url(#volBarGrad)"
                opacity="0.6"
              />
            );
          })}

          {/* Main Area Fill */}
          <path d={areaD} fill="url(#chartGradientMain)" />

          {/* Main Stroke Line */}
          <path
            d={lineD}
            fill="none"
            stroke="#f43f5e"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Interactive Hover Point & Vertical Crosshair */}
          {hoveredIndex !== null && points[hoveredIndex] && (
            <g>
              <line
                x1={points[hoveredIndex].x}
                y1={paddingTop}
                x2={points[hoveredIndex].x}
                y2={height - paddingBottom}
                stroke="#f43f5e"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              <circle
                cx={points[hoveredIndex].x}
                cy={points[hoveredIndex].y}
                r="5"
                fill="#ffffff"
                stroke="#e11d48"
                strokeWidth="2.5"
              />
            </g>
          )}

          {/* Transparent Hover Hitboxes */}
          {points.map((p, i) => {
            const hitWidth = width / candles.length;
            return (
              <rect
                key={`hit-${i}`}
                x={p.x - hitWidth / 2}
                y={0}
                width={hitWidth}
                height={height}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoveredIndex(i)}
              />
            );
          })}

          {/* X-axis Date Labels */}
          {dateIndices.map((idx) => {
            const p = points[idx];
            if (!p) return null;
            return (
              <text
                key={`date-${idx}`}
                x={p.x}
                y={height - 12}
                fill="rgba(161, 161, 170, 0.7)"
                fontSize="10"
                fontFamily="monospace"
                textAnchor="middle"
              >
                {p.date}
              </text>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

// ── Research Intelligence & Telemetry Donut Panel ─
function TelemetryHealthPanel({ validation, overview }) {
  if (!validation) return null;

  const total = validation.total_raw_records || 1;
  const clean = validation.cleaned_records || 0;
  const cleanPct = Math.min(Math.round((clean / total) * 100), 100);

  // SVG circular gauge
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (cleanPct / 100) * circumference;

  return (
    <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between gap-5">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-rose-500" />
            <h3 className="text-sm font-bold text-white tracking-tight uppercase">
              Pipeline Health & Telemetry
            </h3>
          </div>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
            Verified
          </span>
        </div>

        {/* Circular Donut Gauge & Summary */}
        <div className="flex items-center gap-5 mt-4">
          <div className="relative flex items-center justify-center shrink-0">
            <svg width="94" height="94" className="rotate-[-90deg]">
              <circle
                cx="47"
                cy="47"
                r={radius}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="7"
                fill="none"
              />
              <circle
                cx="47"
                cy="47"
                r={radius}
                stroke="#e11d48"
                strokeWidth="7"
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                className="transition-all duration-700 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="font-mono text-base font-extrabold text-white leading-none">
                {cleanPct}%
              </span>
              <span className="text-[9px] font-mono text-zinc-400 uppercase mt-0.5">Integrity</span>
            </div>
          </div>

          <div className="flex-1 space-y-1.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Clean Records
              </span>
              <span className="font-mono font-bold text-white">{validation.cleaned_records}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500" /> Duplicates Filtered
              </span>
              <span className="font-mono font-bold text-zinc-300">{validation.duplicates_removed}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Raw Ingested
              </span>
              <span className="font-mono font-bold text-zinc-300">{validation.total_raw_records}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Profile & Metadata tags */}
      <div className="pt-3 border-t border-white/[0.06] flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
          <span className="text-zinc-500">Order:</span>
          <span className="font-bold text-emerald-400">
            {validation.is_chronological ? 'Strict Chronological (Asc)' : 'Reordered'}
          </span>
        </div>
        {overview && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white/[0.04] text-zinc-300 border border-white/[0.08]">
              {overview.sector}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/20">
              {overview.currency}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white/[0.04] text-zinc-300 border border-white/[0.08]">
              {overview.exchange}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Dashboard Page Component ───────────────────────────────────────────
export default function DashboardPage() {
  const navigate = useNavigate();

  // User state
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('currentUser') || '{}');
    } catch {
      return {};
    }
  });

  const [ticker, setTicker] = useState('INFY.NS');
  const [market, setMarket] = useState('NSE');
  const [period, setPeriod] = useState('1mo');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // User preferences state (Task 6)
  const [preferenceUpdatedAt, setPreferenceUpdatedAt] = useState(null);
  const [loadingPreferences, setLoadingPreferences] = useState(false);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [preferenceSuccess, setPreferenceSuccess] = useState(null);
  const [preferenceError, setPreferenceError] = useState(null);

  const [overview, setOverview] = useState(null);
  const [history, setHistory] = useState(null);

  // User-specific research history state
  const [researchHistory, setResearchHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const [selectedReportTaskId, setSelectedReportTaskId] = useState(null);

  // Watchlist state (Task 5)
  const [watchlist, setWatchlist] = useState([]);
  const [loadingWatchlist, setLoadingWatchlist] = useState(false);
  const [watchlistError, setWatchlistError] = useState(null);
  const [watchlistSuccess, setWatchlistSuccess] = useState(null);
  const [addingWatchlist, setAddingWatchlist] = useState(false);

  // Interactive live search state (Task 5)
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Raw table toggle
  const [showRawTable, setShowRawTable] = useState(false);

  const searchInputRef = useRef(null);

  // Authentication check on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch('/api/auth/me', { credentials: 'include' });
        if (!res.ok) {
          localStorage.removeItem('currentUser');
          navigate('/login', {
            state: { message: 'Authentication required. Please sign in to continue.' },
          });
          return;
        }
        const data = await res.json();
        setUser(data.data);
      } catch {
        localStorage.removeItem('currentUser');
        navigate('/login', {
          state: { message: 'Authentication required. Please sign in to continue.' },
        });
      }
    };

    checkAuth();
  }, [navigate]);

  // Fetch research history
  const fetchResearchHistory = useCallback(async () => {
    setLoadingHistory(true);
    setHistoryError(null);
    try {
      const res = await fetch('/api/research/history', { credentials: 'include' });
      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Session expired. Please sign in again.' } });
        return;
      }
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to fetch research history.');
      }
      const data = await res.json();
      setResearchHistory(data.data || []);
    } catch (err) {
      setHistoryError(err.message || 'Could not load research history.');
    } finally {
      setLoadingHistory(false);
    }
  }, [navigate]);

  // Fetch watchlist
  const fetchWatchlist = useCallback(async () => {
    setLoadingWatchlist(true);
    setWatchlistError(null);
    try {
      const res = await fetch('/api/watchlist', { credentials: 'include' });
      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Session expired. Please sign in again.' } });
        return;
      }
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to fetch watchlist.');
      }
      const data = await res.json();
      setWatchlist(data.data || []);
    } catch (err) {
      setWatchlistError(err.message || 'Could not load saved stocks.');
    } finally {
      setLoadingWatchlist(false);
    }
  }, [navigate]);

  // Add stock to watchlist
  const handleAddToWatchlist = async (tickerToAdd = ticker) => {
    const clean = tickerToAdd.trim().toUpperCase();
    if (!clean) return;

    setAddingWatchlist(true);
    setWatchlistError(null);
    setWatchlistSuccess(null);

    try {
      const res = await fetch('/api/watchlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ticker: clean }),
      });

      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Your session has expired. Please log in again.' } });
        return;
      }

      const data = await res.json();

      if (res.status === 409) {
        setWatchlistError(data.detail || `Stock '${clean}' is already in your watchlist.`);
        return;
      }

      if (!res.ok) {
        throw new Error(data.detail || `Failed to add ${clean} to watchlist.`);
      }

      setWatchlistSuccess(`'${clean}' successfully added to your watchlist!`);
      setIsSearchOpen(false);
      fetchWatchlist();
    } catch (err) {
      setWatchlistError(err.message || 'Failed to save stock to watchlist.');
    } finally {
      setAddingWatchlist(false);
    }
  };

  // Remove stock from watchlist
  const handleRemoveFromWatchlist = async (savedStockId, tickerName) => {
    setWatchlistError(null);
    setWatchlistSuccess(null);

    try {
      const res = await fetch(`/api/watchlist/${savedStockId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Your session has expired. Please log in again.' } });
        return;
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Failed to remove ${tickerName}.`);
      }

      setWatchlistSuccess(`'${tickerName}' removed from your watchlist.`);
      fetchWatchlist();
    } catch (err) {
      setWatchlistError(err.message || 'Failed to remove stock.');
    }
  };

  // Debounced Live Search (Task 5)
  useEffect(() => {
    const cleanQuery = ticker.trim();
    if (cleanQuery.length < 2) {
      setSearchResults([]);
      setIsSearchOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(`/api/stocks/search?q=${encodeURIComponent(cleanQuery)}`, {
          credentials: 'include',
        });
        if (res.ok) {
          const json = await res.json();
          setSearchResults(json.results || []);
          setIsSearchOpen(true);
        }
      } catch {
        // Silently ignore network failures
      } finally {
        setSearching(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [ticker]);

  // ── User Preferences Functions (Task 6) ───────────────────────────────────
  // Fetch user preferences from PostgreSQL
  const fetchPreferences = useCallback(async () => {
    setLoadingPreferences(true);
    setPreferenceError(null);
    try {
      const res = await fetch('/api/preferences', { credentials: 'include' });
      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Session expired. Please sign in again.' } });
        return null;
      }
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to load user preferences.');
      }
      const data = await res.json();
      if (data.market) setMarket(data.market);
      if (data.analysis_period) setPeriod(data.analysis_period);
      if (data.preference_id) setPreferenceId(data.preference_id);
      if (data.updated_at) setPreferenceUpdatedAt(data.updated_at);
      return data;
    } catch (err) {
      setPreferenceError(err.message || 'Could not load preferences.');
      return null;
    } finally {
      setLoadingPreferences(false);
    }
  }, [navigate]);

  // Save / Update user preferences in PostgreSQL
  const handleSavePreferences = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setSavingPreferences(true);
    setPreferenceError(null);
    setPreferenceSuccess(null);
    try {
      const res = await fetch('/api/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          market,
          analysis_period: period,
        }),
      });

      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Session expired. Please sign in again.' } });
        return;
      }

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to save preferences.');
      }

      setMarket(data.market);
      setPeriod(data.analysis_period);
      setPreferenceId(data.preference_id);
      setPreferenceUpdatedAt(data.updated_at);
      setPreferenceSuccess(
        `Preferences saved: Default Market is ${data.market} and Analysis Period is ${data.analysis_period}.`
      );
    } catch (err) {
      setPreferenceError(err.message || 'Failed to save preferences.');
    } finally {
      setSavingPreferences(false);
    }
  };

  // Load stored report data from an existing task without executing a new research run
  const loadTaskReport = async (taskId) => {
    try {
      const res = await fetch(`/api/research/tasks/${taskId}`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        if (data.report) {
          setOverview(data.report.overview_data);
          setHistory(data.report.history_data);
          if (data.task?.ticker) setTicker(data.task.ticker);
          if (data.task?.market) setMarket(data.task.market);
          if (data.task?.requested_period) setPeriod(data.task.requested_period);
        }
      }
    } catch {
      // Non-fatal
    }
  };

  // Execute research task and record to database with market and analysis period
  const runResearch = async (
    symbolToRun = ticker,
    periodToRun = period,
    marketToRun = market
  ) => {
    const cleanSymbol = symbolToRun.trim().toUpperCase();
    if (!cleanSymbol) return;

    setIsSearchOpen(false);
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/research/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ticker: cleanSymbol,
          period: periodToRun,
          market: marketToRun,
        }),
      });

      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Your session has expired. Please log in again.' } });
        return;
      }

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || `Failed to execute research for ${cleanSymbol}`);
      }

      if (data.report) {
        setOverview(data.report.overview_data);
        setHistory(data.report.history_data);
      }

      fetchResearchHistory();
    } catch (err) {
      setError(err.message || 'An error occurred while executing research task.');
      fetchResearchHistory();
    } finally {
      setLoading(false);
    }
  };

  // Initial load: fetch saved preferences, watchlist, and history
  // Does not trigger arbitrary auto-research, respecting user preference and existing reports
  useEffect(() => {
    const initWorkspace = async () => {
      // 1. Fetch user saved preferences from PostgreSQL
      await fetchPreferences();

      // 2. Fetch watchlist
      fetchWatchlist();

      // 3. Fetch research history and restore latest completed report without triggering arbitrary new research
      try {
        const res = await fetch('/api/research/history', { credentials: 'include' });
        if (res.ok) {
          const json = await res.json();
          const items = json.data || [];
          setResearchHistory(items);
          const lastCompleted = items.find((t) => t.status === 'Completed');
          if (lastCompleted) {
            await loadTaskReport(lastCompleted.task_id);
          }
        }
      } catch {
        fetchResearchHistory();
      }
    };

    initWorkspace();
  }, [fetchPreferences, fetchWatchlist, fetchResearchHistory]);

  const handleQuickTicker = (sym) => {
    let targetMarket = market;
    if (sym.endsWith('.NS')) targetMarket = 'NSE';
    else if (sym.endsWith('.BO')) targetMarket = 'BSE';
    else if (['AAPL', 'MSFT', 'NVDA'].includes(sym)) targetMarket = 'NASDAQ';

    setTicker(sym);
    setMarket(targetMarket);
    runResearch(sym, period, targetMarket);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    runResearch(ticker, period, market);
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    } catch {
      // Ignore network errors
    } finally {
      localStorage.removeItem('currentUser');
      navigate('/login', { state: { message: 'You have been successfully logged out.' } });
    }
  };

  const isPriceUp = overview?.current_price >= overview?.previous_close;
  const priceChange = overview?.previous_close ? ((overview.current_price - overview.previous_close) / overview.previous_close) * 100 : 0;
  const recentCloses = useMemo(() => (history?.candles || []).slice(-15).map((c) => c.close), [history]);
  const recentVolumes = useMemo(() => (history?.candles || []).slice(-15).map((c) => c.volume), [history]);

  return (
    <div className="min-h-screen bg-[#050507] text-zinc-100 flex flex-col md:flex-row antialiased selection:bg-rose-600/30 selection:text-rose-200">
      {/* ── Persistent Left Sidebar ── */}
      <aside className="w-full md:w-64 lg:w-72 bg-[#09090d] border-r border-white/[0.07] flex flex-col justify-between shrink-0 md:sticky md:top-0 md:h-screen z-30">
        <div>
          {/* Brand Logo Header */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-white/[0.06]">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-rose-600 via-red-600 to-rose-700 text-white font-bold shadow-crimson-sm shrink-0">
              <TrendingUp className="h-5 w-5" />
            </div>
            <div className="flex flex-col min-w-0">
              <span className="text-base font-extrabold tracking-tight text-white font-sans uppercase">
                SAI ANALYSIS
              </span>
              <span className="text-[9px] font-mono font-medium text-rose-400 uppercase tracking-wider truncate">
                Stock Research AI
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1 text-xs">
            <a
              href="#dashboard-overview"
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-rose-950/70 via-red-950/30 to-transparent border-l-2 border-rose-500 text-white font-semibold shadow-sm transition-all"
            >
              <div className="flex items-center gap-2.5">
                <LayoutDashboard className="h-4 w-4 text-rose-500" />
                <span>Dashboard</span>
              </div>
              <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
            </a>

            <a
              href="#stock-controller"
              className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.03] transition-all font-medium"
            >
              <Search className="h-4 w-4" />
              <span>Stock Search</span>
            </a>

            <a
              href="#preferences-section"
              className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.03] transition-all font-medium"
            >
              <Sliders className="h-4 w-4" />
              <span>User Preferences</span>
            </a>

            <a
              href="#chart-section"
              className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.03] transition-all font-medium"
            >
              <BarChart2 className="h-4 w-4" />
              <span>Performance Chart</span>
            </a>

            <a
              href="#watchlist-section"
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.03] transition-all font-medium"
            >
              <div className="flex items-center gap-2.5">
                <Bookmark className="h-4 w-4" />
                <span>Watchlist</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.05] text-zinc-300 border border-white/[0.08]">
                {watchlist.length}
              </span>
            </a>

            <a
              href="#history-section"
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-zinc-400 hover:text-white hover:bg-white/[0.03] transition-all font-medium"
            >
              <div className="flex items-center gap-2.5">
                <History className="h-4 w-4" />
                <span>Research History</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.05] text-zinc-300 border border-white/[0.08]">
                {researchHistory.length}
              </span>
            </a>
          </nav>
        </div>

        {/* Sidebar Footer Area */}
        <div className="p-4 border-t border-white/[0.06] space-y-3">
          {/* Engine Health Card */}
          <div className="p-3.5 rounded-xl border border-white/[0.08] bg-[#120f16]/90 relative overflow-hidden">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Cpu className="h-3.5 w-3.5 text-rose-500" />
                Stock Engine
              </span>
              <span className="text-[9px] font-mono text-emerald-400 font-semibold uppercase">Active</span>
            </div>
            <p className="text-[11px] text-zinc-400 leading-snug">
              Milestone 1 • Fast multi-agent analytics & validation pipeline.
            </p>
            <div className="mt-2.5 flex items-center gap-1.5 text-[10px] text-zinc-400 font-mono">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              PostgreSQL Connected
            </div>
          </div>

          {/* User Profile Pill */}
          <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/[0.06]">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-bold font-mono shrink-0">
                {user.full_name?.charAt(0) || 'U'}
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-white truncate leading-tight">
                  {user.full_name || 'Mathew Andersson'}
                </p>
                <p className="text-[10px] text-zinc-400 font-mono truncate">
                  {user.email || 'user@example.com'}
                </p>
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="p-1.5 text-zinc-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Ambient Top Crimson Glow */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-[400px] w-full max-w-6xl bg-gradient-to-b from-rose-600/15 via-red-600/5 to-transparent blur-3xl opacity-75"
        />

        {/* ── Top Header Bar ── */}
        <header className="sticky top-0 z-20 border-b border-white/[0.07] bg-[#050507]/90 backdrop-blur-xl px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
              Welcome back, <span className="text-white">{user.full_name?.split(' ')[0] || 'Analyst'}</span>
            </h1>
            <p className="text-xs text-zinc-400 mt-0.5">
              Multi-Agent Stock Research & Market Intelligence
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick Header Search input */}
            <div className="relative w-48 sm:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
              <input
                type="text"
                value={ticker}
                onChange={(e) => {
                  setTicker(e.target.value);
                  setIsSearchOpen(true);
                }}
                placeholder="Search stocks, tickers..."
                className="w-full rounded-xl border border-white/[0.09] bg-[#0a0a0f] pl-8 pr-3 py-1.5 text-xs text-zinc-200 placeholder-zinc-500 outline-none focus:border-rose-500/70"
              />
            </div>

            {/* Notification Bell */}
            <button
              type="button"
              className="p-2 rounded-xl border border-white/[0.08] bg-white/[0.02] text-zinc-400 hover:text-white hover:bg-white/[0.06] transition-colors relative"
              title="Notifications"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-1.5 w-1.5 rounded-full bg-rose-500" />
            </button>

            {/* New Research Action Trigger */}
            <button
              type="button"
              onClick={() => {
                if (searchInputRef.current) {
                  searchInputRef.current.focus();
                }
              }}
              className="btn-primary py-1.5 px-3.5 text-xs flex items-center gap-1.5 shadow-sm shadow-rose-950"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Research</span>
            </button>
          </div>
        </header>

        {/* ── Main Dashboard Workspace ── */}
        <main className="p-6 lg:p-8 space-y-6 flex-1 max-w-7xl mx-auto w-full relative z-10">
          {/* ── Section: Stock Search Controller Card ── */}
          <section id="stock-controller" className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 relative z-20">
            <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-3.5 items-center">
              <div className="relative flex-1 w-full">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-rose-500" />
                <input
                  ref={searchInputRef}
                  type="text"
                  value={ticker}
                  onChange={(e) => {
                    setTicker(e.target.value);
                    setIsSearchOpen(true);
                  }}
                  onFocus={() => {
                    if (searchResults.length > 0) setIsSearchOpen(true);
                  }}
                  placeholder="Search by company name or stock ticker (e.g. Infosys, TCS, Apple, INFY.NS)…"
                  className="input-base pl-12 uppercase font-mono tracking-wider text-sm bg-[#0a0a0f] border-white/[0.1] focus:border-rose-500/80"
                />
                {searching && (
                  <div className="absolute right-4 top-1/2 -translate-y-1/2">
                    <Spinner className="h-4 w-4 text-rose-500" />
                  </div>
                )}

                {/* Autocomplete Dropdown */}
                {isSearchOpen && searchResults.length > 0 && (
                  <div className="absolute left-0 right-0 top-full mt-2 z-50 bg-[#0c0c12]/98 border border-white/[0.12] rounded-xl shadow-2xl shadow-black overflow-hidden backdrop-blur-2xl max-h-72 overflow-y-auto animate-fade-in divide-y divide-white/[0.06]">
                    <div className="px-3.5 py-2 bg-white/[0.03] text-[10px] font-semibold text-zinc-400 uppercase tracking-wider flex items-center justify-between">
                      <span>Matching Companies & Tickers</span>
                      <button
                        type="button"
                        onClick={() => setIsSearchOpen(false)}
                        className="text-zinc-400 hover:text-white"
                      >
                        Close ✕
                      </button>
                    </div>
                    {searchResults.map((item) => (
                      <div
                        key={item.ticker}
                        onClick={() => {
                          setTicker(item.ticker);
                          setIsSearchOpen(false);
                        }}
                        className="p-3 hover:bg-white/[0.04] cursor-pointer flex items-center justify-between gap-3 transition-colors group"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs font-bold text-white bg-white/[0.06] px-2 py-0.5 rounded border border-white/[0.12] group-hover:border-rose-500/50">
                              {item.ticker}
                            </span>
                            <span className="text-[10px] text-rose-400 font-semibold uppercase bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                              {item.exchange}
                            </span>
                          </div>
                          <p className="text-xs text-zinc-200 mt-1 truncate font-medium">
                            {item.company_name}
                          </p>
                        </div>

                        <div className="flex items-center gap-1.5 shrink-0" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            onClick={() => {
                              setTicker(item.ticker);
                              handleAddToWatchlist(item.ticker);
                            }}
                            className="btn-secondary p-1.5 text-zinc-400 hover:text-rose-400"
                            title={`Add ${item.ticker} to Watchlist`}
                          >
                            <Bookmark className="h-3.5 w-3.5" />
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              setTicker(item.ticker);
                              let itemMarket = market;
                              if (item.exchange === 'NSE') itemMarket = 'NSE';
                              else if (item.exchange === 'BSE') itemMarket = 'BSE';
                              else if (item.exchange === 'NASDAQ') itemMarket = 'NASDAQ';
                              else if (item.exchange === 'NYSE') itemMarket = 'NYSE';
                              setMarket(itemMarket);
                              runResearch(item.ticker, period, itemMarket);
                            }}
                            className="btn-primary py-1 px-3 text-xs flex items-center gap-1 shadow-sm shadow-rose-950"
                            title={`Research ${item.ticker}`}
                          >
                            <TrendingUp className="h-3 w-3" />
                            <span>Research</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Market Selection Dropdown (Task 6) */}
              <div className="flex items-center gap-1.5 shrink-0">
                <label htmlFor="search-market" className="text-[10px] font-mono uppercase text-zinc-400 hidden sm:inline">
                  Market:
                </label>
                <select
                  id="search-market"
                  value={market}
                  onChange={(e) => setMarket(e.target.value)}
                  className="input-base w-28 py-2.5 cursor-pointer text-xs font-semibold bg-[#0a0a0f] border-white/[0.1] text-zinc-200 focus:border-rose-500/80"
                  title="Target Market Exchange"
                >
                  <option value="NSE">NSE (India)</option>
                  <option value="BSE">BSE (India)</option>
                  <option value="NASDAQ">NASDAQ (US)</option>
                  <option value="NYSE">NYSE (US)</option>
                </select>
              </div>

              {/* Period Select & Buttons (Task 6) */}
              <div className="flex items-center gap-1.5 shrink-0">
                <label htmlFor="search-period" className="text-[10px] font-mono uppercase text-zinc-400 hidden sm:inline">
                  Period:
                </label>
                <select
                  id="search-period"
                  value={period}
                  onChange={(e) => {
                    setPeriod(e.target.value);
                    if (overview) {
                      runResearch(ticker, e.target.value, market);
                    }
                  }}
                  className="input-base w-28 py-2.5 cursor-pointer text-xs font-semibold bg-[#0a0a0f] border-white/[0.1] text-zinc-200 focus:border-rose-500/80"
                  title="Analysis Period"
                >
                  <option value="1mo">1 Month</option>
                  <option value="3mo">3 Months</option>
                  <option value="6mo">6 Months</option>
                  <option value="1y">1 Year</option>
                  <option value="5y">5 Years</option>
                </select>
              </div>

              <div className="flex items-center gap-2 w-full md:w-auto">
                <button
                  type="submit"
                  disabled={loading}
                  className="btn-primary w-full md:w-28 py-2.5 text-xs whitespace-nowrap shadow-sm shadow-rose-950"
                >
                  {loading ? <Spinner className="h-3.5 w-3.5" /> : <Search className="h-3.5 w-3.5" />}
                  <span>{loading ? 'Analyzing…' : 'Research'}</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleAddToWatchlist(ticker)}
                  disabled={addingWatchlist || loading}
                  className="btn-secondary w-full md:w-auto py-2.5 px-3.5 text-xs font-semibold text-zinc-300 hover:text-white whitespace-nowrap"
                  title={`Save ${ticker} to Watchlist`}
                >
                  {addingWatchlist ? <Spinner className="h-3.5 w-3.5" /> : <Bookmark className="h-3.5 w-3.5 text-rose-500" />}
                  <span>Watchlist</span>
                </button>
              </div>
            </form>

            {/* Quick Symbol Pills */}
            <div className="mt-3.5 pt-3 border-t border-white/[0.05] flex flex-wrap items-center gap-2 text-xs">
              <span className="text-zinc-500 text-[11px] font-semibold uppercase tracking-wider">Popular Tickers:</span>
              {QUICK_TICKERS.map((sym) => (
                <button
                  key={sym}
                  type="button"
                  onClick={() => handleQuickTicker(sym)}
                  className={`px-2.5 py-0.5 rounded-lg font-mono text-[11px] transition-all ${
                    ticker === sym
                      ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white font-bold shadow-sm shadow-rose-950'
                      : 'bg-white/[0.03] border border-white/[0.08] text-zinc-400 hover:text-white hover:bg-white/[0.06]'
                  }`}
                >
                  {sym}
                </button>
              ))}
            </div>
          </section>

          {/* Feedback Banners */}
          {watchlistSuccess && (
            <div className="glass-card p-3 border border-emerald-500/30 bg-emerald-950/25 text-emerald-300 text-xs font-semibold flex items-center justify-between rounded-xl">
              <div className="flex items-center gap-2">
                <Check className="h-4 w-4 text-emerald-400" />
                <span>{watchlistSuccess}</span>
              </div>
              <button onClick={() => setWatchlistSuccess(null)} className="text-emerald-400 hover:text-white text-xs font-bold">
                ✕
              </button>
            </div>
          )}

          {watchlistError && <AlertBanner message={watchlistError} variant="error" />}
          {error && <AlertBanner message={error} variant="error" />}

          {/* ── Section: User Preferences (Market & Analysis Period - Task 6) ── */}
          <section
            id="preferences-section"
            className="glass-card p-5 lg:p-6 border border-white/[0.08] bg-[#0d0d13]/90 relative z-10"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-rose-950/70 to-red-950/40 border border-rose-500/30 text-rose-400 shrink-0">
                  <Sliders className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-bold text-white tracking-tight uppercase">
                      User Preferences: Market & Analysis Period
                    </h2>
                    <span className="text-[10px] font-mono font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      PostgreSQL Persisted
                    </span>
                  </div>
                  <p className="text-xs text-zinc-400 mt-0.5">
                    Configure your target exchange and historical timeframe. Stored persistently for{' '}
                    <span className="text-zinc-200 font-mono">{user.email || 'authenticated user'}</span>.
                  </p>
                </div>
              </div>

              {preferenceUpdatedAt && (
                <span className="text-[10px] font-mono text-zinc-500 self-start sm:self-auto">
                  Last Saved: {new Date(preferenceUpdatedAt).toLocaleTimeString()}
                </span>
              )}
            </div>

            {/* Preference Feedback Banners */}
            {preferenceSuccess && (
              <div className="mt-4 glass-card p-3 border border-emerald-500/30 bg-emerald-950/25 text-emerald-300 text-xs font-semibold flex items-center justify-between rounded-xl animate-fade-in">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span>{preferenceSuccess}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setPreferenceSuccess(null)}
                  className="text-emerald-400 hover:text-white text-xs font-bold"
                >
                  ✕
                </button>
              </div>
            )}

            {preferenceError && (
              <div className="mt-4">
                <AlertBanner message={preferenceError} variant="error" />
              </div>
            )}

            {/* Preferences Form Controls */}
            <form onSubmit={handleSavePreferences} className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Market Preference Control */}
              <div className="p-4 rounded-xl border border-white/[0.06] bg-[#0a0a0f] flex flex-col justify-between gap-3">
                <div>
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor="pref-market"
                      className="text-xs font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5"
                    >
                      <Building2 className="h-3.5 w-3.5 text-rose-500" />
                      Market Exchange
                    </label>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold">
                      Current: {market}
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Select target stock exchange for equity research, data validation, and ticker formatting.
                  </p>
                </div>

                <div className="space-y-2">
                  <select
                    id="pref-market"
                    value={market}
                    onChange={(e) => setMarket(e.target.value)}
                    className="input-base w-full py-2.5 text-xs font-semibold bg-[#0d0d14] border-white/[0.1] text-zinc-100 focus:border-rose-500/80 cursor-pointer"
                  >
                    <option value="NSE">NSE — National Stock Exchange of India (.NS)</option>
                    <option value="BSE">BSE — BSE Ltd., India (.BO)</option>
                    <option value="NASDAQ">NASDAQ — US Tech & Global Equities</option>
                    <option value="NYSE">NYSE — New York Stock Exchange</option>
                  </select>
                  <div className="text-[10px] text-zinc-500 font-mono">
                    {market === 'NSE' && '• NSE format: INFY.NS, TCS.NS, RELIANCE.NS'}
                    {market === 'BSE' && '• BSE format: INFY.BO, 500209.BO'}
                    {market === 'NASDAQ' && '• NASDAQ format: AAPL, MSFT, GOOGL, NVDA'}
                    {market === 'NYSE' && '• NYSE format: IBM, KO, JNJ, DIS'}
                  </div>
                </div>
              </div>

              {/* Analysis Period Preference Control */}
              <div className="p-4 rounded-xl border border-white/[0.06] bg-[#0a0a0f] flex flex-col justify-between gap-3">
                <div>
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor="pref-period"
                      className="text-xs font-bold text-zinc-200 uppercase tracking-wider flex items-center gap-1.5"
                    >
                      <Calendar className="h-3.5 w-3.5 text-rose-500" />
                      Analysis Period
                    </label>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-bold">
                      Current: {period}
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-400 mt-1">
                    Default historical duration requested for OHLCV data retrieval and charts.
                  </p>
                </div>

                <div className="space-y-2">
                  <select
                    id="pref-period"
                    value={period}
                    onChange={(e) => setPeriod(e.target.value)}
                    className="input-base w-full py-2.5 text-xs font-semibold bg-[#0d0d14] border-white/[0.1] text-zinc-100 focus:border-rose-500/80 cursor-pointer"
                  >
                    <option value="1mo">1 Month (1mo) — Short-term Momentum</option>
                    <option value="3mo">3 Months (3mo) — Quarterly Outlook</option>
                    <option value="6mo">6 Months (6mo) — Medium-term Trend</option>
                    <option value="1y">1 Year (1y) — Full-Year Cycle</option>
                    <option value="5y">5 Years (5y) — Long-term Structural</option>
                  </select>
                  <div className="text-[10px] text-zinc-500 font-mono">
                    • Validated against provider historical datasets (1mo, 3mo, 6mo, 1y, 5y)
                  </div>
                </div>
              </div>

              {/* Form Action Buttons Bar */}
              <div className="md:col-span-2 flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
                <div className="text-[11px] text-zinc-500 font-mono">
                  Account: <span className="text-zinc-300">{user.email || 'Authenticated'}</span> • Isolated user preferences
                </div>

                <div className="flex items-center gap-2.5 w-full sm:w-auto">
                  <button
                    type="button"
                    onClick={fetchPreferences}
                    disabled={loadingPreferences || savingPreferences}
                    className="btn-secondary py-2 px-4 text-xs font-semibold w-full sm:w-auto"
                  >
                    <RefreshCw
                      className={`h-3.5 w-3.5 ${
                        loadingPreferences ? 'animate-spin text-rose-400' : 'text-zinc-400'
                      }`}
                    />
                    <span>Reset to Saved</span>
                  </button>

                  <button
                    type="submit"
                    disabled={savingPreferences || loadingPreferences}
                    className="btn-primary py-2 px-5 text-xs font-bold w-full sm:w-auto shadow-sm shadow-rose-950 flex items-center justify-center gap-2"
                  >
                    {savingPreferences ? (
                      <>
                        <Spinner className="h-3.5 w-3.5" />
                        <span>Saving Preferences…</span>
                      </>
                    ) : (
                      <>
                        <Check className="h-3.5 w-3.5" />
                        <span>Save Preferences</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>
          </section>

          {/* Loading Indicator */}
          {loading && (
            <div className="flex items-center justify-center p-12 glass-card border border-white/[0.08] bg-[#0d0d13]/90">
              <div className="flex flex-col items-center gap-3">
                <Spinner className="h-8 w-8 text-rose-500" />
                <p className="text-xs font-mono text-zinc-300">
                  Executing research pipeline for {ticker} ({market}, {period})…
                </p>
              </div>
            </div>
          )}

          {/* ── Ready / Empty State when no stock overview is loaded yet ── */}
          {!loading && !overview && (
            <div className="glass-card p-8 border border-white/[0.08] bg-[#0d0d13]/90 text-center animate-fade-in space-y-5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-950/80 to-red-950/40 border border-rose-500/30 text-rose-400 shadow-crimson-sm mx-auto">
                <TrendingUp className="h-6 w-6 text-rose-400" />
              </div>
              <div className="max-w-md mx-auto space-y-2">
                <h3 className="text-base font-bold text-white tracking-tight">
                  Ready for Stock Research & Market Intelligence
                </h3>
                <p className="text-xs text-zinc-400 leading-relaxed">
                  Default exchange set to <strong className="text-white font-mono">{market}</strong> with a{' '}
                  <strong className="text-white font-mono">{period}</strong> analysis period. Select a market below or search a stock above to initiate research.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-2xl mx-auto pt-2">
                {[
                  { code: 'NSE', name: 'National Stock Exchange', sample: 'INFY.NS' },
                  { code: 'BSE', name: 'Bombay Stock Exchange', sample: 'INFY.BO' },
                  { code: 'NASDAQ', name: 'NASDAQ Stock Market', sample: 'AAPL' },
                  { code: 'NYSE', name: 'New York Stock Exchange', sample: 'IBM' },
                ].map((m) => (
                  <div
                    key={m.code}
                    onClick={() => {
                      setMarket(m.code);
                      setTicker(m.sample);
                    }}
                    className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                      market === m.code
                        ? 'border-rose-500/60 bg-rose-950/20 shadow-sm shadow-rose-950/40'
                        : 'border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.04]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-white">{m.code}</span>
                      {market === m.code && <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />}
                    </div>
                    <p className="text-[10px] text-zinc-400 mt-1 truncate">{m.name}</p>
                    <p className="text-[9px] font-mono text-zinc-500 mt-0.5">{m.sample}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Active Stock Bento Financial Overview (Row 1: 4 Cards with Real Sparklines) ── */}
          {!loading && overview && (
            <div id="dashboard-overview" className="space-y-6 animate-fade-in">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Bento Card 1: Active Price & Change */}
                <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                        {overview.ticker} • {overview.exchange}
                      </span>
                      <h4 className="text-xs font-medium text-zinc-300 truncate max-w-[150px]">
                        {overview.company_name}
                      </h4>
                    </div>
                    {isPriceUp ? (
                      <span className="inline-flex items-center gap-0.5 text-xs font-mono font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                        <ArrowUpRight className="h-3 w-3" />+{priceChange.toFixed(2)}%
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-0.5 text-xs font-mono font-bold text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-800/40">
                        <ArrowDownRight className="h-3 w-3" />{priceChange.toFixed(2)}%
                      </span>
                    )}
                  </div>

                  <div className="mt-4 flex items-end justify-between">
                    <div>
                      <div className="text-2xl lg:text-3xl font-extrabold font-mono text-white tracking-tight">
                        {overview.currency === 'INR' ? '₹' : '$'}
                        {overview.current_price?.toLocaleString() || 'N/A'}
                      </div>
                      <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
                        Prev: {overview.currency === 'INR' ? '₹' : '$'}{overview.previous_close || 'N/A'}
                      </p>
                    </div>

                    <Sparkline data={recentCloses} height={36} width={90} color={isPriceUp ? '#34d399' : '#f43f5e'} />
                  </div>
                </div>

                {/* Bento Card 2: Day Range */}
                <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                      Day Trading Range
                    </span>
                    <span className="text-[10px] font-mono text-zinc-500">Intraday</span>
                  </div>

                  <div className="mt-4 flex items-end justify-between">
                    <div>
                      <div className="text-base font-mono font-bold text-white tracking-tight">
                        {overview.day_low || 'N/A'} — {overview.day_high || 'N/A'}
                      </div>
                      <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
                        Currency: {overview.currency}
                      </p>
                    </div>

                    <Sparkline data={recentCloses} height={36} width={85} color="#f43f5e" />
                  </div>
                </div>

                {/* Bento Card 3: 52-Week Range & Position */}
                <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                      52-Week Range
                    </span>
                    <span className="text-[10px] font-mono text-rose-400">Annual</span>
                  </div>

                  <div className="mt-4">
                    <div className="text-base font-mono font-bold text-white tracking-tight">
                      {overview.fifty_two_week_low || 'N/A'} — {overview.fifty_two_week_high || 'N/A'}
                    </div>

                    {/* 52-Week Position Bar */}
                    {overview.fifty_two_week_low && overview.fifty_two_week_high && overview.current_price && (
                      <div className="mt-2.5">
                        <div className="h-1.5 w-full rounded-full bg-white/[0.08] overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-red-600 via-rose-500 to-emerald-400 rounded-full"
                            style={{
                              width: `${Math.min(
                                Math.max(
                                  ((overview.current_price - overview.fifty_two_week_low) /
                                    (overview.fifty_two_week_high - overview.fifty_two_week_low)) *
                                    100,
                                  5
                                ),
                                100
                              )}%`,
                            }}
                          />
                        </div>
                        <div className="flex justify-between text-[9px] font-mono text-zinc-500 mt-1">
                          <span>Low: {overview.fifty_two_week_low}</span>
                          <span>High: {overview.fifty_two_week_high}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Bento Card 4: Valuation & Volume */}
                <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                      P/E Ratio & Volume
                    </span>
                    <span className="text-[10px] font-mono font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                      P/E: {overview.pe_ratio || 'N/A'}
                    </span>
                  </div>

                  <div className="mt-4 flex items-end justify-between">
                    <div>
                      <div className="text-lg lg:text-xl font-mono font-extrabold text-white">
                        {overview.volume ? overview.volume.toLocaleString() : 'N/A'}
                      </div>
                      <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
                        Shares Traded
                      </p>
                    </div>

                    <Sparkline data={recentVolumes} height={36} width={85} color="#fb7185" />
                  </div>
                </div>
              </div>

              {/* ── Row 2: Major Visual Bento Grid (Stock Chart + Pipeline Health) ── */}
              <div id="chart-section" className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left 8 cols: Large Interactive Stock Performance Chart */}
                <div className="lg:col-span-8">
                  {history?.candles && (
                    <StockPerformanceChart
                      history={history}
                      period={period}
                      onPeriodChange={(newPeriod) => {
                        setPeriod(newPeriod);
                        runResearch(ticker, newPeriod, market);
                      }}
                      currency={overview.currency}
                    />
                  )}
                </div>

                {/* Right 4 cols: Pipeline Health & Telemetry Donut */}
                <div className="lg:col-span-4">
                  {history?.validation && (
                    <TelemetryHealthPanel validation={history.validation} overview={overview} />
                  )}
                </div>
              </div>

              {/* ── Collapsible Verified OHLCV Records Table ── */}
              {history?.candles && history.candles.length > 0 && (
                <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                        Verified OHLCV Trading Records
                      </h4>
                      <p className="text-[11px] text-zinc-400 mt-0.5">
                        {history.candles.length} verified market days stored for this session
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={() => setShowRawTable(!showRawTable)}
                      className="btn-secondary py-1 px-3 text-xs flex items-center gap-1.5"
                    >
                      <span>{showRawTable ? 'Hide Table' : 'Show Trading Days'}</span>
                      {showRawTable ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                    </button>
                  </div>

                  {showRawTable && (
                    <div className="mt-4 overflow-x-auto max-h-64 rounded-xl border border-white/[0.08] animate-fade-in">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-white/[0.03] text-zinc-400 sticky top-0 uppercase tracking-wider text-[10px] border-b border-white/[0.08]">
                          <tr>
                            <th className="py-2.5 px-3">Date</th>
                            <th className="py-2.5 px-3">Open</th>
                            <th className="py-2.5 px-3">High</th>
                            <th className="py-2.5 px-3">Low</th>
                            <th className="py-2.5 px-3">Close</th>
                            <th className="py-2.5 px-3">Volume</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/[0.04] bg-[#0b0b10] text-zinc-200">
                          {history.candles.slice(-20).reverse().map((candle) => {
                            const isGreen = candle.close >= candle.open;
                            return (
                              <tr key={candle.date} className="hover:bg-white/[0.02]">
                                <td className="py-2 px-3 font-semibold text-zinc-300">{candle.date}</td>
                                <td className="py-2 px-3">{candle.open.toFixed(2)}</td>
                                <td className="py-2 px-3 text-emerald-400">{candle.high.toFixed(2)}</td>
                                <td className="py-2 px-3 text-rose-400">{candle.low.toFixed(2)}</td>
                                <td className={`py-2 px-3 font-bold ${isGreen ? 'text-emerald-400' : 'text-rose-400'}`}>
                                  {candle.close.toFixed(2)}
                                </td>
                                <td className="py-2 px-3 text-zinc-400">{candle.volume.toLocaleString()}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* ── Business Profile Summary ── */}
              {overview.business_summary && (
                <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90">
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-1.5">
                    Company Operations & Business Summary
                  </h4>
                  <p className="text-xs text-zinc-300 leading-relaxed max-h-36 overflow-y-auto">
                    {overview.business_summary}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ── Row 3: Dual Intelligence Workspace (History + Watchlist) ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left Column: Research Activity History */}
            <section id="history-section" className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col gap-4">
              <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.06]">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-400">
                    <History className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-white tracking-tight">
                        Recent Research Tasks
                      </h3>
                      <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                        {researchHistory.length}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-400">
                      Executed tasks persisted for <span className="text-zinc-200 font-mono">{user.email}</span>
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={fetchResearchHistory}
                  disabled={loadingHistory}
                  className="btn-secondary py-1 px-2.5 text-[11px]"
                  title="Refresh history"
                >
                  <RefreshCw className={`h-3 w-3 ${loadingHistory ? 'animate-spin text-rose-400' : 'text-zinc-400'}`} />
                  <span className="hidden sm:inline">Refresh</span>
                </button>
              </div>

              {historyError && <AlertBanner message={historyError} variant="error" />}

              {/* Loading */}
              {loadingHistory && researchHistory.length === 0 && (
                <div className="flex items-center justify-center py-10">
                  <div className="flex flex-col items-center gap-2">
                    <Spinner className="h-5 w-5 text-rose-500" />
                    <span className="text-xs text-zinc-400">Loading research history…</span>
                  </div>
                </div>
              )}

              {/* Empty */}
              {!loadingHistory && researchHistory.length === 0 && (
                <div className="text-center py-8 px-4 border border-dashed border-white/[0.08] rounded-xl bg-white/[0.01]">
                  <History className="h-7 w-7 text-zinc-600 mx-auto mb-2 opacity-50" />
                  <h4 className="text-xs font-semibold text-zinc-300">No Research Tasks Yet</h4>
                  <p className="text-[11px] text-zinc-500 mt-0.5 max-w-xs mx-auto">
                    Search for any ticker above and click <strong>"Research"</strong> to run your first analysis.
                  </p>
                </div>
              )}

              {/* Activity List */}
              {researchHistory.length > 0 && (
                <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                  {researchHistory.map((taskItem) => {
                    const isCompleted = taskItem.status === 'Completed';
                    const isFailed = taskItem.status === 'Failed';

                    return (
                      <div
                        key={taskItem.task_id}
                        className="p-3 rounded-xl border border-white/[0.06] bg-[#0c0c12]/80 hover:bg-white/[0.02] transition-colors flex items-center justify-between gap-3 group"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {/* Status Icon */}
                          <div className="shrink-0">
                            {isCompleted ? (
                              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-950/50 border border-emerald-800/50 text-emerald-400">
                                <CheckCircle2 className="h-3.5 w-3.5" />
                              </div>
                            ) : isFailed ? (
                              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-950/50 border border-rose-800/50 text-rose-400">
                                <AlertCircle className="h-3.5 w-3.5" />
                              </div>
                            ) : (
                              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-950/50 border border-amber-800/50 text-amber-400">
                                <Clock className="h-3.5 w-3.5" />
                              </div>
                            )}
                          </div>

                          <div className="min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs font-bold text-white bg-white/[0.06] px-2 py-0.5 rounded border border-white/[0.1]">
                                {taskItem.ticker}
                              </span>
                              <span className="text-[10px] font-mono text-zinc-400 hidden sm:inline">
                                {taskItem.market} • {taskItem.requested_period}
                              </span>
                            </div>
                            <p className="text-xs text-zinc-300 font-medium truncate mt-0.5" title={taskItem.company_name}>
                              {taskItem.company_name || taskItem.ticker}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          <span className="text-[10px] text-zinc-500 font-mono hidden md:inline">
                            {new Date(taskItem.created_at).toLocaleDateString()}
                          </span>

                          {isCompleted ? (
                            <button
                              type="button"
                              onClick={() => setSelectedReportTaskId(taskItem.task_id)}
                              className="btn-primary py-1 px-2.5 text-[11px] shadow-sm shadow-rose-950"
                            >
                              Report
                            </button>
                          ) : (
                            <span className="text-[10px] font-mono text-zinc-500">
                              {taskItem.status}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            {/* Right Column: Watchlist */}
            <div id="watchlist-section">
              <WatchlistSection
                watchlist={watchlist}
                loading={loadingWatchlist}
                error={watchlistError}
                onRefresh={fetchWatchlist}
                onResearch={(sym) => {
                  let targetM = market;
                  if (sym.endsWith('.NS')) targetM = 'NSE';
                  else if (sym.endsWith('.BO')) targetM = 'BSE';
                  else if (market === 'NSE' || market === 'BSE') targetM = 'NASDAQ';
                  setTicker(sym);
                  setMarket(targetM);
                  runResearch(sym, period, targetM);
                }}
                onRemove={handleRemoveFromWatchlist}
                actionLoadingId={loading ? ticker : null}
              />
            </div>
          </div>
        </main>

        {/* ── Modal: Research Report Detail ── */}
        {selectedReportTaskId && (
          <ReportModal
            taskId={selectedReportTaskId}
            onClose={() => setSelectedReportTaskId(null)}
            onLoadStock={(t, p, m) => {
              setTicker(t);
              setPeriod(p);
              const targetM = m || market;
              setMarket(targetM);
              runResearch(t, p, targetM);
            }}
          />
        )}

        {/* Minimal Footer */}
        <footer className="border-t border-white/[0.06] bg-[#050507] py-4 px-6 text-center text-xs text-zinc-600 font-mono">
          © {new Date().getFullYear()} SAI ANALYSIS • Multi-Agent Stock Research & Market Intelligence
        </footer>
      </div>
    </div>
  );
}
