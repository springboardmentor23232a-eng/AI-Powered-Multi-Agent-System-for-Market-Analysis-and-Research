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
import ReportModal from '../components/research/ReportModal';
import { normalizeCandles } from '../components/market/chartHelpers';
import UserPreferencesModal from '../components/terminal/UserPreferencesModal';
import TerminalSidebar from '../components/terminal/TerminalSidebar';
import TerminalCommandBar from '../components/terminal/TerminalCommandBar';
import WorkspaceViewSwitcher from '../components/terminal/WorkspaceViewSwitcher';

const KNOWN_NYSE_TICKERS = new Set([
  'IBM', 'JPM', 'DIS', 'KO', 'WMT', 'GE', 'BRK.A', 'BRK.B',
  'V', 'UNH', 'XOM', 'CVX', 'PG', 'MA', 'HD', 'BAC', 'PFE', 'ABBV'
]);

const getMarketFromItem = (item) => {
  if (!item) return 'NASDAQ';
  if (item.market && ['NSE', 'BSE', 'NASDAQ', 'NYSE'].includes(item.market.toUpperCase())) {
    return item.market.toUpperCase();
  }
  const sym = (item.ticker || '').toUpperCase();
  if (sym.endsWith('.NS')) return 'NSE';
  if (sym.endsWith('.BO')) return 'BSE';
  const exch = (item.exchange || '').toUpperCase();
  if (exch === 'NSE' || exch === 'NSI') return 'NSE';
  if (exch === 'BSE' || exch === 'BOM') return 'BSE';
  if (exch === 'NYSE' || exch === 'NYQ' || KNOWN_NYSE_TICKERS.has(sym)) return 'NYSE';
  return 'NASDAQ';
};









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

  // Search query (strictly empty initially, never auto-filled with TCS.NS)
  const [searchQuery, setSearchQuery] = useState('');

  // Authoritative selected stock: { ticker, company_name, exchange, market, currency }
  const [selectedStock, setSelectedStock] = useState(null);

  // Active analyzed stock: { ticker, company_name, market }
  const [activeStock, setActiveStock] = useState(null);

  const [market, setMarket] = useState('NSE');
  const [period, setPeriod] = useState('1mo');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // User preferences state (Task 6)
  const [preferenceUpdatedAt, setPreferenceUpdatedAt] = useState(null);
  const [preferenceId, setPreferenceId] = useState(null);
  const [loadingPreferences, setLoadingPreferences] = useState(false);
  const [savingPreferences, setSavingPreferences] = useState(false);
  const [preferenceSuccess, setPreferenceSuccess] = useState(null);
  const [preferenceError, setPreferenceError] = useState(null);

  const [overview, setOverview] = useState(null);
  const [history, setHistory] = useState(null);
  const [financials, setFinancials] = useState(null);
  const [loadingFinancials, setLoadingFinancials] = useState(false);
  const [financialsError, setFinancialsError] = useState(null);

  // Fundamental Analysis state (Module 3)
  const [fundamental, setFundamental] = useState(null);
  const [loadingFundamental, setLoadingFundamental] = useState(false);
  const [fundamentalError, setFundamentalError] = useState(null);

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

  // Raw table toggle
  const [showRawTable, setShowRawTable] = useState(false);

  // Platform Workspace & AI Agent selection (Categorized Terminal Navigation)
  const [activeWorkspace, setActiveWorkspace] = useState('overview');
  const [isPreferencesOpen, setIsPreferencesOpen] = useState(false);

  const handleSelectWorkspace = useCallback((workspaceId) => {
    setActiveWorkspace(workspaceId);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // In-flight request deduplication and lifecycle refs
  const fetchingAuthRef = useRef(false);
  const fetchingHistoryRef = useRef(false);
  const fetchingWatchlistRef = useRef(false);
  const fetchingPreferencesRef = useRef(false);
  const fetchingFinancialsSymbolRef = useRef(null);
  const fetchingFundamentalSymbolRef = useRef(null);
  const activeReportTaskIdRef = useRef(null);
  const activeResearchSeqRef = useRef(0);
  const pollIntervalRef = useRef(null);

  const activeStockRef = useRef(activeStock);
  const selectedStockRef = useRef(selectedStock);

  useEffect(() => {
    activeStockRef.current = activeStock;
    selectedStockRef.current = selectedStock;
  }, [activeStock, selectedStock]);

  // Authentication check on mount with AbortController and cancellation cleanup
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    const checkAuth = async () => {
      if (fetchingAuthRef.current) return;
      fetchingAuthRef.current = true;
      try {
        const res = await fetch('/api/auth/me', {
          credentials: 'include',
          signal: controller.signal,
        });
        if (!res.ok) {
          if (isMounted) {
            localStorage.removeItem('currentUser');
            navigate('/login', {
              state: { message: 'Authentication required. Please sign in to continue.' },
            });
          }
          return;
        }
        const data = await res.json();
        if (isMounted) {
          setUser(data.data);
        }
      } catch (err) {
        if (err.name !== 'AbortError' && isMounted) {
          localStorage.removeItem('currentUser');
          navigate('/login', {
            state: { message: 'Authentication required. Please sign in to continue.' },
          });
        }
      } finally {
        fetchingAuthRef.current = false;
      }
    };

    checkAuth();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [navigate]);

  // Fetch research history with in-flight deduplication
  const fetchResearchHistory = useCallback(async () => {
    if (fetchingHistoryRef.current) return [];
    fetchingHistoryRef.current = true;
    setLoadingHistory(true);
    setHistoryError(null);
    try {
      const res = await fetch('/api/research/history', { credentials: 'include' });
      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Session expired. Please sign in again.' } });
        return [];
      }
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to fetch research history.');
      }
      const data = await res.json();
      const items = data.data || [];
      setResearchHistory(items);
      return items;
    } catch (err) {
      setHistoryError(err.message || 'Could not load research history.');
      return [];
    } finally {
      setLoadingHistory(false);
      fetchingHistoryRef.current = false;
    }
  }, [navigate]);

  // Fetch watchlist with in-flight deduplication
  const fetchWatchlist = useCallback(async () => {
    if (fetchingWatchlistRef.current) return [];
    fetchingWatchlistRef.current = true;
    setLoadingWatchlist(true);
    setWatchlistError(null);
    try {
      const res = await fetch('/api/watchlist', { credentials: 'include' });
      if (res.status === 401) {
        localStorage.removeItem('currentUser');
        navigate('/login', { state: { message: 'Session expired. Please sign in again.' } });
        return [];
      }
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to fetch watchlist.');
      }
      const data = await res.json();
      const items = data.data || [];
      setWatchlist(items);
      return items;
    } catch (err) {
      setWatchlistError(err.message || 'Could not load saved stocks.');
      return [];
    } finally {
      setLoadingWatchlist(false);
      fetchingWatchlistRef.current = false;
    }
  }, [navigate]);

  // Add stock to watchlist
  const handleAddToWatchlist = async (tickerToAdd) => {
    const clean = (tickerToAdd || selectedStock?.ticker || activeStock?.ticker || searchQuery).trim().toUpperCase();
    if (!clean) {
      setWatchlistError('Please select or search a stock to add to your watchlist.');
      return;
    }

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

      setWatchlistSuccess(`'${data.company_name || clean}' successfully added to your watchlist!`);
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

  // ── User Preferences Functions (Task 6) ───────────────────────────────────
  // Fetch user preferences from PostgreSQL with in-flight deduplication
  const fetchPreferences = useCallback(async () => {
    if (fetchingPreferencesRef.current) return null;
    fetchingPreferencesRef.current = true;
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
      fetchingPreferencesRef.current = false;
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

  // Fetch Financial Statements with deduplication and zero state dependencies (prevents recreation loops)
  const fetchFinancials = useCallback(async (symbol) => {
    const clean = (symbol || activeStockRef.current?.ticker || selectedStockRef.current?.ticker || '').trim().toUpperCase();
    if (!clean || fetchingFinancialsSymbolRef.current === clean) return;
    fetchingFinancialsSymbolRef.current = clean;
    setLoadingFinancials(true);
    setFinancialsError(null);
    try {
      const res = await fetch(`/api/stocks/${encodeURIComponent(clean)}/financials`, {
        credentials: 'include',
      });
      if (res.ok) {
        const json = await res.json();
        setFinancials(json);
      } else {
        const err = await res.json().catch(() => ({}));
        setFinancialsError(err.detail || 'Financial statements unavailable for this symbol.');
      }
    } catch {
      setFinancialsError('Could not load financial statements.');
    } finally {
      setLoadingFinancials(false);
      fetchingFinancialsSymbolRef.current = null;
    }
  }, []);

  // Fetch Fundamental Analysis with deduplication and zero state dependencies (Module 3)
  const fetchFundamental = useCallback(async (symbol) => {
    const clean = (symbol || activeStockRef.current?.ticker || selectedStockRef.current?.ticker || '').trim().toUpperCase();
    if (!clean || fetchingFundamentalSymbolRef.current === clean) return;
    fetchingFundamentalSymbolRef.current = clean;
    setLoadingFundamental(true);
    setFundamentalError(null);
    try {
      const res = await fetch(`/api/stocks/${encodeURIComponent(clean)}/fundamental`, {
        credentials: 'include',
      });
      if (res.ok) {
        const json = await res.json();
        setFundamental(json);
      } else {
        const err = await res.json().catch(() => ({}));
        setFundamentalError(err.detail || 'Fundamental analysis unavailable for this symbol.');
      }
    } catch {
      setFundamentalError('Could not execute fundamental analysis.');
    } finally {
      setLoadingFundamental(false);
      fetchingFundamentalSymbolRef.current = null;
    }
  }, []);

  // Load stored report data from an existing task without executing a new research run
  const loadTaskReport = useCallback(async (taskId) => {
    if (!taskId) return;
    activeReportTaskIdRef.current = taskId;
    try {
      const res = await fetch(`/api/research/tasks/${taskId}`, { credentials: 'include' });
      if (res.ok) {
        // Discard response if another report was requested while this was in flight
        if (activeReportTaskIdRef.current !== taskId) return;
        const data = await res.json();
        if (data.report) {
          const isDatasetReport = data.report.report_content?.type === 'dataset_validation';
          const normalizedCandles = normalizeCandles(data.report.history_data?.candles);

          let reportOverview = data.report.overview_data || {};
          // If dataset report has minimal overview and ticker is present, enrich overview if possible
          if (isDatasetReport && (!reportOverview.current_price || !reportOverview.exchange) && data.task?.ticker) {
            try {
              const ovRes = await fetch(`/api/stocks/${encodeURIComponent(data.task.ticker)}/overview`, { credentials: 'include' });
              if (ovRes.ok) {
                const liveOv = await ovRes.json();
                reportOverview = { ...liveOv, ...reportOverview };
              }
            } catch {
              // Non-fatal fallback
            }
          }

          setOverview(reportOverview);
          setHistory(data.report.history_data ? {
            ...data.report.history_data,
            candles: normalizedCandles,
          } : null);
          if (data.report.report_content?.financial_statements) {
            setFinancials(data.report.report_content.financial_statements);
          } else if (data.task?.ticker) {
            fetchFinancials(data.task.ticker);
          }
          if (data.report.report_content?.fundamental_analysis) {
            setFundamental(data.report.report_content.fundamental_analysis);
          } else if (data.task?.ticker) {
            fetchFundamental(data.task.ticker);
          }
          if (data.task?.market) setMarket(data.task.market);
          if (data.task?.requested_period) setPeriod(data.task.requested_period);
          if (data.task?.ticker) {
            setActiveStock({
              ticker: data.task.ticker,
              company_name: data.task.company_name || data.task.ticker,
              market: data.task.market,
            });
            // Search input remains empty for intentional user queries
          }
        }
      }
    } catch {
      // Non-fatal
    }
  }, [fetchFinancials, fetchFundamental]);

  // ── Research Task Status Polling (Tasks 3, 4 & Bugfix) ────────────────────
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const pollTask = useCallback((taskId) => {
    if (!taskId) return;
    stopPolling();

    let pollAttempts = 0;
    const maxPolls = 30; // 60 seconds maximum polling window at 2000ms

    pollIntervalRef.current = setInterval(async () => {
      pollAttempts++;
      try {
        const res = await fetch(`/api/research/tasks/${taskId}`, { credentials: 'include' });
        if (!res.ok) {
          stopPolling();
          return;
        }
        const data = await res.json();
        const taskStatus = data.task?.status;

        // Requirement 6: Stop polling when task completes or fails
        if (taskStatus === 'Completed') {
          stopPolling();
          if (data.report) {
            const normalizedCandles = normalizeCandles(data.report.history_data?.candles);
            setOverview(data.report.overview_data);
            setHistory(data.report.history_data ? {
              ...data.report.history_data,
              candles: normalizedCandles,
            } : null);
            if (data.report.report_content?.financial_statements) {
              setFinancials(data.report.report_content.financial_statements);
            } else if (data.task?.ticker) {
              fetchFinancials(data.task.ticker);
            }
            if (data.report.report_content?.fundamental_analysis) {
              setFundamental(data.report.report_content.fundamental_analysis);
            } else if (data.task?.ticker) {
              fetchFundamental(data.task.ticker);
            }
          }
          fetchResearchHistory();
        } else if (taskStatus === 'Failed') {
          stopPolling();
          setError(`Research task for ${data.task?.ticker || 'stock'} failed.`);
          fetchResearchHistory();
        }

        if (pollAttempts >= maxPolls) {
          stopPolling();
        }
      } catch {
        stopPolling();
      }
    }, 2000);
  }, [fetchFinancials, fetchFundamental, fetchResearchHistory, stopPolling]);

  // Clean up polling and asynchronous tasks on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  // Execute research task and record to database with market and analysis period
  const runResearch = async (
    symbolToRun,
    periodToRun = period,
    marketToRun = market,
    stockMeta = null
  ) => {
    const cleanSymbol = (symbolToRun || selectedStock?.ticker || searchQuery).trim().toUpperCase();
    if (!cleanSymbol) {
      setError('Please enter or select a stock ticker or company to research.');
      return;
    }

    const currentSeq = ++activeResearchSeqRef.current;
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

      // Check for stale response
      if (currentSeq !== activeResearchSeqRef.current) return;

      const taskStatus = data.task?.status;

      if (taskStatus === 'Pending' || taskStatus === 'Processing') {
        pollTask(data.task.task_id);
      } else if (data.report) {
        const normalizedCandles = normalizeCandles(data.report.history_data?.candles);
        setOverview(data.report.overview_data);
        setHistory(data.report.history_data ? {
          ...data.report.history_data,
          candles: normalizedCandles,
        } : null);
        if (data.report.report_content?.financial_statements) {
          setFinancials(data.report.report_content.financial_statements);
        } else {
          fetchFinancials(cleanSymbol);
        }
        if (data.report.report_content?.fundamental_analysis) {
          setFundamental(data.report.report_content.fundamental_analysis);
        } else {
          fetchFundamental(cleanSymbol);
        }
      }

      const updatedStock = {
        ticker: cleanSymbol,
        company_name: data.task?.company_name || stockMeta?.company_name || cleanSymbol,
        exchange: data.task?.market || marketToRun,
        market: marketToRun,
      };
      setActiveStock(updatedStock);
      setSelectedStock(updatedStock);

      fetchResearchHistory();
    } catch (err) {
      if (currentSeq === activeResearchSeqRef.current) {
        setError(err.message || 'An error occurred while executing research task.');
        fetchResearchHistory();
      }
    } finally {
      if (currentSeq === activeResearchSeqRef.current) {
        setLoading(false);
      }
    }
  };

  // Initial load: fetch saved preferences, watchlist, and history
  // Executes strictly once on mount with cancellation; does not re-run on subsequent state updates
  useEffect(() => {
    let isMounted = true;
    const controller = new AbortController();

    const initWorkspace = async () => {
      try {
        // Parallel non-blocking initial workspace data load
        const [prefRes, watchRes, histRes] = await Promise.allSettled([
          fetch('/api/preferences', { credentials: 'include', signal: controller.signal }),
          fetch('/api/watchlist', { credentials: 'include', signal: controller.signal }),
          fetch('/api/research/history', { credentials: 'include', signal: controller.signal }),
        ]);

        if (!isMounted) return;

        // 1. Process user preferences
        if (prefRes.status === 'fulfilled' && prefRes.value.ok) {
          const prefData = await prefRes.value.json();
          if (isMounted) {
            if (prefData.market) setMarket(prefData.market);
            if (prefData.analysis_period) setPeriod(prefData.analysis_period);
            if (prefData.preference_id) setPreferenceId(prefData.preference_id);
            if (prefData.updated_at) setPreferenceUpdatedAt(prefData.updated_at);
          }
        }

        // 2. Process watchlist
        if (watchRes.status === 'fulfilled' && watchRes.value.ok) {
          const watchData = await watchRes.value.json();
          if (isMounted) {
            setWatchlist(watchData.data || []);
          }
        }

        // 3. Process research history and restore last completed report or poll pending task
        if (histRes.status === 'fulfilled' && histRes.value.ok) {
          const histData = await histRes.value.json();
          const items = histData.data || [];
          if (isMounted) {
            setResearchHistory(items);
            const inProgressTask = items.find((t) => t.status === 'Pending' || t.status === 'Processing');
            if (inProgressTask) {
              pollTask(inProgressTask.task_id);
            } else {
              const lastCompleted = items.find((t) => t.status === 'Completed');
              if (lastCompleted) {
                await loadTaskReport(lastCompleted.task_id);
              }
            }
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          // Ignore
        }
      }
    };

    initWorkspace();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [loadTaskReport, pollTask]);

  const runResearchRef = useRef(runResearch);
  useEffect(() => {
    runResearchRef.current = runResearch;
  });

  const handleStockSelect = useCallback((item) => {
    const targetMarket = getMarketFromItem(item);
    const updatedStock = {
      ticker: item.ticker,
      company_name: item.company_name,
      exchange: item.exchange || targetMarket,
      market: targetMarket,
      currency: item.currency || (targetMarket === 'NSE' || targetMarket === 'BSE' ? 'INR' : 'USD'),
    };
    setSelectedStock(updatedStock);
    setSearchQuery(item.ticker);
    setMarket(targetMarket);
    runResearchRef.current(item.ticker, period, targetMarket, updatedStock);
  }, [period]);

  const handleSelectFromWatchlist = useCallback((sym) => {
    let targetM = market;
    if (sym.endsWith('.NS')) targetM = 'NSE';
    else if (sym.endsWith('.BO')) targetM = 'BSE';
    else if (market === 'NSE' || market === 'BSE') targetM = 'NASDAQ';
    const stockObj = { ticker: sym, company_name: sym, exchange: targetM, market: targetM };
    setSelectedStock(stockObj);
    setSearchQuery(sym);
    setMarket(targetM);
    runResearchRef.current(sym, period, targetM, stockObj);
  }, [market, period]);

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

  const normalizedHistoryCandles = useMemo(() => normalizeCandles(history?.candles), [history?.candles]);

  return (
    <div className="min-h-screen bg-[#050507] text-zinc-100 flex flex-col md:flex-row antialiased selection:bg-rose-600/30 selection:text-rose-200">
      {/* ── Persistent Left Sidebar (Categorized Financial Terminal) ── */}
      <TerminalSidebar
        activeWorkspace={activeWorkspace}
        onSelectWorkspace={handleSelectWorkspace}
        user={user}
        onLogout={handleLogout}
        watchlistCount={watchlist.length}
        historyCount={researchHistory.length}
      />

      {/* ── Main Content Area ── */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Ambient Top Crimson Glow */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 h-[400px] w-full max-w-6xl bg-gradient-to-b from-rose-600/15 via-red-600/5 to-transparent blur-3xl opacity-75"
        />

        {/* ── Universal Omnisearch Command Bar ── */}
        <TerminalCommandBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onSelectStock={handleStockSelect}
          onRunResearch={(sym, p, m, stockObj) => runResearch(sym, p, m, stockObj)}
          selectedStock={selectedStock}
          activeStock={activeStock}
          market={market}
          setMarket={setMarket}
          period={period}
          setPeriod={(newP) => {
            setPeriod(newP);
            const activeSym = overview?.ticker || activeStock?.ticker || selectedStock?.ticker;
            if (activeSym) {
              runResearch(activeSym, newP, market, selectedStock || activeStock);
            }
          }}
          loading={loading}
          onOpenPreferences={() => setIsPreferencesOpen(true)}
          onSelectWorkspace={handleSelectWorkspace}
        />

        {/* ── Dynamic Platform Workspace & AI Agent Viewport ── */}
        <main className="p-4 sm:p-6 lg:p-8 space-y-6 flex-1 max-w-7xl mx-auto w-full relative z-10">
          <WorkspaceViewSwitcher
            activeWorkspace={activeWorkspace}
            onSelectWorkspace={handleSelectWorkspace}
            overview={overview}
            history={history}
            normalizedCandles={normalizedHistoryCandles}
            period={period}
            onPeriodChange={(newP) => {
              setPeriod(newP);
              const activeSym = overview?.ticker || activeStock?.ticker || selectedStock?.ticker;
              if (activeSym) {
                runResearch(activeSym, newP, market, selectedStock || activeStock);
              }
            }}
            activeStock={activeStock}
            selectedStock={selectedStock}
            loading={loading}
            error={error}
            onClearError={() => setError(null)}
            showRawTable={showRawTable}
            setShowRawTable={setShowRawTable}
            fundamental={fundamental}
            loadingFundamental={loadingFundamental}
            fundamentalError={fundamentalError}
            fetchFundamental={fetchFundamental}
            financials={financials}
            loadingFinancials={loadingFinancials}
            financialsError={financialsError}
            fetchFinancials={fetchFinancials}
            watchlist={watchlist}
            loadingWatchlist={loadingWatchlist}
            watchlistError={watchlistError}
            watchlistSuccess={watchlistSuccess}
            addingWatchlist={addingWatchlist}
            onAddToWatchlist={handleAddToWatchlist}
            onRemoveFromWatchlist={handleRemoveFromWatchlist}
            onSelectStockFromWatchlist={handleSelectFromWatchlist}
            actionLoadingId={loading ? (selectedStock?.ticker || activeStock?.ticker) : null}
            researchHistory={researchHistory}
            loadingHistory={loadingHistory}
            historyError={historyError}
            fetchResearchHistory={fetchResearchHistory}
            onSelectReport={(taskId) => setSelectedReportTaskId(taskId)}
            user={user}
            market={market}
            setMarket={setMarket}
            setPeriod={setPeriod}
            preferenceId={preferenceId}
            preferenceUpdatedAt={preferenceUpdatedAt}
            loadingPreferences={loadingPreferences}
            savingPreferences={savingPreferences}
            preferenceSuccess={preferenceSuccess}
            setPreferenceSuccess={setPreferenceSuccess}
            preferenceError={preferenceError}
            onSavePreferences={handleSavePreferences}
            onResetPreferences={fetchPreferences}
          />
        </main>

        {/* ── Overlay Modal: User Preferences (Task 6) ── */}
        <UserPreferencesModal
          isOpen={isPreferencesOpen}
          isModal={true}
          onClose={() => setIsPreferencesOpen(false)}
          market={market}
          setMarket={setMarket}
          period={period}
          setPeriod={setPeriod}
          preferenceId={preferenceId}
          preferenceUpdatedAt={preferenceUpdatedAt}
          loadingPreferences={loadingPreferences}
          savingPreferences={savingPreferences}
          preferenceSuccess={preferenceSuccess}
          setPreferenceSuccess={setPreferenceSuccess}
          preferenceError={preferenceError}
          onSavePreferences={handleSavePreferences}
          onResetPreferences={fetchPreferences}
          userEmail={user.email}
        />

        {/* ── Modal: Research Report Detail ── */}
        {selectedReportTaskId && (
          <ReportModal
            taskId={selectedReportTaskId}
            onClose={() => setSelectedReportTaskId(null)}
            onLoadStock={(t, p, m) => {
              const targetM = m || market;
              const stockObj = { ticker: t, company_name: t, exchange: targetM, market: targetM };
              setSelectedStock(stockObj);
              setSearchQuery(t);
              setPeriod(p);
              setMarket(targetM);
              runResearch(t, p, targetM, stockObj);
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
