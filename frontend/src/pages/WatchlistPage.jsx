import React, { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Bookmark,
  Trash2,
  Play,
  Calendar,
  Building2,
  RefreshCw,
  FolderPlus,
  AlertCircle,
  TrendingUp,
} from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StockSearchCombobox from '../components/watchlist/StockSearchCombobox';
import ConfirmModal from '../components/common/ConfirmModal';

export default function WatchlistPage() {
  const { addToast } = useAuth();
  const { openResearchModal } = useOutletContext();

  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Deletion modal state
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
      addToast(`Removed ${stockToDelete.ticker} from your watchlist.`, 'info');
      setStockToDelete(null);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to remove stock from watchlist.';
      addToast(msg, 'error');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Bookmark className="w-6 h-6 text-blue-600" />
            My Stock Watchlist
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Curate and monitor equities across NSE, BSE, NASDAQ, and NYSE for automated research
          </p>
        </div>

        <button
          onClick={() => fetchWatchlist(true)}
          className="self-start sm:self-auto p-2.5 bg-white border border-slate-200 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-sm transition-colors"
          title="Refresh Watchlist"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Stock Search Combobox */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200/80 shadow-sm">
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
          Add Stock to Watchlist
        </label>
        <StockSearchCombobox
          onStockAdded={handleStockAdded}
          existingTickers={watchlist}
        />
        <p className="mt-2 text-xs text-slate-400">
          Search real market tickers or company names across supported exchanges.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm font-medium">
          {error}
        </div>
      )}

      {/* Watchlist Cards/Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-xs text-slate-500 font-medium">Loading saved stocks...</p>
          </div>
        ) : watchlist.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-14 h-14 rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-4">
              <FolderPlus className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-800">Your watchlist is empty</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 leading-relaxed">
              You haven't saved any stocks yet. Use the search field above to search for companies (like Apple, Nvidia, Infosys, Reliance) and add them to your watchlist.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-semibold text-slate-400 bg-slate-50/70">
                  <th className="py-3.5 px-6">Company / Ticker</th>
                  <th className="py-3.5 px-4">Market</th>
                  <th className="py-3.5 px-4">Date Added</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {watchlist.map((stock) => (
                  <tr key={stock.saved_stock_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-6">
                      <div className="font-extrabold text-slate-900 flex items-center gap-2">
                        <span>{stock.ticker}</span>
                      </div>
                      <div className="text-xs text-slate-500 truncate max-w-[280px]">
                        {stock.company_name}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                        {stock.market}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-xs text-slate-500 whitespace-nowrap">
                      {new Date(stock.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </td>
                    <td className="py-4 px-6 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => openResearchModal(stock)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-blue-600 hover:text-white bg-blue-50 hover:bg-blue-600 transition-all border border-blue-200 hover:border-transparent shadow-sm"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                          <span>Start Research</span>
                        </button>
                        <button
                          onClick={() => setStockToDelete(stock)}
                          className="p-1.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 transition-colors"
                          title="Remove from Watchlist"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Confirmation Modal for Deletion */}
      <ConfirmModal
        isOpen={!!stockToDelete}
        title="Remove Stock from Watchlist"
        message={`Are you sure you want to remove ${stockToDelete?.ticker} (${stockToDelete?.company_name}) from your personal watchlist? This will not affect your existing research history.`}
        confirmText="Remove Stock"
        cancelText="Keep"
        onConfirm={handleConfirmDelete}
        onCancel={() => setStockToDelete(null)}
        isDangerous={true}
        loading={deleting}
      />
    </div>
  );
}

