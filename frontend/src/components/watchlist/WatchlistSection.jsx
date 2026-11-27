import React, { useState } from 'react';
import {
  Bookmark,
  TrendingUp,
  Trash2,
  RefreshCw,
} from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';

export default function WatchlistSection({
  watchlist,
  loading,
  error,
  onRefresh,
  onResearch,
  onRemove,
  actionLoadingId,
}) {
  const [removingId, setRemovingId] = useState(null);

  const handleRemoveClick = async (savedStockId, ticker) => {
    setRemovingId(savedStockId);
    try {
      await onRemove(savedStockId, ticker);
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <section className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col gap-4">
      {/* ── Section Header ── */}
      <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-400">
            <Bookmark className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-tight">
                Saved Stocks & Watchlist
              </h3>
              <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                {watchlist.length} saved
              </span>
            </div>
            <p className="text-[11px] text-zinc-400">
              Personalized watchlist persisted in PostgreSQL
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="btn-secondary py-1 px-2.5 text-[11px]"
          title="Refresh watchlist from database"
        >
          <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin text-rose-400' : 'text-zinc-400'}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {error && <AlertBanner message={error} variant="error" />}

      {/* ── Loading State ── */}
      {loading && watchlist.length === 0 && (
        <div className="flex items-center justify-center py-10">
          <div className="flex flex-col items-center gap-2">
            <Spinner className="h-5 w-5 text-rose-500" />
            <span className="text-xs text-zinc-400">Loading saved stocks…</span>
          </div>
        </div>
      )}

      {/* ── Empty State ── */}
      {!loading && watchlist.length === 0 && (
        <div className="text-center py-8 px-4 border border-dashed border-white/[0.08] rounded-xl bg-white/[0.01]">
          <Bookmark className="h-7 w-7 text-zinc-600 mx-auto mb-2 opacity-50" />
          <h4 className="text-xs font-semibold text-zinc-300">Your Watchlist is Empty</h4>
          <p className="text-[11px] text-zinc-500 mt-0.5 max-w-xs mx-auto">
            Search for a stock above and click <strong>"Add to Watchlist"</strong> to monitor companies here.
          </p>
        </div>
      )}

      {/* ── Watchlist Table ── */}
      {watchlist.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-white/[0.06]">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/[0.02] text-zinc-400 text-[10px] uppercase tracking-wider border-b border-white/[0.06]">
              <tr>
                <th className="py-2.5 px-3">Ticker</th>
                <th className="py-2.5 px-3">Company Name</th>
                <th className="py-2.5 px-3 hidden sm:table-cell">Exchange</th>
                <th className="py-2.5 px-3 hidden md:table-cell">Saved Date</th>
                <th className="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] bg-[#0c0c12]/80 text-zinc-200">
              {watchlist.map((item) => {
                const isBusy = removingId === item.saved_stock_id || actionLoadingId === item.ticker;

                return (
                  <tr key={item.saved_stock_id || item.ticker} className="hover:bg-white/[0.03] transition-colors group">
                    <td className="py-2.5 px-3">
                      <span className="font-mono text-xs font-bold text-white bg-white/[0.06] px-2 py-0.5 rounded border border-white/[0.1] group-hover:border-rose-500/40">
                        {item.ticker}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-sans font-medium text-zinc-200 max-w-[140px] truncate" title={item.company_name || item.ticker}>
                      {item.company_name || item.ticker}
                    </td>
                    <td className="py-2.5 px-3 hidden sm:table-cell">
                      {item.exchange ? (
                        <span className="text-[10px] font-semibold text-rose-400 uppercase bg-rose-500/10 px-1.5 py-0.5 rounded border border-rose-500/20">
                          {item.exchange}
                        </span>
                      ) : (
                        <span className="text-zinc-500 text-[11px]">—</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-zinc-500 text-[11px] hidden md:table-cell">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : 'Recent'}
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => onResearch(item.ticker)}
                          disabled={isBusy}
                          className="btn-primary py-1 px-2.5 text-[11px] flex items-center gap-1 shadow-sm shadow-rose-950"
                          title={`Research ${item.ticker}`}
                        >
                          {actionLoadingId === item.ticker ? (
                            <Spinner className="h-3 w-3" />
                          ) : (
                            <TrendingUp className="h-3 w-3" />
                          )}
                          <span>Research</span>
                        </button>

                        <button
                          type="button"
                          onClick={() => handleRemoveClick(item.saved_stock_id, item.ticker)}
                          disabled={isBusy}
                          title={`Remove ${item.ticker}`}
                          className="p-1 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-950/40 transition-colors"
                          aria-label={`Remove ${item.ticker}`}
                        >
                          {removingId === item.saved_stock_id ? (
                            <Spinner className="h-3 w-3 text-rose-400" />
                          ) : (
                            <Trash2 className="h-3 w-3" />
                          )}
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
    </section>
  );
}

