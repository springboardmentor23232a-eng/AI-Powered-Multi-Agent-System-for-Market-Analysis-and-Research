import React, { useState, useEffect, useRef } from 'react';
import { Search, Plus, Loader2, Check } from 'lucide-react';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';

export default function StockSearchCombobox({ onStockAdded, existingTickers = [] }) {
  const { addToast } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [addingTicker, setAddingTicker] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.get(`/stocks/search?q=${encodeURIComponent(query.trim())}`);
        setResults(res.data || []);
        setIsOpen(true);
      } catch (err) {
        console.error('Failed to search stocks:', err);
      } finally {
        setLoading(false);
      }
    }, 280);

    return () => clearTimeout(timer);
  }, [query]);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAddStock = async (stock) => {
    setAddingTicker(stock.ticker);
    try {
      const res = await api.post('/watchlist', {
        ticker: stock.ticker,
        company_name: stock.company_name,
        market: stock.market,
      });
      addToast(`Pinned ${stock.ticker} (${stock.company_name}) to your radar!`, 'success');
      if (onStockAdded) {
        onStockAdded(res.data);
      }
      setQuery('');
      setIsOpen(false);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to add stock to watchlist.';
      addToast(msg, 'error');
    } finally {
      setAddingTicker(null);
    }
  };

  return (
    <div ref={containerRef} className="relative w-full max-w-xl">
      <div className="relative">
        <Search className="w-5 h-5 text-slate-400 absolute left-4 top-3" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder="Search ticker or company (AAPL, NVDA, INFY, Reliance, TCS)..."
          className="w-full pl-12 pr-11 py-3 bg-[#FAF9F5] border border-[#DCD8CD] rounded-2xl text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:border-[#0A624C] transition-all font-medium text-sm"
        />
        {loading && (
          <div className="absolute right-4 top-3.5">
            <Loader2 className="w-5 h-5 text-[#0A624C] animate-spin" />
          </div>
        )}
      </div>

      {isOpen && (
        <div className="absolute left-0 right-0 top-full mt-2 bg-white rounded-2xl shadow-xl border border-[#E4E1D8] overflow-hidden z-40 max-h-96 overflow-y-auto divide-y divide-[#EDEAE0]">
          {results.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-sm">
              No matching verified stocks found for <span className="font-semibold text-slate-900">"{query}"</span>.
            </div>
          ) : (
            results.map((stock) => {
              const isAlreadySaved = existingTickers.some(
                (item) => item.ticker === stock.ticker && item.market === stock.market
              );
              const isCurrentAdding = addingTicker === stock.ticker;

              return (
                <div
                  key={`${stock.market}-${stock.ticker}`}
                  className="px-4 py-3 hover:bg-[#FAF9F5] transition-colors flex items-center justify-between gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-slate-900 text-sm">{stock.ticker}</span>
                      <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                        {stock.market}
                      </span>
                      {stock.sector && (
                        <span className="text-[11px] text-slate-500 truncate hidden sm:inline">
                          • {stock.sector}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-600 truncate mt-0.5">{stock.company_name}</p>
                  </div>

                  <div>
                    {isAlreadySaved ? (
                      <span className="inline-flex items-center gap-1 text-xs font-mono font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                        <Check className="w-3.5 h-3.5" />
                        PINNED
                      </span>
                    ) : (
                      <button
                        onClick={() => handleAddStock(stock)}
                        disabled={isCurrentAdding}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-bold text-white bg-[#0A624C] hover:bg-[#084C3B] rounded-lg transition-all disabled:opacity-50"
                      >
                        {isCurrentAdding ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Plus className="w-3.5 h-3.5" />
                        )}
                        PIN
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
