// Thin fetch wrapper. The JWT lives in an HTTP-only cookie (JS can't read it); we send it with
// credentials: "include" and add the CSRF token header on state-changing requests.
let csrfToken = null;
let onUnauthorized = () => {};

export const setCsrfToken = (t) => { csrfToken = t; };
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn; };

export class ApiError extends Error {
  constructor(message, status, errors) { super(message); this.status = status; this.errors = errors || {}; }
}

export async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (csrfToken && method !== "GET") headers["X-CSRF-Token"] = csrfToken;
  let res;
  try {
    res = await fetch(`/api${path}`, { method, headers, credentials: "include", body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    throw new ApiError("Cannot reach the server. Please check your connection and try again.", 0);
  }
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = typeof data.detail === "string" ? data.detail : "Something went wrong. Please try again.";
    // missing / invalid / expired token on a protected call -> ask the user to sign in again
    if (res.status === 401 && auth) onUnauthorized(msg);
    throw new ApiError(msg, res.status, data.errors);
  }
  return data;
}
