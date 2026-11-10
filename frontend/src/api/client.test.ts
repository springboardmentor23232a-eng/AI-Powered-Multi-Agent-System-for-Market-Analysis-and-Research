import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, setUnauthorizedHandler, tokenStore } from "./client";

const store = new Map<string, string>();

beforeEach(() => {
  store.clear();
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
    removeItem: (k: string) => void store.delete(k),
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  setUnauthorizedHandler(null);
});

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("api client", () => {
  it("sends the bearer token", async () => {
    tokenStore.set("abc");
    const fetchMock = vi.fn().mockResolvedValue(json([]));
    vi.stubGlobal("fetch", fetchMock);
    await api.history();
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer abc");
  });

  it("throws ApiError with the server detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(json({ detail: "Not in universe" }, 404)));
    await expect(api.startResearch("ZZZ")).rejects.toMatchObject({ status: 404, message: "Not in universe" });
    await expect(api.startResearch("ZZZ")).rejects.toBeInstanceOf(ApiError);
  });

  it("clears the token and notifies on 401", async () => {
    tokenStore.set("expired");
    const handler = vi.fn();
    setUnauthorizedHandler(handler);
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(json({ detail: "Invalid or expired token" }, 401)));
    await expect(api.history()).rejects.toBeInstanceOf(ApiError);
    expect(tokenStore.get()).toBeNull();
    expect(handler).toHaveBeenCalledOnce();
  });

  it("includes as_of only for replay requests", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(json({ task_id: "t" }, 202)));
    vi.stubGlobal("fetch", fetchMock);
    await api.startResearch("TCS");
    await api.startResearch("TCS", "2026-07-01");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ ticker: "TCS" });
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ ticker: "TCS", as_of: "2026-07-01" });
  });
});
