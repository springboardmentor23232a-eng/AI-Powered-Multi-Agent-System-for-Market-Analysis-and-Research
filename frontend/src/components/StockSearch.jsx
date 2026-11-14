import React, { useState } from 'react';
import { Search, Lightbulb, Plus, Check, Loader2, Sparkles, AlertTriangle, X } from 'lucide-react';
import { stockService, dashboardService } from '../services/api';

export const StockSearch = ({ onWatchlistUpdated, onStartResearch }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [addedMap, setAddedMap] = useState({});
  const [pendingUsAction, setPendingUsAction] = useState(null); // { type: 'research'|'watchlist', item }

  const handleSearch = async (termToSearch = searchTerm) => {
    const query = termToSearch.trim();
    if (!query) return;

    try {
      setLoading(true);
      setHasSearched(true);
      const res = await stockService.search(query);
      setResults(res.results || []);
    } catch (err) {
      console.error('Stock search error:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  const handleExampleClick = (example) => {
    setSearchTerm(example);
    handleSearch(example);
  };

  const executeAddToWatchlist = async (ticker) => {
    try {
      await dashboardService.addToWatchlist(ticker);
      setAddedMap((prev) => ({ ...prev, [ticker]: true }));
      if (onWatchlistUpdated) {
        onWatchlistUpdated();
      }
    } catch (err) {
      console.error('Failed to add to watchlist:', err);
    }
  };

  const handleWatchlistClick = (item) => {
    if (item.is_us_market || item.currency === 'USD') {
      setPendingUsAction({ type: 'watchlist', item });
    } else {
      executeAddToWatchlist(item.ticker);
    }
  };

  const handleResearchClick = (item) => {
    if (item.is_us_market || item.currency === 'USD') {
      setPendingUsAction({ type: 'research', item });
    } else if (onStartResearch) {
      onStartResearch(item.ticker, item.name, item.market);
    }
  };

  const handleConfirmUsAction = () => {
    if (!pendingUsAction) return;
    const { type, item } = pendingUsAction;
    setPendingUsAction(null);
    if (type === 'watchlist') {
      executeAddToWatchlist(item.ticker);
    } else if (type === 'research' && onStartResearch) {
      onStartResearch(item.ticker, item.name, item.market);
    }
  };

  return (
    <div className="w-full relative">
      {/* Section Header */}
      <div className="flex items-center gap-2 mb-3">
        <Search className="w-5 h-5 text-white" />
        <h2 className="text-xl font-bold text-white tracking-tight">Stock Search</h2>
      </div>

      {/* Search Input Bar + Search Button */}
      <div className="relative flex items-center gap-3">
        <div className="relative flex-1">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search for companies by name or ticker (e.g. AAPL, RELIANCE, TCS, TSLA)..."
            className="w-full px-4 py-3 bg-[#0b0f15] border border-[#1c2533] focus:border-emerald-500/70 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none transition-colors shadow-inner"
          />
        </div>

        <button
          onClick={() => handleSearch()}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-[#00a86b] hover:bg-[#00ba77] text-white font-semibold text-sm transition-all shadow-lg shadow-emerald-900/30 disabled:opacity-60 shrink-0"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Search className="w-4 h-4" />
          )}
          <span>Search</span>
        </button>
      </div>

      {/* Examples Row matching Reference Image 2 */}
      <div className="flex items-center flex-wrap gap-1.5 mt-3 text-xs text-slate-400">
        <Lightbulb className="w-3.5 h-3.5 text-amber-400/90 shrink-0 mr-1" />
        <span className="text-slate-400">Verified Tickers:</span>
        {['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'Apple (AAPL)', 'Microsoft (MSFT)', 'Tesla (TSLA)'].map((ex, idx, arr) => (
          <React.Fragment key={ex}>
            <button
              onClick={() => handleExampleClick(ex.includes('(') ? ex.split('(')[1].replace(')', '') : ex)}
              className="text-slate-300 hover:text-emerald-400 transition-colors underline-offset-2 hover:underline cursor-pointer"
            >
              {ex}
            </button>
            {idx < arr.length - 1 && <span className="text-slate-600">,</span>}
          </React.Fragment>
        ))}
      </div>

      {/* Search Results Dropdown/Card if active */}
      {hasSearched && (
        <div className="mt-4 p-3 bg-[#0b0f15] border border-[#1c2533] rounded-xl shadow-lg">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-400 px-2 py-1 uppercase tracking-wider">
            <span>Search Results ({results.length})</span>
          </div>
          {results.length === 0 ? (
            <p className="text-xs text-slate-500 px-2 py-2">
              No matching tickers found. Try searching by company name or symbol.
            </p>
          ) : (
            <div className="divide-y divide-[#161d28] mt-1">
              {results.map((item) => (
                <div
                  key={item.ticker}
                  className="flex items-center justify-between py-3 px-3 hover:bg-[#111722] rounded-lg transition-colors gap-3"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-white text-sm">{item.ticker}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#18212e] text-slate-300 border border-[#243144]">
                        {item.exchange || item.market}
                      </span>

                      {/* US Market Alert Badge */}
                      {item.is_us_market ? (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1 font-semibold">
                          <AlertTriangle className="w-2.5 h-2.5" />
                          <span>USD ($)</span>
                        </span>
                      ) : (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-medium">
                          INR (₹)
                        </span>
                      )}

                      {/* Real Price Display */}
                      {item.current_price != null && (
                        <span className="text-xs font-semibold text-white ml-auto sm:ml-2">
                          {item.currency_symbol || '$'}{item.current_price.toLocaleString()}
                        </span>
                      )}

                      {item.change_percent != null && (
                        <span className={`text-[11px] font-medium ${item.change_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                          {item.change_percent >= 0 ? '+' : ''}{item.change_percent}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-1 truncate">{item.name}</p>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {/* Launch Research button */}
                    {onStartResearch && (
                      <button
                        onClick={() => handleResearchClick(item)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-500/40 transition-all shadow-sm"
                        title="Start Multi-Agent Research"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                        <span>Research</span>
                      </button>
                    )}

                    {/* Add to Watchlist button */}
                    <button
                      onClick={() => handleWatchlistClick(item)}
                      disabled={addedMap[item.ticker]}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                        addedMap[item.ticker]
                          ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-default'
                          : 'bg-[#151c27] hover:bg-[#1d2737] text-slate-200 border border-[#222e40] hover:border-slate-500'
                      }`}
                    >
                      {addedMap[item.ticker] ? (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Saved</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-3.5 h-3.5" />
                          <span>Watchlist</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* US Market Confirmation Alert Modal */}
      {pendingUsAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md bg-[#0b0f15] border border-amber-500/40 rounded-2xl p-6 shadow-2xl relative space-y-4">
            <button
              onClick={() => setPendingUsAction(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 shrink-0">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">US Market Currency Notice</h3>
                <p className="text-xs text-amber-300/90 font-medium">{pendingUsAction.item.name} ({pendingUsAction.item.ticker})</p>
              </div>
            </div>

            <div className="p-3.5 bg-amber-950/20 border border-amber-900/40 rounded-xl text-xs text-slate-300 leading-relaxed space-y-2">
              <p>
                ⚠️ <strong>Currency Notice:</strong> This stock is listed on a US exchange (<strong>{pendingUsAction.item.exchange || 'NASDAQ/NYSE'}</strong>) and priced strictly in <strong>US Dollars ($ USD)</strong>.
              </p>
              <p className="text-amber-200">
                All valuation multiples, historical prices, and agent metrics will be processed in USD ($) rather than Indian Rupees (₹ INR).
              </p>
              <p className="font-semibold text-white pt-1">
                Are you sure you want to proceed with this US stock {pendingUsAction.type === 'research' ? 'research' : 'watchlist item'}?
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setPendingUsAction(null)}
                className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmUsAction}
                className="px-5 py-2 rounded-lg text-xs font-semibold text-black bg-amber-400 hover:bg-amber-300 transition-all shadow-md shadow-amber-900/30"
              >
                Yes, I am Sure (Proceed in USD)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StockSearch;
