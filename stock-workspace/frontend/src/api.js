// All calls go to /api (proxied to FastAPI). The JWT lives in an HTTP-only cookie,
// so JavaScript never sees the token. The custom header is our CSRF protection.
async function request(path, { method = "GET", body } = {}) {
  const res = await fetch("/api" + path, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-Requested-With": "XMLHttpRequest" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    let msg = "Something went wrong";
    if (typeof data.detail === "string") msg = data.detail;
    else if (Array.isArray(data.detail)) msg = (data.detail[0]?.msg || msg).replace(/^Value error, /, "");
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  register: (b) => request("/auth/register", { method: "POST", body: b }),
  login: (b) => request("/auth/login", { method: "POST", body: b }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/auth/me"),
  savePrefs: (b) => request("/preferences", { method: "PUT", body: b }),
  search: (q, market) => request(`/stocks/search?q=${encodeURIComponent(q)}&market=${market}`),
  watchlist: () => request("/watchlist"),
  addWatch: (b) => request("/watchlist", { method: "POST", body: b }),
  removeWatch: (id) => request(`/watchlist/${id}`, { method: "DELETE" }),
  tasks: () => request("/research"),
  startResearch: (b) => request("/research", { method: "POST", body: b }),
  task: (id) => request(`/research/${id}`),
};

export const MARKETS = [
  { id: "NSE", label: "NSE", desc: "National Stock Exchange of India" },
  { id: "BSE", label: "BSE", desc: "BSE Ltd., India" },
  { id: "NASDAQ", label: "NASDAQ", desc: "US stock exchange" },
  { id: "NYSE", label: "NYSE", desc: "New York Stock Exchange" },
];
export const PERIODS = [
  { id: "1M", label: "1 Month" }, { id: "3M", label: "3 Months" }, { id: "6M", label: "6 Months" },
  { id: "1Y", label: "1 Year" }, { id: "5Y", label: "5 Years" },
];
export const periodLabel = (id) => PERIODS.find((p) => p.id === id)?.label || id;
