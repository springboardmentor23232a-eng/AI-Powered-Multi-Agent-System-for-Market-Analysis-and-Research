import React, { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  Bookmark,
  Trash2,
  Play,
  RefreshCw,
  FolderPlus,
  Compass,
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StockSearchCombobox from '../components/watchlist/StockSearchCombobox';
import ConfirmModal from '../components/common/ConfirmModal';

export default function WatchlistPage() {
  const { addToast } = useAuth();
  const { openResearchModal } = useOutletContext();
  const navigate = useNavigate();

  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const [stockToDelete, setStockToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchWatchlist = async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const res = await api.get('/watchlist');
      setWatchlist(res.data);
      setError(null);
    } catch (err) {
      console.error('Failed to load watchlist:', err);
      setError('Could not retrieve watchlist from the database.');
    } finally {
      setLoading(false);
      if (isManual) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const handleStockAdded = (newStock) => {
    setWatchlist((prev) => [newStock, ...prev]);
  };

  const handleConfirmDelete = async () => {
    if (!stockToDelete) return;
    setDeleting(true);
    try {
      await api.delete(`/watchlist/${stockToDelete.saved_stock_id}`);
      setWatchlist((prev) =>
        prev.filter((item) => item.saved_stock_id !== stockToDelete.saved_stock_id)
      );
      addToast(`Removed ${stockToDelete.ticker} from your radar.`, 'info');
      setStockToDelete(null);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to remove stock from watchlist.';
      addToast(msg, 'error');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[10px] font-mono uppercase tracking-widest text-amber-700 font-semibold">
            Monitored Securities
          </span>
          <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Bookmark className="w-6 h-6 text-[#0A624C]" />
            Radar Watchlist
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Curate equities across NSE, BSE, NASDAQ & NYSE for instant chart exploration and agent runs
          </p>
        </div>

        <button
          onClick={() => fetchWatchlist(true)}
          className="self-start sm:self-auto p-2.5 bg-white border border-[#E4E1D8] rounded-xl text-slate-600 hover:text-[#0A624C] transition-colors"
          title="Refresh Watchlist"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="glass-panel p-6 rounded-3xl">
        <label className="block text-[11px] font-mono font-bold text-[#0A624C] uppercase tracking-wider mb-2">
          Pin Security to Radar
        </label>
        <StockSearchCombobox onStockAdded={handleStockAdded} existingTickers={watchlist} />
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono">
          {error}
        </div>
      )}

      {loading ? (
        <div className="glass-panel p-12 rounded-3xl text-center space-y-3">
          <div className="w-6 h-6 border-2 border-[#0A624C] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-mono text-slate-500">LOADING RADAR...</p>
        </div>
      ) : watchlist.length === 0 ? (
        <div className="glass-panel p-16 rounded-3xl text-center">
          <div className="w-14 h-14 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] text-slate-400 flex items-center justify-center mx-auto mb-4">
            <FolderPlus className="w-7 h-7" />
          </div>
          <h3 className="text-base font-bold text-slate-900">Your radar is empty</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
            Search for companies above (AAPL, NVDA, INFY, Reliance) and pin them to launch 1-click analysis.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {watchlist.map((stock) => (
            <div key={stock.saved_stock_id} className="glass-card p-5 rounded-3xl flex flex-col justify-between gap-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-lg font-extrabold text-slate-900">{stock.ticker}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                      {stock.market}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 font-medium">{stock.company_name}</p>
                  <p className="text-[10px] font-mono text-slate-400 mt-1">
                    PINNED {new Date(stock.created_at).toLocaleDateString()}
                  </p>
                </div>

                <button
                  onClick={() => setStockToDelete(stock)}
                  className="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-[#E4E1D8] hover:border-rose-200 transition-colors"
                  title="Remove from Watchlist"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex items-center gap-2 pt-3 border-t border-[#E4E1D8]">
                <button
                  onClick={() => navigate(`/explorer?ticker=${stock.ticker}&market=${stock.market}`)}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono font-semibold text-[#1E3A5F] bg-[#FAF9F5] hover:bg-[#EFECE4] border border-[#DCD8CD] transition-all"
                >
                  <Compass className="w-3.5 h-3.5" />
                  CHARTS
                </button>
                <button
                  onClick={() => openResearchModal(stock)}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono font-bold text-white bg-[#0A624C] hover:bg-[#084C3B] transition-all"
                >
                  <Play className="w-3.5 h-3.5 fill-white" />
                  RUN AGENTS
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <ConfirmModal
        isOpen={!!stockToDelete}
        title="Remove Security from Radar"
        message={`Remove ${stockToDelete?.ticker} (${stockToDelete?.company_name}) from your radar watchlist? Existing research dossiers remain unaffected.`}
        confirmText="Remove"
        cancelText="Keep"
        onConfirm={handleConfirmDelete}
        onCancel={() => setStockToDelete(null)}
        isDangerous={true}
        loading={deleting}
      />
    </div>
  );
}
