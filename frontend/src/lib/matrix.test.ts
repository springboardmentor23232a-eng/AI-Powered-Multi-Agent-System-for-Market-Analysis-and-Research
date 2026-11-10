import { describe, expect, it } from "vitest";
import { buildMatrix } from "./matrix";

const signals = { fundamental: "bearish", technical: "bullish", news: null } as const;

describe("buildMatrix", () => {
  it("marks backend contradictions as conflicts in both directions", () => {
    const m = buildMatrix({ ...signals }, [
      { agent_a: "fundamental", agent_b: "technical", severity: "high", description: "x" },
    ]);
    expect(m[0][1]).toMatchObject({ kind: "conflict", severity: "high" });
    expect(m[1][0]).toMatchObject({ kind: "conflict", severity: "high" });
  });

  it("uses unknown when an agent has no signal and self cells carry the signal", () => {
    const m = buildMatrix({ ...signals }, []);
    expect(m[0][2]).toEqual({ kind: "unknown" });
    expect(m[1][1]).toEqual({ kind: "self", signal: "bullish" });
  });

  it("distinguishes aligned from partial agreement", () => {
    const m = buildMatrix({ fundamental: "bullish", technical: "bullish", news: "neutral" }, []);
    expect(m[0][1]).toEqual({ kind: "aligned" });
    expect(m[0][2]).toEqual({ kind: "partial" });
  });
});
