const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getCookie(name) {
  const row = document.cookie
    .split("; ")
    .find((item) => item.startsWith(`${name}=`));

  return row ? decodeURIComponent(row.substring(name.length + 1)) : "";
}

async function request(path, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = { ...(options.headers || {}) };

  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = getCookie("csrf_token");
    if (csrf) headers["X-CSRF-Token"] = csrf;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    method,
    headers,
    credentials: "include"
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new Event("session-expired"));
    }
    throw new Error(data.detail || `Request failed (${response.status})`);
  }

  return data;
}

export const api = {
  register: (body) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(body)
    }),

  login: (body) =>
    request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(body)
    }),

  me: () => request("/api/auth/me"),
  logout: () =>
    request("/api/auth/logout", {
      method: "POST",
      body: JSON.stringify({})
    }),

  getWatchlist: () => request("/api/watchlist"),
  searchStocks: (query, market) =>
    request(`/api/stocks/search?q=${encodeURIComponent(query)}&market=${encodeURIComponent(market)}`),
  addStock: (stock) =>
    request("/api/watchlist", {
      method: "POST",
      body: JSON.stringify(stock)
    }),
  removeStock: (id) =>
    request(`/api/watchlist/${id}`, { method: "DELETE" }),

  getPreferences: () => request("/api/preferences"),
  savePreferences: (preferences) =>
    request("/api/preferences", {
      method: "PUT",
      body: JSON.stringify(preferences)
    }),

  getTasks: () => request("/api/research-tasks"),
  createTask: (task) =>
    request("/api/research-tasks", {
      method: "POST",
      body: JSON.stringify(task)
    }),
  getReport: (taskId) =>
    request(`/api/research-tasks/${taskId}/report`),

  googleLoginUrl: `${API_URL}/api/auth/google/login`
};
