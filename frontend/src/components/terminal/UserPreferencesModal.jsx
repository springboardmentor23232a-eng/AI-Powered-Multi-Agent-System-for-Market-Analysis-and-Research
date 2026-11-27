import React from 'react';
import {
  Sliders,
  Building2,
  Calendar,
  CheckCircle2,
  Check,
  RefreshCw,
  X,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';

/**
 * UserPreferencesModal
 * Manages user default market exchange and analysis period persisted in PostgreSQL.
 * Supports both standalone inline section and overlay modal modes.
 */
export default function UserPreferencesModal({
  isOpen = true,
  isModal = false,
  onClose = () => {},
  market = 'NSE',
  setMarket = () => {},
  period = '1mo',
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
  userEmail = '',
}) {
  if (isModal && !isOpen) return null;

  const content = (
    <section
      id="preferences-section"
      className={`glass-card p-5 lg:p-6 border border-white/[0.08] bg-[#0d0d13]/90 relative z-10 ${
        isModal ? 'max-w-2xl w-full mx-auto shadow-2xl' : ''
      }`}
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
              <span className="text-zinc-200 font-mono">{userEmail || 'authenticated user'}</span>.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto text-[10px] font-mono text-zinc-500">
          {preferenceId && <span>Pref #{preferenceId}</span>}
          {preferenceUpdatedAt && (
            <span>
              • Saved: {new Date(preferenceUpdatedAt).toLocaleTimeString()}
            </span>
          )}
          {isModal && (
            <button
              type="button"
              onClick={onClose}
              className="p-1 text-zinc-400 hover:text-white rounded-lg hover:bg-white/[0.05] transition-colors ml-2"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
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
      <form onSubmit={onSavePreferences} className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-5">
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
              <option value="BSE">BSE — Bombay Stock Exchange (.BO)</option>
              <option value="NASDAQ">NASDAQ — National Association of Securities Dealers (US)</option>
              <option value="NYSE">NYSE — New York Stock Exchange (US)</option>
            </select>
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
              Select default historical timeframe for automated chart generation and research synthesis.
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
            Account: <span className="text-zinc-300">{userEmail || 'Authenticated'}</span> • Isolated user preferences
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto">
            <button
              type="button"
              onClick={onResetPreferences}
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
  );

  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade-in">
        <div className="relative w-full max-w-2xl">
          {content}
        </div>
      </div>
    );
  }

  return content;
}
