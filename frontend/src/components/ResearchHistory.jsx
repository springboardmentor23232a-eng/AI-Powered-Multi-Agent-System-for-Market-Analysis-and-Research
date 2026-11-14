import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

const STATUS_STYLES = {
  Pending: "bg-yellow-100 text-yellow-800",
  Processing: "bg-blue-100 text-blue-800",
  Completed: "bg-green-100 text-green-800",
  Failed: "bg-red-100 text-red-800",
};

export default function ResearchHistory({ refreshKey }) {
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get("/research")
      .then((res) => setTasks(res.data))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false));
  }, [refreshKey]);

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <h3 className="font-semibold text-gray-900">Research History</h3>

      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      {loading && <p className="mt-3 text-sm text-gray-500">Loading...</p>}

      {!loading && !error && tasks.length === 0 && (
        <p className="mt-3 text-sm text-gray-500">
          No research yet. Save a stock to your watchlist and click Research.
        </p>
      )}

      {tasks.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-gray-500">
              <tr>
                <th className="py-2 pr-4">Company</th>
                <th className="py-2 pr-4">Ticker</th>
                <th className="py-2 pr-4">Market</th>
                <th className="py-2 pr-4">Period</th>
                <th className="py-2 pr-4">Date</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {tasks.map((t) => (
                <tr key={t.task_id}>
                  <td className="py-2 pr-4 font-medium text-gray-900">{t.company_name}</td>
                  <td className="py-2 pr-4">{t.ticker}</td>
                  <td className="py-2 pr-4">{t.market}</td>
                  <td className="py-2 pr-4">{t.analysis_period}</td>
                  <td className="py-2 pr-4">{new Date(t.created_at).toLocaleString()}</td>
                  <td className="py-2 pr-4">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[t.status] || ""}`}>
                      {t.status}
                    </span>
                  </td>
                  <td className="py-2">
                    {t.status === "Completed" ? (
                      <button className="text-blue-600 hover:underline">View report</button>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}