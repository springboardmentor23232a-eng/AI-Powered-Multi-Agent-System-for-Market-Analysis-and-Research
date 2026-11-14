import { Link } from "react-router-dom";

export default function WatchlistSummary({ watchlists, loading }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">My Watchlists</h3>
        <Link to="/watchlists" className="text-sm font-medium text-blue-600 hover:underline">
          View all watchlists
        </Link>
      </div>

      {loading && <p className="mt-3 text-sm text-gray-500">Loading...</p>}

      <ul className="mt-4 divide-y">
        {watchlists.map((w) => (
          <li key={w.watchlist_id} className="py-3">
            <div className="flex items-center justify-between">
              <p className="font-medium text-gray-900">{w.name}</p>
              <span className="text-sm text-gray-500">
                {w.stocks.length} stock{w.stocks.length === 1 ? "" : "s"}
              </span>
            </div>
            {w.stocks.length > 0 && (
              <p className="mt-1 text-xs text-gray-500">
                {w.stocks.slice(0, 6).map((s) => s.ticker).join(", ")}
                {w.stocks.length > 6 ? " ..." : ""}
              </p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}