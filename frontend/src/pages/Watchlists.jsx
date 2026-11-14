import { useCallback, useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import Header from "../components/Header";
import PriceChart from "../components/PriceChart";

export default function Watchlists() {
  const [watchlists, setWatchlists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newName, setNewName] = useState("");
  const [chartTicker, setChartTicker] = useState(null);
  const [message, setMessage] = useState({ type: "", text: "" });

  const notify = (type, text) => setMessage({ type, text });

  const load = useCallback(async () => {
    try {
      const res = await api.get("/watchlists");
      setWatchlists(res.data);
    } catch (err) {
      setMessage({ type: "error", text: errorMessage(err) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const createList = async (e) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    try {
      await api.post("/watchlists", { name });
      setNewName("");
      notify("success", `Watchlist "${name}" created`);
      load();
    } catch (err) {
      notify("error", errorMessage(err));
    }
  };

  const deleteList = async (w) => {
    if (!window.confirm(`Delete "${w.name}" and the ${w.stocks.length} stock(s) in it?`)) return;
    try {
      await api.delete(`/watchlists/${w.watchlist_id}`);
      notify("success", `Watchlist "${w.name}" deleted`);
      load();
    } catch (err) {
      notify("error", errorMessage(err));
    }
  };

  const removeStock = async (id) => {
    try {
      await api.delete(`/saved-stocks/${id}`);
      load();
    } catch (err) {
      notify("error", errorMessage(err));
    }
  };

  const moveStock = async (id, watchlistId) => {
    try {
      await api.patch(`/saved-stocks/${id}`, { watchlist_id: Number(watchlistId) });
      load();
    } catch (err) {
      notify("error", errorMessage(err));
    }
  };

  const research = async (ticker) => {
    try {
      await api.post("/research", { ticker });
      notify("success", `Research started for ${ticker}. Open the Dashboard to see it in Research History.`);
    } catch (err) {
      notify("error", errorMessage(err));
    }
  };

  const btn = "rounded-lg border px-3 py-1 text-sm";

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="mx-auto max-w-6xl space-y-6 p-8">
        <h2 className="text-2xl font-semibold text-gray-900">My Watchlists</h2>

        <form onSubmit={createList} className="flex flex-col gap-3 rounded-xl bg-white p-6 shadow sm:flex-row">
          <input
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none"
            placeholder="New watchlist name (e.g. Banking, Dividend stocks)"
            maxLength={50}
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button
            type="submit"
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            Create watchlist
          </button>
        </form>

        {message.text && (
          <p className={`text-sm ${message.type === "error" ? "text-red-600" : "text-green-600"}`}>
            {message.text}
          </p>
        )}

        {chartTicker && (
          <PriceChart ticker={chartTicker} onClose={() => setChartTicker(null)} />
        )}

        {loading && <p className="text-gray-500">Loading...</p>}

        {watchlists.map((w) => (
          <div key={w.watchlist_id} className="rounded-xl bg-white p-6 shadow">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{w.name}</h3>
                <p className="text-sm text-gray-500">
                  {w.stocks.length} stock{w.stocks.length === 1 ? "" : "s"} · created{" "}
                  {new Date(w.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => deleteList(w)}
                className={`${btn} border-red-300 text-red-600 hover:bg-red-50`}
              >
                Delete watchlist
              </button>
            </div>

            {w.stocks.length === 0 ? (
              <p className="mt-4 text-sm text-gray-500">
                No stocks yet. Use the search bar on the Dashboard to add some.
              </p>
            ) : (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b text-gray-500">
                    <tr>
                      <th className="py-2 pr-4">Company</th>
                      <th className="py-2 pr-4">Ticker</th>
                      <th className="py-2 pr-4">Market</th>
                      <th className="py-2 pr-4">Date added</th>
                      <th className="py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {w.stocks.map((s) => (
                      <tr key={s.saved_stock_id}>
                        <td className="py-2 pr-4 font-medium text-gray-900">{s.company_name}</td>
                        <td className="py-2 pr-4">{s.ticker}</td>
                        <td className="py-2 pr-4">{s.market}</td>
                        <td className="py-2 pr-4">{new Date(s.created_at).toLocaleString()}</td>
                        <td className="py-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <button onClick={() => setChartTicker(s.ticker)} className={`${btn} border-gray-300 hover:bg-gray-50`}>
                              Chart
                            </button>
                            <button onClick={() => research(s.ticker)} className={`${btn} border-blue-600 bg-blue-600 text-white hover:bg-blue-700`}>
                              Research
                            </button>
                            {watchlists.length > 1 && (
                              <select
                                value=""
                                onChange={(e) => e.target.value && moveStock(s.saved_stock_id, e.target.value)}
                                className="rounded-lg border border-gray-300 bg-white px-2 py-1 text-sm"
                              >
                                <option value="">Move to...</option>
                                {watchlists
                                  .filter((o) => o.watchlist_id !== w.watchlist_id)
                                  .map((o) => (
                                    <option key={o.watchlist_id} value={o.watchlist_id}>{o.name}</option>
                                  ))}
                              </select>
                            )}
                            <button onClick={() => removeStock(s.saved_stock_id)} className={`${btn} border-red-300 text-red-600 hover:bg-red-50`}>
                              Remove
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
        ))}
      </main>
    </div>
  );
}