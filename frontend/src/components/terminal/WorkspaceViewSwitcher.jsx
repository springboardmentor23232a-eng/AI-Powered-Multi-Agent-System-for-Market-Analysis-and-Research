/**
 * WorkspaceViewSwitcher.jsx
 * Dynamic Platform Workspace & AI Agent Component Resolver for SAI ANALYSIS.
 *
 * Capabilities:
 * - Switches between all 3 Platform Workspaces (Overview, Watchlist, Archive)
 * - Dynamically resolves and renders Active AI Agents through their registered components:
 *   - Dataset Validation Agent (Module 2) -> DatasetValidationDashboard
 *   - Fundamental Analysis Agent (Module 3) -> FundamentalAnalysisView
 * - Dynamically resolves and renders Planned AI Agents through AgentTeaserCard:
 *   - Market Data Collection Agent (Module 2)
 *   - Technical Analysis Agent (Module 4)
 *   - News & Sentiment Agent (Module 5)
 *   - Risk Analysis Agent (Module 6)
 *   - Supervisor Agent (Module 7)
 * - Supports future-agent extensibility via agentRegistry configuration with zero rewrite.
 */

import React from 'react';
import {
  ArrowLeft,
  Bookmark,
  History,
  TrendingUp,
  Database,
  LayoutDashboard,
} from 'lucide-react';
import TerminalOverviewWorkspace from './TerminalOverviewWorkspace';
import AgentTeaserCard from './AgentTeaserCard';
import WatchlistSection from '../watchlist/WatchlistSection';
import ResearchHistorySection from '../research/ResearchHistorySection';
import FundamentalAnalysisView from '../research/FundamentalAnalysisView';
import FinancialStatementsView from '../research/FinancialStatementsView';
import DatasetValidationDashboard from '../dataset/DatasetValidationDashboard';
import {
  getAgentById,
  hasValidComponent,
} from '../../config/agentRegistry';

export default function WorkspaceViewSwitcher({
  activeWorkspace = 'overview',
  onSelectWorkspace = () => {},
  // Market & Telemetry Data
  overview = null,
  history = null,
  normalizedCandles = [],
  period = '1mo',
  onPeriodChange = () => {},
  activeStock = null,
  selectedStock = null,
  loading = false,
  error = null,
  onClearError = () => {},
  showRawTable = false,
  setShowRawTable = () => {},
  // Fundamental Analysis Data
  fundamental = null,
  loadingFundamental = false,
  fundamentalError = null,
  fetchFundamental = () => {},
  financials = null,
  loadingFinancials = false,
  financialsError = null,
  fetchFinancials = () => {},
  // Watchlist Data
  watchlist = [],
  loadingWatchlist = false,
  watchlistError = null,
  watchlistSuccess = null,
  addingWatchlist = false,
  onAddToWatchlist = () => {},
  onRemoveFromWatchlist = () => {},
  onSelectStockFromWatchlist = () => {},
  actionLoadingId = null,
  // Research History Data
  researchHistory = [],
  loadingHistory = false,
  historyError = null,
  fetchResearchHistory = () => {},
  onSelectReport = () => {},
  // User Data & Preferences
  user = {},
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
  const currentTicker =
    overview?.ticker || activeStock?.ticker || selectedStock?.ticker || '';
  const currency = overview?.currency || fundamental?.currency || 'USD';

  // ── 1. PLATFORM WORKSPACE SWITCHING ──────────────────────────────────────
  if (activeWorkspace === 'overview') {
    return (
      <TerminalOverviewWorkspace
        overview={overview}
        history={history}
        normalizedCandles={normalizedCandles}
        period={period}
        onPeriodChange={onPeriodChange}
        activeStock={activeStock}
        selectedStock={selectedStock}
        loading={loading}
        error={error}
        onClearError={onClearError}
        showRawTable={showRawTable}
        setShowRawTable={setShowRawTable}
        researchHistory={researchHistory}
        loadingHistory={loadingHistory}
        historyError={historyError}
        fetchResearchHistory={fetchResearchHistory}
        onSelectReport={onSelectReport}
        watchlist={watchlist}
        loadingWatchlist={loadingWatchlist}
        watchlistError={watchlistError}
        watchlistSuccess={watchlistSuccess}
        addingWatchlist={addingWatchlist}
        onAddToWatchlist={onAddToWatchlist}
        onRemoveFromWatchlist={onRemoveFromWatchlist}
        onSelectStockFromWatchlist={onSelectStockFromWatchlist}
        actionLoadingId={actionLoadingId}
        user={user}
        onSelectWorkspace={onSelectWorkspace}
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
        onSavePreferences={onSavePreferences}
        onResetPreferences={onResetPreferences}
      />
    );
  }

  if (activeWorkspace === 'watchlist') {
    return (
      <div className="space-y-6 max-w-6xl mx-auto py-2">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onSelectWorkspace('overview')}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors"
              title="Return to Terminal Overview"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <Bookmark className="h-4 w-4" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-tight">
                  Saved Stocks Watchlist
                </h1>
                <p className="text-[11px] text-zinc-400 font-mono">
                  PostgreSQL-Persisted Portfolio Watchlist • {watchlist.length} Tickers Tracked
                </p>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onSelectWorkspace('overview')}
            className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
          >
            <LayoutDashboard className="h-3.5 w-3.5 text-rose-500" />
            <span>Terminal Overview</span>
          </button>
        </div>

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
    );
  }

  if (activeWorkspace === 'history') {
    return (
      <div className="space-y-6 max-w-6xl mx-auto py-2">
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => onSelectWorkspace('overview')}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors"
              title="Return to Terminal Overview"
            >
              <ArrowLeft className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <History className="h-4 w-4" />
              </div>
              <div>
                <h1 className="text-base font-bold text-white tracking-tight">
                  Research History & Telemetry Archive
                </h1>
                <p className="text-[11px] text-zinc-400 font-mono">
                  {researchHistory.length} Research Tasks Evaluated • Click Report to View Full Audit
                </p>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={() => onSelectWorkspace('overview')}
            className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
          >
            <LayoutDashboard className="h-3.5 w-3.5 text-rose-500" />
            <span>Terminal Overview</span>
          </button>
        </div>

        <ResearchHistorySection
          history={researchHistory}
          loading={loadingHistory}
          error={historyError}
          onRefresh={fetchResearchHistory}
          onSelectReport={onSelectReport}
          userEmail={user.email}
        />
      </div>
    );
  }

  // ── 2. DYNAMIC AI AGENT RESOLUTION ─────────────────────────────────────────
  const agent = getAgentById(activeWorkspace);

  if (agent) {
    // A. Active Agent: Fundamental Analysis Agent (Module 3)
    if (agent.id === 'fundamental-analysis-agent') {
      return (
        <div className="space-y-4 max-w-7xl mx-auto py-1">
          <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => onSelectWorkspace('overview')}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors"
                title="Return to Terminal Overview"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <TrendingUp className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-sm font-bold text-white tracking-tight">
                      {agent.name}
                    </h1>
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ACTIVE
                    </span>
                  </div>
                  <p className="text-[10px] font-mono text-zinc-400">
                    Active Stock Target: <span className="text-white font-bold">{currentTicker || 'None (Search above)'}</span> • 3-Statement Modeling & Peer Comparison
                  </p>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onSelectWorkspace('overview')}
              className="text-xs font-mono text-zinc-400 hover:text-white transition-colors"
            >
              Dashboard Overview
            </button>
          </div>

          {/* 3-Statement Modeling View */}
          <FinancialStatementsView
            financials={financials}
            loading={loadingFinancials}
            error={financialsError}
            onRefresh={() => fetchFinancials(currentTicker)}
            currency={currency}
            ticker={currentTicker}
          />

          <FundamentalAnalysisView
            fundamental={fundamental}
            loading={loadingFundamental}
            error={fundamentalError}
            onRefresh={() => fetchFundamental(currentTicker)}
            currency={currency}
            ticker={currentTicker}
          />
        </div>
      );
    }

    // B. Active Agent: Dataset Validation Agent (Module 2)
    if (agent.id === 'dataset-validation-agent') {
      return (
        <div className="space-y-4 max-w-7xl mx-auto py-1">
          <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => onSelectWorkspace('overview')}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/[0.05] transition-colors"
                title="Return to Terminal Overview"
              >
                <ArrowLeft className="h-4 w-4" />
              </button>
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <Database className="h-4 w-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-sm font-bold text-white tracking-tight">
                      {agent.name}
                    </h1>
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      ACTIVE
                    </span>
                  </div>
                  <p className="text-[10px] font-mono text-zinc-400">
                    Active Target: <span className="text-white font-bold">{currentTicker || 'None'}</span> • Automated Multi-Tier Data Cleaning
                  </p>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => onSelectWorkspace('overview')}
              className="text-xs font-mono text-zinc-400 hover:text-white transition-colors"
            >
              Dashboard Overview
            </button>
          </div>

          <DatasetValidationDashboard initialTicker={currentTicker} />
        </div>
      );
    }

    // C. Generic Active Agent Resolver (For Future Agents with registered component)
    if (hasValidComponent(agent) && typeof agent.component === 'function') {
      const AgentComponent = agent.component;
      return (
        <div className="space-y-4 max-w-7xl mx-auto py-1">
          <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
            <button
              type="button"
              onClick={() => onSelectWorkspace('overview')}
              className="flex items-center gap-2 text-xs font-mono text-zinc-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4 text-rose-500" />
              <span>Back to Overview</span>
            </button>
            <span className="text-xs font-mono text-rose-400">{agent.name}</span>
          </div>
          <AgentComponent
            ticker={currentTicker}
            overview={overview}
            history={history}
            period={period}
            fundamental={fundamental}
          />
        </div>
      );
    }

    // D. Planned Roadmap Agents (Market Data, Technical, News, Risk, Supervisor)
    return (
      <AgentTeaserCard
        agent={agent}
        onBackToOverview={() => onSelectWorkspace('overview')}
        onSelectWorkspace={onSelectWorkspace}
      />
    );
  }

  // ── 3. DEFENSIVE UNKNOWN WORKSPACE FALLBACK ─────────────────────────────────
  return (
    <TerminalOverviewWorkspace
      overview={overview}
      history={history}
      normalizedCandles={normalizedCandles}
      period={period}
      onPeriodChange={onPeriodChange}
      activeStock={activeStock}
      selectedStock={selectedStock}
      loading={loading}
      error={error}
      onClearError={onClearError}
      showRawTable={showRawTable}
      setShowRawTable={setShowRawTable}
      researchHistory={researchHistory}
      loadingHistory={loadingHistory}
      historyError={historyError}
      fetchResearchHistory={fetchResearchHistory}
      onSelectReport={onSelectReport}
      watchlist={watchlist}
      loadingWatchlist={loadingWatchlist}
      watchlistError={watchlistError}
      watchlistSuccess={watchlistSuccess}
      addingWatchlist={addingWatchlist}
      onAddToWatchlist={onAddToWatchlist}
      onRemoveFromWatchlist={onRemoveFromWatchlist}
      onSelectStockFromWatchlist={onSelectStockFromWatchlist}
      actionLoadingId={actionLoadingId}
      user={user}
      onSelectWorkspace={onSelectWorkspace}
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
      onSavePreferences={onSavePreferences}
      onResetPreferences={onResetPreferences}
    />
  );
}
