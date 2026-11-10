import type { Contradiction, Signal } from "../api/types";

export const MATRIX_AGENTS = ["fundamental", "technical", "news"] as const;
export type MatrixAgent = (typeof MATRIX_AGENTS)[number];

export type Cell =
  | { kind: "self"; signal: Signal | null }
  | { kind: "unknown" }
  | { kind: "aligned" }
  | { kind: "partial" }
  | { kind: "conflict"; severity: string; description: string };

/** Pairwise agreement between agents. Conflicts come from the backend's rule-based detector. */
export function buildMatrix(
  signals: Record<MatrixAgent, Signal | null>,
  contradictions: Contradiction[],
): Cell[][] {
  return MATRIX_AGENTS.map((row) =>
    MATRIX_AGENTS.map((col): Cell => {
      if (row === col) return { kind: "self", signal: signals[row] };
      const found = contradictions.find(
        (c) => (c.agent_a === row && c.agent_b === col) || (c.agent_a === col && c.agent_b === row),
      );
      if (found) return { kind: "conflict", severity: found.severity, description: found.description };
      const a = signals[row];
      const b = signals[col];
      if (a === null || b === null) return { kind: "unknown" };
      return a === b ? { kind: "aligned" } : { kind: "partial" };
    }),
  );
}
