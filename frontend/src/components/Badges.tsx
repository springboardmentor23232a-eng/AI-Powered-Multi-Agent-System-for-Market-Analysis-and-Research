import type { Claim, Signal, TaskStatus } from "../api/types";

const STATUS: Record<string, string> = {
  queued: "bg-slate-100 text-slate-700",
  running: "bg-blue-100 text-blue-800",
  completed: "bg-emerald-100 text-emerald-800",
  partial: "bg-amber-100 text-amber-800",
  failed: "bg-red-100 text-red-800",
  success: "bg-emerald-100 text-emerald-800",
  unavailable: "bg-amber-100 text-amber-800",
};

export function StatusPill({ status }: { status: TaskStatus | string }) {
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS[status] ?? STATUS.queued}`}>{status}</span>;
}

const SIGNAL: Record<Signal, string> = {
  bullish: "bg-emerald-100 text-emerald-800",
  bearish: "bg-red-100 text-red-800",
  neutral: "bg-slate-100 text-slate-700",
};

export function SignalPill({ signal }: { signal: Signal | null | undefined }) {
  if (!signal) return <span className="text-xs text-slate-400">no signal</span>;
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${SIGNAL[signal]}`}>{signal}</span>;
}

const CLAIM: Record<Claim["type"], { label: string; cls: string }> = {
  FACT: { label: "FACT", cls: "bg-blue-100 text-blue-800" },
  CALCULATED: { label: "CALC", cls: "bg-violet-100 text-violet-800" },
  INTERPRETATION: { label: "AI", cls: "bg-amber-100 text-amber-800" },
};

export function ClaimTag({ type }: { type: Claim["type"] }) {
  const c = CLAIM[type];
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${c.cls}`}>{c.label}</span>;
}

export function EvidenceBadge({ verified, total, percent }: { verified: number; total: number; percent: number }) {
  const tone = percent >= 95 ? "border-emerald-300 bg-emerald-50 text-emerald-800" : "border-amber-300 bg-amber-50 text-amber-800";
  return (
    <div className={`inline-flex items-baseline gap-2 rounded-lg border px-3 py-1.5 ${tone}`} title="Claims verified against sources or recomputed by tools">
      <span className="text-xs font-medium uppercase tracking-wide">Evidence</span>
      <span className="text-lg font-semibold">{percent}%</span>
      <span className="text-xs">{verified}/{total} claims verified</span>
    </div>
  );
}
