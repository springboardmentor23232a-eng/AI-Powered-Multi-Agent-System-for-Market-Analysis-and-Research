import type {
  AgentName, AgentOutput, Claim, Contradiction, Preferences, SearchHit, TaskDetail, TaskSummary, WatchItem,
} from "./types";

const BASE: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const KEY = "veritas_token";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export const tokenStore = {
  get: (): string | null => globalThis.localStorage?.getItem(KEY) ?? null,
  set: (t: string) => globalThis.localStorage?.setItem(KEY, t),
  clear: () => globalThis.localStorage?.removeItem(KEY),
};

let onUnauthorized: (() => void) | null = null;
export const setUnauthorizedHandler = (fn: (() => void) | null) => {
  onUnauthorized = fn;
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch {
      /* keep statusText */
    }
    if (res.status === 401 && token) {
      tokenStore.clear();
      onUnauthorized?.();
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

const post = <T,>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  register: (email: string, password: string, full_name?: string, confirm_password?: string) =>
    post<{ access_token: string }>("/auth/register", {
      email,
      password,
      ...(full_name ? { full_name } : {}),
      ...(confirm_password ? { confirm_password } : {}),
    }),
  login: (email: string, password: string) => post<{ access_token: string }>("/auth/login", { email, password }),
  search: (q: string) => request<{ results: SearchHit[] }>(`/stocks/search?q=${encodeURIComponent(q)}`),
  startResearch: (ticker: string, asOf?: string) =>
    post<TaskSummary>("/research", { ticker, ...(asOf ? { as_of: asOf } : {}) }),
  history: () => request<TaskSummary[]>("/research"),
  detail: (id: string) => request<TaskDetail>(`/research/${id}`),
  agent: <T,>(id: string, name: AgentName) => request<AgentOutput<T>>(`/research/${id}/agents/${name}`),
  claims: (id: string) => request<Claim[]>(`/research/${id}/claims`),
  contradictions: (id: string) => request<Contradiction[]>(`/research/${id}/contradictions`),
  report: (id: string) => request<{ content: string; summary: string }>(`/research/${id}/report`),
  watchlist: () => request<WatchItem[]>("/watchlist"),
  watch: (ticker: string) => post<WatchItem>("/watchlist", { ticker }),
  unwatch: (ticker: string) => request<void>(`/watchlist/${ticker}`, { method: "DELETE" }),
  preferences: () => request<Preferences>("/preferences"),
  setPreferences: (p: Preferences) => request<Preferences>("/preferences", { method: "PUT", body: JSON.stringify(p) }),
};

export async function downloadReport(id: string, ticker: string): Promise<void> {
  const token = tokenStore.get();
  const res = await fetch(`${BASE}/research/${id}/report?format=md`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new ApiError(res.status, "Report download failed");
  const url = URL.createObjectURL(await res.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = `${ticker}_research_report.md`;
  a.click();
  URL.revokeObjectURL(url);
}
