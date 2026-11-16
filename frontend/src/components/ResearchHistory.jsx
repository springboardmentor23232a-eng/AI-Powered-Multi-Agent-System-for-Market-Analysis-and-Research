import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import ReportModal from "./ReportModal.jsx";

const BADGE = {
  Pending: "bg-slate-100 text-slate-700",
  Processing: "bg-amber-100 text-amber-800",
  Completed: "bg-green-100 text-green-800",
  Failed: "bg-red-100 text-red-700",
};
const PERIOD_LABEL = { "1M": "1 Month", "3M": "3 Months", "6M": "6 Months", "1Y": "1 Year", "5Y": "5 Years" };

export default function ResearchHistory({ refreshKey }) {
  const [tasks, setTasks] = useState(null);
  const [error, setError] = useState("");
  const [openId, setOpenId] = useState(null);

  const load = useCallback(() => api("/research").then((t) => { setTasks(t); setError(""); }).catch((e) => setError(e.message)), []);
  useEffect(() => { load(); }, [load, refreshKey]);

  // While any task is Pending/Processing, poll so the status updates live
  const active = tasks?.some((t) => t.status === "Pending" || t.status === "Processing");
  useEffect(() => {
    if (!active) return;
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, [active, load]);

  return (
    <section className="card">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Research history</h2>
        <button className="btn-ghost !py-1 text-xs" onClick={load}>Refresh</button>
      </div>
      {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
      {tasks === null && !error && <p className="text-sm text-slate-500">Loading…</p>}
      {tasks?.length === 0 && <p className="text-sm text-slate-500">No research yet. Start one from the panel on the left or from your watchlist.</p>}
      {tasks?.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-xs uppercase text-slate-500">
              <tr><th className="py-2 pr-3">Company</th><th className="pr-3">Market</th><th className="pr-3">Period</th><th className="pr-3">Date</th><th className="pr-3">Status</th><th /></tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tasks.map((t) => (
                <tr key={t.task_id}>
                  <td className="py-2 pr-3"><div className="font-medium">{t.company_name}</div><div className="text-xs text-slate-500">{t.ticker}</div></td>
                  <td className="pr-3">{t.market}</td>
                  <td className="pr-3">{PERIOD_LABEL[t.analysis_period]}</td>
                  <td className="pr-3 whitespace-nowrap">{new Date(t.research_date).toLocaleString()}</td>
                  <td className="pr-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${BADGE[t.status]}`}>{t.status}</span>
                    {t.status === "Failed" && t.error_message && <div className="mt-1 max-w-[220px] text-xs text-red-600" title={t.error_message}>{t.error_message.slice(0, 80)}{t.error_message.length > 80 ? "…" : ""}</div>}
                  </td>
                  <td className="text-right">{t.report_available && <button className="btn-primary !px-2 !py-1 text-xs" onClick={() => setOpenId(t.task_id)}>Open report</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {openId && <ReportModal taskId={openId} onClose={() => setOpenId(null)} />}
    </section>
  );
}
