import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import api from "../api";
import Header from "../components/Header";
import StockSearch from "../components/StockSearch";
import WatchlistSummary from "../components/WatchlistSummary";
import Preferences from "../components/Preferences";
import ResearchHistory from "../components/ResearchHistory";

export default function Dashboard() {
  const { user } = useAuth();
  const [prefs, setPrefs] = useState(null);
  const [watchlists, setWatchlists] = useState([]);
  const [loadingLists, setLoadingLists] = useState(true);

  const loadWatchlists = useCallback(() => {
    api
      .get("/watchlists")
      .then((res) => setWatchlists(res.data))
      .catch(() => setWatchlists([]))
      .finally(() => setLoadingLists(false));
  }, []);

  useEffect(() => {
    loadWatchlists();
  }, [loadWatchlists]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="mx-auto max-w-6xl space-y-6 p-8">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Welcome, {user.full_name}!</h2>
          <p className="mt-1 text-gray-600">{user.email}</p>
        </div>

        <StockSearch
          market={prefs?.market}
          watchlists={watchlists}
          onAdded={loadWatchlists}
        />

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <WatchlistSummary watchlists={watchlists} loading={loadingLists} />
          </div>
          <Preferences onChange={setPrefs} />
        </div>

        <ResearchHistory />
      </main>
    </div>
  );
}