import { describe, expect, it } from "vitest";
import { isTerminal, num, pct, shortDate } from "./format";

describe("format helpers", () => {
  it("formats percentages and handles missing values", () => {
    expect(pct(0.1234)).toBe("12.3%");
    expect(pct(null)).toBe("n/a");
    expect(num(undefined)).toBe("n/a");
  });
  it("formats dates and status", () => {
    expect(shortDate("2026-11-02T10:00:00Z")).toBe("2026-11-02");
    expect(shortDate(null)).toBe("undated");
    expect(isTerminal("running")).toBe(false);
    expect(isTerminal("partial")).toBe(true);
  });
});
