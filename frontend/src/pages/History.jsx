import { useEffect, useState } from "react";
import { api } from "../api";

const STATUS = { pending: "Pending", processing: "Processing", completed: "Completed", failed: "Failed" };

export default function History({ refreshKey }) {
  const [tasks, setTasks] = useState([]);
  const [report, setReport] = useState(null);
  const [msg, setMsg] = useState("");

  const load = () => api("/research").then(setTasks).catch((e) => setMsg(e.message));

  useEffect(() => { load(); }, [refreshKey]);

  useEffect(() => {
    if (!tasks.some((t) => t.status === "pending" || t.status === "processing")) return;
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, [tasks]);

  const open = async (id) => {
    try { setReport(await api(`/research/${id}`)); }
    catch (e) { setMsg(e.message); }
  };

  return (
    <section>
      <h3>Research History</h3>
      {msg && <p>{msg}</p>}
      {tasks.length === 0 ? <p>No research yet.</p> : (
        <table border="1" cellPadding="6">
          <thead>
            <tr><th>Company</th><th>Ticker</th><th>Market</th><th>Period</th><th>Date</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.task_id}>
                <td>{t.company_name || "-"}</td>
                <td>{t.ticker}</td>
                <td>{t.market}</td>
                <td>{t.requested_period}</td>
                <td>{new Date(t.created_at).toLocaleString()}</td>
                <td>{STATUS[t.status] || t.status}</td>
                <td>{t.status === "completed" && <button onClick={() => open(t.task_id)}>Open report</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {report?.report && (
        <div style={{ marginTop: 16, padding: 12, border: "1px solid #888" }}>
          <button onClick={() => setReport(null)}>Close</button>
          <pre style={{ whiteSpace: "pre-wrap" }}>{report.report.report_content}</pre>
          <small>Limitations: {report.report.limitations}</small>
        </div>
      )}
    </section>
  );
}