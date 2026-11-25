export const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function api(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include", // httpOnly JWT cookie
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    const msg = Array.isArray(d)
      ? d.map((e) => e.msg.replace("Value error, ", "")).join(", ")
      : d || "Something went wrong";
    throw new Error(msg);
  }
  return data;
}
