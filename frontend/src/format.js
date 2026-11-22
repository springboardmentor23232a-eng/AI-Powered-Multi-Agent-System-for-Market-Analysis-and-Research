// Shows a timestamp from the backend in UTC, e.g. "19 Nov 2026, 14:32 UTC"
export function formatUtc(iso) {
  if (!iso) return "";
  return (
    new Date(iso).toLocaleString("en-GB", {
      timeZone: "UTC",
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }) + " UTC"
  );
}

const SYMBOLS = { INR: "₹", USD: "$" };

// "INR" -> "INR (₹)"
export function currencyLabel(code) {
  if (!code) return "";
  return SYMBOLS[code] ? `${code} (${SYMBOLS[code]})` : code;
}