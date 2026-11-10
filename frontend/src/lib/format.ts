export const pct = (x: number | null | undefined, digits = 1): string =>
  x === null || x === undefined ? "n/a" : `${(x * 100).toFixed(digits)}%`;

export const num = (x: number | null | undefined, digits = 2): string =>
  x === null || x === undefined ? "n/a" : x.toLocaleString("en-IN", { maximumFractionDigits: digits, minimumFractionDigits: digits });

export const shortDate = (iso: string | null | undefined): string => (iso ? iso.slice(0, 10) : "undated");

export const isTerminal = (status: string): boolean => !["queued", "running"].includes(status);
