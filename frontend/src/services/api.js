const API_BASE_URL = "http://127.0.0.1:8000/api";

function getAuthHeader() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    "Content-Type": "application/json",
    ...getAuthHeader(),
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });
  
  if (response.status === 204) {
    return null;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.detail || response.statusText || "An unexpected error occurred";
    throw new Error(errorMsg);
  }

  return data;
}

export const api = {
  // Authentication
  register: (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  getMe: () => request("/auth/me"),

  // User Preferences
  getPreferences: () => request("/preferences"),
  updatePreferences: (payload) => request("/preferences", { method: "PUT", body: JSON.stringify(payload) }),

  // Watchlist & Stock Search
  getWatchlist: () => request("/watchlist"),
  addToWatchlist: (payload) => request("/watchlist", { method: "POST", body: JSON.stringify(payload) }),
  removeFromWatchlist: (stockId) => request(`/watchlist/${stockId}`, { method: "DELETE" }),
  searchStocks: (query, market) => {
    const params = new URLSearchParams({ q: query });
    if (market) params.append("market", market);
    return request(`/watchlist/search?${params.toString()}`);
  },

  // Research Tasks & Multi-Agent Reports
  getResearchTasks: () => request("/research/tasks"),
  startResearchTask: (payload) => request("/research/tasks", { method: "POST", body: JSON.stringify(payload) }),
  getTaskReport: (taskId) => request(`/research/tasks/${taskId}`),
};
