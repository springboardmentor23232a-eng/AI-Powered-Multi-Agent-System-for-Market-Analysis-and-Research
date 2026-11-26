import { useEffect, useState } from "react";
import { api } from "../api.js";

const fmt = (n, c = "") => (n == null ? "—" : `${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })} ${c}`.trim());

function Sparkline({ points }) {
  if (!points?.length) return null;
  const vals = points.map((p) => p.close), min = Math.min(...vals), max = Math.max(...vals);
  const w = 600, h = 120;
  const d = vals.map((v, i) => `${i ? "L" : "M"}${(i / (vals.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * h}`).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="h-32 w-full" preserveAspectRatio="none" role="img" aria-label="Closing price chart">
      <path d={d} fill="none" stroke="#2f5fe0" strokeWidth="2" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

export default function ReportModal({ taskId, onClose }) {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { api(`/research/${taskId}/report`).then(setReport).catch((e) => setError(e.message)); }, [taskId]);
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const s = report?.content.statistics;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4" onClick={onClose} role="dialog" aria-modal="true">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="mb-3 flex items-start justify-between gap-4">
          <h2 className="text-lg font-semibold">{report?.title || "Report"}</h2>
          <button className="btn-ghost !px-2 !py-1" onClick={onClose} aria-label="Close">✕</button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        {!report && !error && <p className="text-sm text-slate-500">Loading report…</p>}
        {report && (
          <div className="space-y-4">
            <p className="text-sm">{report.summary}</p>
            <Sparkline points={report.content.price_history} />
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {[["Latest price", fmt(s.latest_price, s.currency)], ["Period return", `${s.period_return_pct}%`], ["Period high", fmt(s.period_high, s.currency)],
                ["Period low", fmt(s.period_low, s.currency)], ["Volatility (ann.)", `${s.annualised_volatility_pct}%`], ["20-day SMA", fmt(s.sma_20, s.currency)]].map(([k, v]) => (
                <div key={k} className="rounded-lg bg-slate-50 p-3"><div className="text-xs text-slate-500">{k}</div><div className="font-semibold">{v}</div></div>
              ))}
            </div>
            <p className="text-xs text-slate-500">Source: {report.content.data_source} · {s.start_date} → {s.end_date} · {s.data_points} data points</p>
            <p className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">{report.content.note} Not investment advice.</p>
          </div>
        )}
      </div>
    </div>
  );
}
