import React from 'react';
import { ShieldCheck } from 'lucide-react';

/**
 * TelemetryHealthPanel
 * Research intelligence and circular SVG telemetry gauge panel.
 */
export default function TelemetryHealthPanel({ validation, overview }) {
  if (!validation) return null;

  const total = validation.total_raw_records || 1;
  const clean = validation.cleaned_records || 0;
  const cleanPct = Math.min(Math.round((clean / total) * 100), 100);

  // SVG circular gauge
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (cleanPct / 100) * circumference;

  return (
    <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between gap-5">
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-rose-500" />
            <h3 className="text-sm font-bold text-white tracking-tight uppercase">
              Pipeline Health & Telemetry
            </h3>
          </div>
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-800/60">
            Verified
          </span>
        </div>

        {/* Circular Donut Gauge & Summary */}
        <div className="flex items-center gap-5 mt-4">
          <div className="relative flex items-center justify-center shrink-0">
            <svg width="94" height="94" className="rotate-[-90deg]">
              <circle
                cx="47"
                cy="47"
                r={radius}
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="7"
                fill="none"
              />
              <circle
                cx="47"
                cy="47"
                r={radius}
                stroke="#e11d48"
                strokeWidth="7"
                fill="none"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                strokeLinecap="round"
                className="transition-all duration-700 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="font-mono text-base font-extrabold text-white leading-none">
                {cleanPct}%
              </span>
              <span className="text-[9px] font-mono text-zinc-400 uppercase mt-0.5">Integrity</span>
            </div>
          </div>

          <div className="flex-1 space-y-1.5 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> Clean Records
              </span>
              <span className="font-mono font-bold text-white">{validation.cleaned_records}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500" /> Duplicates Filtered
              </span>
              <span className="font-mono font-bold text-zinc-300">{validation.duplicates_removed}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-400 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400" /> Raw Ingested
              </span>
              <span className="font-mono font-bold text-zinc-300">{validation.total_raw_records}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Profile & Metadata tags */}
      <div className="pt-3 border-t border-white/[0.06] flex flex-col gap-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
          <span className="text-zinc-500">Order:</span>
          <span className="font-bold text-emerald-400">
            {validation.is_chronological ? 'Strict Chronological (Asc)' : 'Reordered'}
          </span>
        </div>
        {overview && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white/[0.04] text-zinc-300 border border-white/[0.08]">
              {overview.sector}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/20">
              {overview.currency}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-white/[0.04] text-zinc-300 border border-white/[0.08]">
              {overview.exchange}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
