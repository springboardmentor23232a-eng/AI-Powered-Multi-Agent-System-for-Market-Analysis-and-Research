export const MARKETS = [
  { id: "NSE", full: "National Stock Exchange of India", hint: "TCS.NS, INFY.NS", example: "TCS.NS" },
  { id: "BSE", full: "BSE Ltd., India", hint: "500325.BO, TCS.BO", example: "500325.BO" },
  { id: "NASDAQ", full: "NASDAQ, US technology and growth", hint: "AAPL, MSFT, NVDA", example: "AAPL" },
  { id: "NYSE", full: "New York Stock Exchange", hint: "JPM, KO, XOM", example: "JPM" },
];

export const PERIODS = [
  { value: "1mo", short: "1M", label: "1 Month", note: "Short-term momentum" },
  { value: "3mo", short: "3M", label: "3 Months", note: "Quarterly outlook" },
  { value: "6mo", short: "6M", label: "6 Months", note: "Half-year trend" },
  { value: "1y", short: "1Y", label: "1 Year", note: "Annual trend" },
  { value: "5y", short: "5Y", label: "5 Years", note: "Long-term view" },
];

export const POPULAR = ["INFY.NS", "TCS.NS", "RELIANCE.NS", "AAPL", "MSFT", "NVDA"];
