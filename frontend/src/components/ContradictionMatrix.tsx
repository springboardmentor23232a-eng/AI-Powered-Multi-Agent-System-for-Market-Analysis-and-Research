import type { Contradiction, Signal } from "../api/types";
import { buildMatrix, MATRIX_AGENTS, type Cell, type MatrixAgent } from "../lib/matrix";
import { SignalPill } from "./Badges";

const TONE = { high: "bg-red-100 border-red-300 text-red-900", medium: "bg-amber-100 border-amber-300 text-amber-900" } as const;

function CellView({ cell }: { cell: Cell }) {
  switch (cell.kind) {
    case "self":
      return <SignalPill signal={cell.signal} />;
    case "unknown":
      return <span className="text-xs text-slate-400">unavailable</span>;
    case "aligned":
      return <span className="text-xs text-emerald-700">aligned</span>;
    case "partial":
      return <span className="text-xs text-slate-500">differs (no conflict)</span>;
    case "conflict":
      return <span className="text-xs font-medium">{cell.description}</span>;
  }
}

export function ContradictionMatrix({ signals, contradictions }: {
  signals: Record<MatrixAgent, Signal | null>;
  contradictions: Contradiction[];
}) {
  const matrix = buildMatrix(signals, contradictions);
  return (
    <section aria-label="Contradiction matrix">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">Contradiction matrix</h3>
      <div className="overflow-x-auto">
        <table className="w-full border-separate border-spacing-1 text-left">
          <thead>
            <tr>
              <th />
              {MATRIX_AGENTS.map((a) => <th key={a} className="px-2 text-xs font-medium capitalize text-slate-500">{a}</th>)}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={MATRIX_AGENTS[i]}>
                <th className="pr-2 text-xs font-medium capitalize text-slate-500">{MATRIX_AGENTS[i]}</th>
                {row.map((cell, j) => {
                  const tone = cell.kind === "conflict" ? (TONE[cell.severity as keyof typeof TONE] ?? TONE.medium) : "bg-white border-slate-200";
                  return <td key={j} className={`min-w-28 rounded border px-2 py-2 align-top ${tone}`}><CellView cell={cell} /></td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {contradictions.length === 0 && <p className="mt-2 text-xs text-slate-500">No contradictions detected between the available analyses.</p>}
    </section>
  );
}
