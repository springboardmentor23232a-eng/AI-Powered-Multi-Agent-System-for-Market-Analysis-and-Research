import React, { createContext, useCallback, useContext, useState } from "react";
import { periodLabel } from "./api.js";

/* ---------- Toasts ---------- */
const ToastCtx = createContext(() => {});
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const push = useCallback((message, type = "success") => {
    const id = Math.random();
    setItems((s) => [...s, { id, message, type }]);
    setTimeout(() => setItems((s) => s.filter((t) => t.id !== id)), 3500);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {items.map((t) => (
          <div key={t.id} className={`animate-pop rounded-xl px-4 py-3 text-sm text-white shadow-lg ${t.type === "error" ? "bg-rose-600" : "bg-emerald-600"}`}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

/* ---------- Small pieces ---------- */
export const Spinner = ({ className = "h-4 w-4" }) => (
  <span className={`inline-block animate-spin rounded-full border-2 border-current border-t-transparent ${className}`} />
);

const BADGE = {
  Pending: "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300",
  Processing: "bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300",
  Completed: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-300",
  Failed: "bg-rose-100 text-rose-700 dark:bg-rose-500/20 dark:text-rose-300",
};
export function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${BADGE[status]}`}>
      {status === "Processing" && <Spinner className="h-3 w-3" />}
      {status}
    </span>
  );
}

export function Modal({ onClose, children }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div className="animate-pop max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );
}

export const fmtDate = (iso) =>
  new Date(iso).toLocaleString(undefined, { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

/* ---------- Price chart (pure SVG, hover tooltip) ---------- */
function PriceChart({ prices }) {
  const [hover, setHover] = useState(null);
  const W = 640, H = 220, P = 10;
  const ys = prices.map((p) => p.price);
  const min = Math.min(...ys), max = Math.max(...ys);
  const x = (i) => P + (i / (prices.length - 1)) * (W - 2 * P);
  const y = (v) => H - P - ((v - min) / (max - min || 1)) * (H - 2 * P);
  const line = prices.map((p, i) => `${x(i)},${y(p.price)}`).join(" ");
  const up = ys[ys.length - 1] >= ys[0];
  const color = up ? "#10b981" : "#f43f5e";
  const onMove = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    const rel = (e.clientX - r.left) / r.width;
    setHover(Math.max(0, Math.min(prices.length - 1, Math.round(rel * (prices.length - 1)))));
  };
  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
        <polygon points={`${P},${H - P} ${line} ${W - P},${H - P}`} fill={color} opacity="0.12" />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
        {hover !== null && (
          <>
            <line x1={x(hover)} x2={x(hover)} y1={P} y2={H - P} stroke="currentColor" opacity="0.25" />
            <circle cx={x(hover)} cy={y(prices[hover].price)} r="4" fill={color} />
          </>
        )}
      </svg>
      {hover !== null && (
        <div className="absolute right-2 top-2 rounded-lg bg-slate-900 px-2 py-1 text-xs text-white">
          {prices[hover].price.toFixed(2)}
        </div>
      )}
    </div>
  );
}

/* ---------- Report ---------- */
export function ReportView({ task, onClose }) {
  const r = task.report;
  const m = r?.metrics;
  const tone = { Bullish: "text-emerald-600", Bearish: "text-rose-600", Neutral: "text-slate-500" };
  return (
    <Modal onClose={onClose}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">{task.company_name} <span className="text-slate-400">({task.ticker})</span></h2>
          <p className="text-sm text-slate-500">{task.market} · {periodLabel(task.analysis_period)} · {fmtDate(task.created_at)}</p>
        </div>
        <button className="btn-ghost" onClick={onClose}>Close</button>
      </div>
      {task.status === "Failed" && <p className="rounded-xl bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-500/10">{task.error || "The analysis failed."}</p>}
      {!r && task.status !== "Failed" && <p className="flex items-center gap-2 text-sm text-slate-500"><Spinner /> The agents are still working on this report…</p>}
      {r && (
        <div className="space-y-5">
          <p className="text-lg">{r.headline} <span className={`font-semibold ${tone[r.outlook]}`}>{r.outlook}</span></p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[["Last price", m.last_price], ["Change", `${m.period_change_pct}%`], ["High", m.high], ["Low", m.low], ["Volatility", `${m.annualised_volatility_pct}%`]].map(([k, v]) => (
              <div key={k} className="rounded-xl bg-slate-100 p-3 dark:bg-slate-800"><div className="text-xs text-slate-500">{k}</div><div className="font-semibold">{v}</div></div>
            ))}
          </div>
          <PriceChart prices={r.prices} />
          <div className="grid gap-3 sm:grid-cols-2">
            {r.agents.map((a) => (
              <div key={a.name} className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
                <div className="text-sm font-semibold">{a.name}</div>
                <p className="text-sm text-slate-600 dark:text-slate-400">{a.result}</p>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-400">{r.disclaimer}</p>
        </div>
      )}
    </Modal>
  );
}
