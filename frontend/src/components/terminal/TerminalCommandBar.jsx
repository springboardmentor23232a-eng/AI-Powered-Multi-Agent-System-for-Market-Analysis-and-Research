/**
 * TerminalCommandBar.jsx
 * Universal Command Bar & Global Omnisearch for SAI ANALYSIS.
 *
 * Capabilities:
 * - Multi-exchange stock search & real-time autocomplete (NSE, BSE, NASDAQ, NYSE)
 * - Platform workspace navigation (Terminal Overview, Watchlist, Archive)
 * - AI Agent quick-launch routing (Dataset Validation, Fundamental Analysis, Roadmap Agents)
 * - Keyboard navigation (Ctrl+K / Cmd+K focus, Arrow keys, Enter to execute, Escape to dismiss)
 * - Analysis period and market exchange controls
 * - User Preferences modal launcher
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Search,
  Sliders,
  TrendingUp,
  LayoutDashboard,
  Cpu,
  Command,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import {
  getAllPlatformWorkspaces,
  AGENT_REGISTRY,
} from '../../config/agentRegistry';

const QUICK_TICKERS = [
  { ticker: 'INFY.NS', name: 'Infosys Limited', market: 'NSE' },
  { ticker: 'TCS.NS', name: 'Tata Consultancy Services', market: 'NSE' },
  { ticker: 'AAPL', name: 'Apple Inc.', market: 'NASDAQ' },
  { ticker: 'MSFT', name: 'Microsoft Corporation', market: 'NASDAQ' },
  { ticker: 'NVDA', name: 'NVIDIA Corporation', market: 'NASDAQ' },
  { ticker: 'RELIANCE.NS', name: 'Reliance Industries', market: 'NSE' },
];

const PERIODS = ['1d', '5d', '1mo', '6mo', '1y', '5y'];
const MARKETS = ['NSE', 'BSE', 'NASDAQ', 'NYSE'];

export default function TerminalCommandBar({
  searchQuery = '',
  setSearchQuery = () => {},
  onSelectStock = () => {},
  onRunResearch = () => {},
  selectedStock = null,
  activeStock = null,
  market = 'NSE',
  setMarket = () => {},
  period = '1mo',
  setPeriod = () => {},
  loading = false,
  onOpenPreferences = () => {},
  onSelectWorkspace = () => {},
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const searchSeqRef = useRef(0);

  const workspaces = useMemo(() => getAllPlatformWorkspaces(), []);

  // Global Ctrl+K / Cmd+K keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        inputRef.current &&
        !inputRef.current.contains(e.target) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced live stock search API call
  useEffect(() => {
    const cleanQuery = searchQuery.trim();
    if (cleanQuery.length < 2) {
      return;
    }

    const currentSeq = ++searchSeqRef.current;
    const controller = new AbortController();

    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(`/api/stocks/search?q=${encodeURIComponent(cleanQuery)}`, {
          credentials: 'include',
          signal: controller.signal,
        });
        if (res.ok) {
          const json = await res.json();
          if (currentSeq === searchSeqRef.current) {
            setSearchResults(json.results || []);
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          // Ignore cancellation
        }
      } finally {
        if (currentSeq === searchSeqRef.current) {
          setSearching(false);
        }
      }
    }, 250);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [searchQuery]);

  // Filter workspaces & agents based on search query
  const matchingWorkspaces = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return workspaces.filter(
      (w) => w.name.toLowerCase().includes(q) || w.id.toLowerCase().includes(q)
    );
  }, [searchQuery, workspaces]);

  const matchingAgents = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return [];
    return AGENT_REGISTRY.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.shortName.toLowerCase().includes(q) ||
        a.module.toLowerCase().includes(q) ||
        a.capabilities.some((c) => c.toLowerCase().includes(q))
    );
  }, [searchQuery]);

  // Flattened items for keyboard arrow navigation
  const navigableItems = useMemo(() => {
    const items = [];
    matchingWorkspaces.forEach((w) => items.push({ type: 'workspace', data: w }));
    matchingAgents.forEach((a) => items.push({ type: 'agent', data: a }));
    searchResults.forEach((s) => items.push({ type: 'stock', data: s }));
    if (!searchQuery.trim() && searchResults.length === 0) {
      QUICK_TICKERS.forEach((qt) => items.push({ type: 'quick_ticker', data: qt }));
    }
    return items;
  }, [matchingWorkspaces, matchingAgents, searchResults, searchQuery]);

  const handleSelectNavigableItem = useCallback(
    (item) => {
      if (!item) return;
      if (item.type === 'workspace') {
        onSelectWorkspace(item.data.id);
        setIsOpen(false);
      } else if (item.type === 'agent') {
        onSelectWorkspace(item.data.id);
        setIsOpen(false);
      } else if (item.type === 'stock') {
        onSelectStock(item.data);
        setIsOpen(false);
      } else if (item.type === 'quick_ticker') {
        onSelectStock({
          ticker: item.data.ticker,
          company_name: item.data.name,
          exchange: item.data.market,
          market: item.data.market,
        });
        setIsOpen(false);
      }
    },
    [onSelectWorkspace, onSelectStock]
  );

  const handleKeyDown = (e) => {
    if (!isOpen && (e.key === 'ArrowDown' || e.key === 'Enter')) {
      setIsOpen(true);
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, navigableItems.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + navigableItems.length) % Math.max(1, navigableItems.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (navigableItems.length > 0 && navigableItems[selectedIndex]) {
        handleSelectNavigableItem(navigableItems[selectedIndex]);
      } else {
        const cleanInput = searchQuery.trim().toUpperCase();
        if (cleanInput) {
          onRunResearch(cleanInput, period, market);
          setIsOpen(false);
        }
      }
    } else if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    const cleanInput = searchQuery.trim().toUpperCase();
    if (cleanInput) {
      onRunResearch(cleanInput, period, market);
      setIsOpen(false);
    }
  };

  return (
    <div className="relative z-30 select-none">
      {/* ── Top Bar Container ── */}
      <div className="bg-[#0b0b11]/95 border-b border-white/[0.08] backdrop-blur-md px-4 py-2.5 flex flex-col md:flex-row items-center justify-between gap-3 shadow-md">
        {/* Left: Global Command Search Input */}
        <form onSubmit={handleFormSubmit} className="relative flex-1 w-full min-w-0">
          <div className="relative flex items-center">
            <Search className="absolute left-3.5 h-4 w-4 text-rose-500 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => {
                const val = e.target.value;
                setSearchQuery(val);
                setIsOpen(true);
                setSelectedIndex(0);
                if (val.trim().length < 2) {
                  setSearchResults([]);
                  setSearching(false);
                }
              }}
              onFocus={() => setIsOpen(true)}
              onKeyDown={handleKeyDown}
              placeholder="Search stocks (INFY.NS, Apple), or type /workspaces, /agents... (Ctrl+K)"
              className="w-full bg-[#12121a] hover:bg-[#151520] focus:bg-[#151522] border border-white/[0.09] focus:border-rose-500/60 rounded-xl pl-10 pr-24 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none transition-all font-mono"
            />

            <div className="absolute right-2.5 flex items-center gap-1.5 pointer-events-none">
              {searching ? (
                <Spinner className="h-3.5 w-3.5 text-rose-500" />
              ) : (
                <span className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-white/[0.06] border border-white/[0.08] text-[9px] font-mono text-zinc-400">
                  <Command className="h-2.5 w-2.5" /> K
                </span>
              )}
            </div>
          </div>
        </form>

        {/* Right: Analytical Controls & Action Triggers */}
        <div className="flex items-center gap-2 shrink-0 w-full md:w-auto justify-between md:justify-end">
          {/* Market Exchange Selector */}
          <div className="flex items-center gap-1 bg-[#12121a] border border-white/[0.08] rounded-xl px-2 py-1">
            <span className="text-[10px] font-mono uppercase text-zinc-500 hidden sm:inline">Exch</span>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value)}
              className="bg-transparent text-xs font-mono font-semibold text-zinc-200 focus:outline-none cursor-pointer"
            >
              {MARKETS.map((m) => (
                <option key={m} value={m} className="bg-[#12121a] text-zinc-200">
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe Period Selector */}
          <div className="flex items-center gap-0.5 bg-[#12121a] border border-white/[0.08] rounded-xl p-0.5">
            {PERIODS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPeriod(p)}
                className={`px-2 py-1 rounded-lg text-[10px] font-mono font-semibold transition-all ${
                  period === p
                    ? 'bg-rose-600 text-white shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-white/[0.04]'
                }`}
              >
                {p}
              </button>
            ))}
          </div>

          {/* User Preferences Modal Trigger */}
          <button
            type="button"
            onClick={onOpenPreferences}
            className="p-2 rounded-xl bg-[#12121a] hover:bg-[#181824] border border-white/[0.08] text-zinc-400 hover:text-white transition-colors"
            title="User Preferences & Risk Profile"
          >
            <Sliders className="h-3.5 w-3.5" />
          </button>

          {/* Execute Research Button */}
          <button
            type="button"
            onClick={() => {
              const cleanInput = searchQuery.trim().toUpperCase() || selectedStock?.ticker || activeStock?.ticker;
              if (cleanInput) {
                onRunResearch(cleanInput, period, market, selectedStock);
                setIsOpen(false);
              }
            }}
            disabled={loading}
            className="btn-primary py-2 px-3 text-xs flex items-center gap-1.5 shadow-sm shadow-rose-950 shrink-0"
          >
            {loading ? <Spinner className="h-3.5 w-3.5" /> : <TrendingUp className="h-3.5 w-3.5" />}
            <span className="hidden sm:inline">Run Research</span>
          </button>
        </div>
      </div>

      {/* ── Omnisearch Results Dropdown ── */}
      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute left-4 right-4 md:left-4 md:right-auto md:w-[620px] top-full mt-1.5 rounded-2xl bg-[#0c0c14]/98 border border-white/[0.1] shadow-2xl backdrop-blur-xl overflow-hidden max-h-[440px] overflow-y-auto"
        >
          {/* Quick Tickers & Benchmarks (When query is empty) */}
          {!searchQuery.trim() && (
            <div className="p-3 space-y-2">
              <div className="px-2 text-[10px] font-mono uppercase text-zinc-500 font-semibold tracking-wider flex items-center justify-between">
                <span>Quick Benchmark Stocks</span>
                <span>Press Enter to select</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5">
                {QUICK_TICKERS.map((item, idx) => (
                  <button
                    key={item.ticker}
                    type="button"
                    onClick={() => handleSelectNavigableItem({ type: 'quick_ticker', data: item })}
                    className={`p-2 rounded-xl text-left transition-all border ${
                      selectedIndex === idx
                        ? 'bg-rose-950/40 border-rose-500/40 text-white'
                        : 'bg-white/[0.02] hover:bg-white/[0.06] border-white/[0.04] text-zinc-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs font-bold text-white">{item.ticker}</span>
                      <span className="text-[9px] font-mono text-zinc-500">{item.market}</span>
                    </div>
                    <p className="text-[10px] text-zinc-400 truncate mt-0.5">{item.name}</p>
                  </button>
                ))}
              </div>

              {/* Quick Workspaces Section */}
              <div className="pt-2 border-t border-white/[0.06]">
                <div className="px-2 pb-1 text-[10px] font-mono uppercase text-zinc-500 font-semibold tracking-wider">
                  Platform Workspaces
                </div>
                <div className="grid grid-cols-2 gap-1">
                  {workspaces.map((ws) => (
                    <button
                      key={ws.id}
                      type="button"
                      onClick={() => {
                        onSelectWorkspace(ws.id);
                        setIsOpen(false);
                      }}
                      className="flex items-center gap-2 p-2 rounded-lg text-left text-xs text-zinc-300 hover:text-white hover:bg-white/[0.04] transition-colors"
                    >
                      <LayoutDashboard className="h-3.5 w-3.5 text-rose-500" />
                      <span className="truncate">{ws.name}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Results: Matching Workspaces */}
          {matchingWorkspaces.length > 0 && (
            <div className="p-2 border-b border-white/[0.06]">
              <div className="px-2 py-1 text-[9px] font-mono uppercase text-zinc-500 font-semibold tracking-wider">
                Workspaces ({matchingWorkspaces.length})
              </div>
              {matchingWorkspaces.map((ws) => (
                <button
                  key={ws.id}
                  type="button"
                  onClick={() => handleSelectNavigableItem({ type: 'workspace', data: ws })}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs hover:bg-white/[0.04] text-left transition-colors"
                >
                  <div className="flex items-center gap-2.5">
                    <LayoutDashboard className="h-4 w-4 text-rose-400" />
                    <span className="font-semibold text-white">{ws.name}</span>
                  </div>
                  <span className="text-[10px] font-mono text-zinc-500">Workspace</span>
                </button>
              ))}
            </div>
          )}

          {/* Results: Matching Agents */}
          {matchingAgents.length > 0 && (
            <div className="p-2 border-b border-white/[0.06]">
              <div className="px-2 py-1 text-[9px] font-mono uppercase text-zinc-500 font-semibold tracking-wider">
                AI Agents ({matchingAgents.length})
              </div>
              {matchingAgents.map((ag) => (
                <button
                  key={ag.id}
                  type="button"
                  onClick={() => handleSelectNavigableItem({ type: 'agent', data: ag })}
                  className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs hover:bg-white/[0.04] text-left transition-colors"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Cpu className="h-4 w-4 text-rose-500 shrink-0" />
                    <div className="truncate">
                      <span className="font-semibold text-white">{ag.name}</span>
                      <span className="text-zinc-500 ml-1.5 text-[11px] font-mono">({ag.module})</span>
                    </div>
                  </div>
                  <span
                    className={`text-[8px] font-mono uppercase px-1.5 py-0.5 rounded font-semibold ${
                      ag.status === 'active'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    {ag.status === 'active' ? 'Active' : 'Planned'}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Results: Matching Stocks */}
          {searchResults.length > 0 && (
            <div className="p-2">
              <div className="px-2 py-1 text-[9px] font-mono uppercase text-zinc-500 font-semibold tracking-wider">
                Stock Matches ({searchResults.length})
              </div>
              {searchResults.map((item) => (
                <button
                  key={item.ticker}
                  type="button"
                  onClick={() => handleSelectNavigableItem({ type: 'stock', data: item })}
                  className="w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs hover:bg-rose-950/20 text-left transition-colors border border-transparent hover:border-rose-500/20"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/[0.04] font-mono font-bold text-white text-xs shrink-0">
                      {item.ticker.slice(0, 2)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-white">{item.ticker}</span>
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-white/[0.06] text-zinc-400">
                          {item.market || item.exchange}
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-400 truncate max-w-sm">{item.company_name}</p>
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-[10px] font-mono text-zinc-400">{item.currency}</span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Empty state when searching and no results found */}
          {searchQuery.trim().length >= 2 &&
            !searching &&
            matchingWorkspaces.length === 0 &&
            matchingAgents.length === 0 &&
            searchResults.length === 0 && (
              <div className="p-6 text-center text-zinc-500 text-xs">
                No stocks, workspaces, or agents found matching "{searchQuery}".
                <div className="mt-2 text-[10px] font-mono text-zinc-600">
                  Press Enter to submit direct ticker query "{searchQuery.toUpperCase()}".
                </div>
              </div>
            )}
        </div>
      )}
    </div>
  );
}
