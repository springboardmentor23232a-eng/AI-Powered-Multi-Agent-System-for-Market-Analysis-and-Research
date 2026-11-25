const SYMBOL = { USD: "$", INR: "₹", EUR: "€", GBP: "£", JPY: "¥" };
const sym = (cur) => SYMBOL[cur] ?? "";

export function money(v, cur = "USD", digits = 2) {
  if (v == null) return "—";
  const locale = cur === "INR" ? "en-IN" : "en-US";
  return `${sym(cur)}${Number(v).toLocaleString(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

export function compact(v, cur, withSymbol = true) {
  if (v == null) return "—";
  const s = withSymbol ? sym(cur) : "";
  const a = Math.abs(v);
  const sign = v < 0 ? "-" : "";
  if (a >= 1e12) return `${sign}${s}${(a / 1e12).toFixed(2)}T`;
  if (a >= 1e9) return `${sign}${s}${(a / 1e9).toFixed(2)}B`;
  if (a >= 1e6) return `${sign}${s}${(a / 1e6).toFixed(2)}M`;
  if (a >= 1e3) return `${sign}${s}${(a / 1e3).toFixed(2)}K`;
  return `${sign}${s}${a.toFixed(2)}`;
}

// Statement cells: counts and ratios must not get a currency symbol.
export function formatCell(item, v, cur) {
  if (v == null) return "—";
  if (/shares|number|count/i.test(item)) return compact(v, cur, false);
  if (/rate/i.test(item) && Math.abs(v) <= 1) return `${(v * 100).toFixed(2)}%`;
  return compact(v, cur);
}

export const pct = (v, d = 2) => (v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(d)}%`);
export const int = (v) => (v == null ? "—" : Number(v).toLocaleString("en-US"));
export const num = (v, d = 2) => (v == null ? "—" : Number(v).toFixed(d));

// The API sends naive UTC timestamps when the DB is SQLite; treat them as UTC.
export function parseUtc(s) {
  if (!s) return null;
  return new Date(/Z|[+-]\d\d:?\d\d$/.test(s) ? s : `${s}Z`);
}
export const dateOf = (s) => parseUtc(s)?.toLocaleDateString() ?? "—";
export const dateTimeOf = (s) => parseUtc(s)?.toLocaleString() ?? "—";

export function marketFromTicker(t) {
  if (t.endsWith(".NS")) return "NSE";
  if (t.endsWith(".BO")) return "BSE";
  return "NASDAQ";
}
