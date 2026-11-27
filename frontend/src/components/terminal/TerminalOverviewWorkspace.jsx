/**
 * TerminalOverviewWorkspace.jsx
 * Unified Financial Terminal Overview Workspace for SAI ANALYSIS.
 *
 * Composition:
 * - Active stock hero bar with real-time price telemetry and direct agent launch actions
 * - Multi-Agent Ecosystem Quick Access Ribbon
 * - 4-Card Bento KPI Grid with embedded SVG sparklines (MarketSnapshotBento)
 * - Large interactive SVG Stock Performance Chart & Volume bars (StockPerformanceChart)
 * - Research Intelligence & Pipeline Health panel with circular data integrity gauge (TelemetryHealthPanel)
 * - Verified OHLCV trading candles table (CandlesTable)
 * - Dual Intelligence Workspace: Recent Research Activity & Saved Stocks Watchlist
 */

import React from 'react';
import {
  TrendingUp,
  Bookmark,
  Database,
  Layers,
  Sparkles,
} from 'lucide-react';
import MarketSnapshotBento from '../market/MarketSnapshotBento';
import StockPerformanceChart, { ChartErrorBoundary } from '../market/StockPerformanceChart';
import TelemetryHealthPanel from '../market/TelemetryHealthPanel';
import CandlesTable from '../market/CandlesTable';
import ResearchHistorySection from '../research/ResearchHistorySection';
import WatchlistSection from '../watchlist/WatchlistSection';
import UserPreferencesModal from './UserPreferencesModal';
import AlertBanner from '../ui/AlertBanner';
import Spinner from '../ui/Spinner';
import { AGENT_REGISTRY } from '../../config/agentRegistry';

export default function TerminalOverviewWorkspace({
  overview,
  history,
  normalizedCandles = [],
  period = '1mo',
  onPeriodChange = () => {},
  activeStock,
  selectedStock,
  loading = false,
  error = null,
  onClearError = () => {},
  showRawTable = false,
  setShowRawTable = () => {},
  researchHistory = [],
  loadingHistory = false,
  historyError = null,
  fetchResearchHistory = () => {},
  onSelectReport = () => {},
  watchlist = [],
  loadingWatchlist = false,
  watchlistError = null,
  watchlistSuccess = null,
  addingWatchlist = false,
  onAddToWatchlist = () => {},
  onRemoveFromWatchlist = () => {},
  onSelectStockFromWatchlist = () => {},
  actionLoadingId = null,
  user = {},
  onSelectWorkspace = () => {},
  // User Preferences
  market = 'NSE',
  setMarket = () => {},
  setPeriod = () => {},
  preferenceId = null,
  preferenceUpdatedAt = null,
  loadingPreferences = false,
  savingPreferences = false,
  preferenceSuccess = null,
  setPreferenceSuccess = () => {},
  preferenceError = null,
  onSavePreferences = () => {},
  onResetPreferences = () => {},
}) {
  const currentTicker = overview?.ticker || activeStock?.ticker || selectedStock?.ticker || '';
  const currentCompany = overview?.company_name || activeStock?.company_name || selectedStock?.company_name || currentTicker;
  const currency = overview?.currency || 'USD';

  const isAlreadyInWatchlist = watchlist.some(
    (w) => w.ticker?.toUpperCase() === currentTicker?.toUpperCase()
  );

  return (
    <div className="space-y-6">
      {/* ── Global Error Banner ── */}
      {error && (
        <AlertBanner
          message={error}
          onClose={onClearError}
          type="error"
        />
      )}

      {/* ── Research Execution Loading State ── */}
      {loading && (
        <div className="flex items-center justify-center p-6 glass-card border border-rose-500/30 bg-[#0d0d14]/90 rounded-2xl shadow-xl">
          <div className="flex items-center gap-3">
            <Spinner className="h-5 w-5 text-rose-500" />
            <p className="text-xs font-mono text-zinc-300">
              Executing multi-agent research pipeline for <span className="text-white font-bold">{currentTicker || 'target'}</span>…
            </p>
          </div>
        </div>
      )}

      {/* ── Active Stock Hero Bar & Agent Action Triggers ── */}
      {currentTicker ? (
        <div className="glass-card p-4 sm:p-5 rounded-2xl border border-white/[0.08] bg-[#0c0c14]/90 flex flex-col lg:flex-row lg:items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-rose-600/30 to-red-700/20 border border-rose-500/30 text-rose-400 font-bold shrink-0 shadow-sm font-mono text-base">
              {currentTicker.slice(0, 2)}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-base font-extrabold text-white tracking-tight">
                  {currentTicker}
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-white/[0.05] text-zinc-300 border border-white/[0.08]">
                  {overview?.market || activeStock?.market || selectedStock?.market || 'NSE'}
                </span>
                <span className="text-[10px] font-mono text-zinc-500">
                  {currency}
                </span>
              </div>
              <p className="text-xs text-zinc-400 truncate max-w-md pt-0.5" title={currentCompany}>
                {currentCompany}
              </p>
            </div>
          </div>

          {/* Quick Price & Action Buttons */}
          <div className="flex items-center gap-3 flex-wrap sm:flex-nowrap justify-between lg:justify-end">
            {overview?.current_price !== undefined && (
              <div className="text-right pr-2">
                <div className="text-lg font-mono font-extrabold text-white">
                  {currency === 'INR' ? '₹' : '$'}
                  {Number(overview.current_price).toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </div>
                <div
                  className={`text-xs font-mono font-semibold ${
                    (overview.change || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {(overview.change || 0) >= 0 ? '+' : ''}
                  {Number(overview.change || 0).toFixed(2)} (
                  {(overview.change_percent || 0) >= 0 ? '+' : ''}
                  {Number(overview.change_percent || 0).toFixed(2)}%)
                </div>
              </div>
            )}

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => onAddToWatchlist(activeStock || selectedStock || { ticker: currentTicker, company_name: currentCompany })}
                disabled={addingWatchlist || isAlreadyInWatchlist}
                className={`px-3 py-2 rounded-xl text-xs font-medium border transition-all flex items-center gap-1.5 ${
                  isAlreadyInWatchlist
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-white/[0.04] hover:bg-white/[0.08] text-zinc-200 border-white/[0.08]'
                }`}
                title={isAlreadyInWatchlist ? 'Saved in Watchlist' : 'Add to Watchlist'}
              >
                {addingWatchlist ? (
                  <Spinner className="h-3.5 w-3.5" />
                ) : (
                  <Bookmark className="h-3.5 w-3.5 text-rose-500" />
                )}
                <span className="hidden sm:inline">
                  {isAlreadyInWatchlist ? 'In Watchlist' : 'Watchlist'}
                </span>
              </button>

              <button
                type="button"
                onClick={() => onSelectWorkspace('fundamental-analysis-agent')}
                className="btn-primary py-2 px-3 text-xs flex items-center gap-1.5"
                title="Launch Full Fundamental Analysis Agent"
              >
                <TrendingUp className="h-3.5 w-3.5" />
                <span>Fundamental Agent</span>
              </button>

              <button
                type="button"
                onClick={() => onSelectWorkspace('dataset-validation-agent')}
                className="px-3 py-2 rounded-xl text-xs font-medium text-white bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] transition-all flex items-center gap-1.5"
                title="Launch Dataset Validation Agent"
              >
                <Database className="h-3.5 w-3.5 text-emerald-400" />
                <span>Validation</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-card p-4 rounded-xl border border-white/[0.06] bg-[#0c0c14]/70 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/[0.04] text-rose-500">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs font-bold text-white">
                Terminal Ready • Select or search any ticker above to initiate research
              </p>
              <p className="text-[11px] text-zinc-400 font-mono">
                Suggested benchmarks: INFY.NS, TCS.NS, AAPL, MSFT, NVDA, RELIANCE.NS
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ── Multi-Agent Ecosystem Status Ribbon ── */}
      <div className="glass-card p-3.5 rounded-xl border border-white/[0.06] bg-[#09090e]/90">
        <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/[0.04]">
          <div className="flex items-center gap-2">
            <Layers className="h-3.5 w-3.5 text-rose-500" />
            <span className="text-[10px] font-mono uppercase font-bold text-zinc-400 tracking-wider">
              Autonomous Agent Fleet (7 Specialized Agents)
            </span>
          </div>
          <span className="text-[9px] font-mono text-zinc-500">
            Click any agent to launch dedicated workspace
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-7 gap-2">
          {AGENT_REGISTRY.map((ag) => {
            const isLive = ag.status === 'active';
            return (
              <button
                key={ag.id}
                type="button"
                onClick={() => onSelectWorkspace(ag.id)}
                className="p-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.04] hover:border-white/[0.08] text-left transition-all group"
                title={`${ag.name}: ${ag.description}`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[9px] font-mono text-zinc-500 uppercase">{ag.module}</span>
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${
                      isLive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400/70'
                    }`}
                  />
                </div>
                <p className="text-[11px] font-semibold text-zinc-300 group-hover:text-white truncate">
                  {ag.shortName}
                </p>
                <span
                  className={`text-[8px] font-mono uppercase font-semibold ${
                    isLive ? 'text-emerald-400' : 'text-amber-400/80'
                  }`}
                >
                  {isLive ? 'Active' : 'Planned'}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Section: User Preferences (Market & Analysis Period - Task 6) ── */}
      <UserPreferencesModal
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
        onSavePreferences={onSavePreferences}
        onResetPreferences={onResetPreferences}
        userEmail={user?.email}
      />

      {/* ── Row 1: Market Snapshot Bento Grid ── */}
      <MarketSnapshotBento
        overview={overview}
        currency={currency}
      />

      {/* ── Row 2: Performance Chart & Pipeline Health ── */}
      <div id="chart-section" className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChartErrorBoundary>
            <StockPerformanceChart
              history={history}
              period={period}
              onPeriodChange={onPeriodChange}
              currency={currency}
            />
          </ChartErrorBoundary>
        </div>

        <div className="lg:col-span-1">
          <TelemetryHealthPanel
            validation={history?.validation}
            overview={overview}
          />
        </div>
      </div>

      {/* ── Expandable Trading Candles Table ── */}
      <CandlesTable
        candles={normalizedCandles}
        isOpen={showRawTable}
        onToggle={() => setShowRawTable(!showRawTable)}
      />

      {/* ── Row 3: Dual Intelligence Workspace (History + Watchlist) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Research Activity History */}
        <div id="history-section">
          <ResearchHistorySection
            history={researchHistory}
            loading={loadingHistory}
            error={historyError}
            onRefresh={fetchResearchHistory}
            onSelectReport={onSelectReport}
            userEmail={user.email}
          />
        </div>

        {/* Right Column: Watchlist */}
        <div id="watchlist-section">
          <WatchlistSection
            watchlist={watchlist}
            loading={loadingWatchlist}
            error={watchlistError}
            success={watchlistSuccess}
            onSelect={onSelectStockFromWatchlist}
            onRemove={onRemoveFromWatchlist}
            actionLoadingId={actionLoadingId}
          />
        </div>
      </div>
    </div>
  );
}
