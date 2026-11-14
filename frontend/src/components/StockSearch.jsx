import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

export default function StockSearch({ market, watchlists, onAdded }) {
  const [query, setQuery] = useState("");
  const [allMarkets, setAllMarkets] = useState(false);
  const [watchlistId, setWatchlistId] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [addingTicker, setAddingTicker] = useState(null);
  const [message, setMessage] = useState({ type: "", text: "" });

  const selected = watchlists.find((w) => String(w.watchlist_id) === watchlistId);

  // Pick the first list by default (and again if the chosen one was deleted)
  useEffect(() => {
    if (!selected && watchlists.length > 0) {
      setWatchlistId(String(watchlists[0].watchlist_id));
    }
  }, [watchlists, selected]);

  // Live search, waits 400 ms after typing stops
  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setSearching(false);
      return;
    }
    let cancelled = false;
    setSearching(true);
    const timer = setTimeout(async () => {
      try {
        const res = await api.get("/stocks/search", {
          params: { q: query.trim(), market: allMarkets ? undefined : market },
        });
        if (!cancelled) setResults(res.data);
      } catch (err) {
        if (!cancelled) setMessage({ type: "error", text: errorMessage(err) });
      } finally {
        if (!cancelled) setSearching(false);
      }
    }, 400);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query, allMarkets, market]);

  const add = async (ticker) => {
    if (!selected) {
      setMessage({ type: "error", text: "Choose a watchlist first." });
      return;
    }
    setAddingTicker(ticker);
    setMessage({ type: "", text: "" });
    try {
      const res = await api.post(`/watchlists/${selected.watchlist_id}/stocks`, { ticker });
      setMessage({
        type: "success",
        text: `${res.data.company_name} added to ${selected.name}`,
      });
      setQuery("");
      setResults([]);
      onAdded();
    } catch (err) {
      setMessage({ type: "error", text: errorMessage(err) });
    } finally {
      setAddingTicker(null);
    }
  };

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <h3 className="font-semibold text-gray-900">Find a stock</h3>

      <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-center">
        <input
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
          placeholder="Search by company name or ticker (e.g. HDFC, TCS, Apple)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Add to</span>
          <select
            value={watchlistId}
            onChange={(e) => setWatchlistId(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 focus:border-blue-500 focus:outline-none"
          >
            {watchlists.map((w) => (
              <option key={w.watchlist_id} value={w.watchlist_id}>{w.name}</option>
            ))}
          </select>
        </div>
      </div>

      <label className="mt-2 flex items-center gap-2 text-sm text-gray-600">
        <input
          type="checkbox"
          checked={allMarkets}
          onChange={(e) => setAllMarkets(e.target.checked)}
        />
        {allMarkets ? "Searching all markets" : `Searching ${market ?? "..."} only (change in Preferences)`}
      </label>

      {searching && <p className="mt-3 text-sm text-gray-500">Searching...</p>}
      {!searching && query.trim().length >= 2 && results.length === 0 && (
        <p className="mt-3 text-sm text-gray-500">
          No supported stocks found. Only company shares on NSE, BSE, NASDAQ and NYSE
          can be added. Try another name, or tick "all markets".
        </p>
      )}

      {results.length > 0 && (
        <ul className="mt-3 divide-y rounded-lg border">
          {results.map((s) => (
            <li key={s.ticker} className="flex items-center justify-between gap-3 px-3 py-2">
              <div>
                <p className="text-sm font-medium text-gray-900">{s.name}</p>
                <p className="text-xs text-gray-500">{s.ticker} · {s.market}</p>
              </div>
              <button
                onClick={() => add(s.ticker)}
                disabled={addingTicker === s.ticker || !selected}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
              >
                {addingTicker === s.ticker ? "Adding..." : "Add to Watchlist"}
              </button>
            </li>
          ))}
        </ul>
      )}

      {message.text && (
        <p className={`mt-3 text-sm ${message.type === "error" ? "text-red-600" : "text-green-600"}`}>
          {message.text}
        </p>
      )}
    </div>
  );
}