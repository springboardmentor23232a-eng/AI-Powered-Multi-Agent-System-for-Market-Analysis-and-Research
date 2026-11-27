import React from 'react';
import {
  History,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Clock,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';

/**
 * ResearchHistorySection
 * Activity list of user-specific research tasks with status tracking and report modal trigger.
 */
export default function ResearchHistorySection({
  history = [],
  loading = false,
  error = null,
  onRefresh = () => {},
  onSelectReport = () => {},
  userEmail = '',
}) {
  return (
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
                {history.length}
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Executed tasks persisted for <span className="text-zinc-200 font-mono">{userEmail}</span>
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="btn-secondary py-1 px-2.5 text-[11px]"
          title="Refresh history"
        >
          <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin text-rose-400' : 'text-zinc-400'}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {error && <AlertBanner message={error} variant="error" />}

      {/* Loading */}
      {loading && history.length === 0 && (
        <div className="flex items-center justify-center py-10">
          <div className="flex flex-col items-center gap-2">
            <Spinner className="h-5 w-5 text-rose-500" />
            <span className="text-xs text-zinc-400">Loading research history…</span>
          </div>
        </div>
      )}

      {/* Empty */}
      {!loading && history.length === 0 && (
        <div className="text-center py-8 px-4 border border-dashed border-white/[0.08] rounded-xl bg-white/[0.01]">
          <History className="h-7 w-7 text-zinc-600 mx-auto mb-2 opacity-50" />
          <h4 className="text-xs font-semibold text-zinc-300">No Research Tasks Yet</h4>
          <p className="text-[11px] text-zinc-500 mt-0.5 max-w-xs mx-auto">
            Search for any ticker above and click <strong>"Research"</strong> to run your first analysis.
          </p>
        </div>
      )}

      {/* Activity List */}
      {history.length > 0 && (
        <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
          {history.map((taskItem) => {
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
                      onClick={() => onSelectReport(taskItem.task_id)}
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
  );
}
