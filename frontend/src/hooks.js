import { useEffect, useState } from "react";
import { api } from "./api";

// GET helper: refetches when `path` (or `nonce`) changes, ignores stale responses.
// `loading` is true from the very first render of a new request, so callers never see
// "not loading, but no data yet".
export function useApi(path, nonce = 0) {
  const key = path ? `${path}|${nonce}` : null;
  const [state, setState] = useState({ key: null, data: null, error: "" });
  useEffect(() => {
    if (!key) return;
    let cancelled = false;
    api(path)
      .then((data) => !cancelled && setState({ key, data, error: "" }))
      .catch((e) => !cancelled && setState({ key, data: null, error: e.message }));
    return () => {
      cancelled = true;
    };
  }, [path, key]);
  if (!key) return { data: null, error: "", loading: false };
  if (state.key !== key) return { data: null, error: "", loading: true };
  return { data: state.data, error: state.error, loading: false };
}

// Quote, history and profile of the stock being viewed. Fetched once and shared by
// the Stock search view and the Price chart view.
export function useStockData(active, range) {
  const enc = active ? encodeURIComponent(active.ticker) : null;
  const m = active?.market;
  const quote = useApi(active ? `/market/${enc}/quote?market=${m}` : null);
  const history = useApi(active ? `/market/${enc}/history?market=${m}&period=${range}` : null);
  const profile = useApi(active ? `/market/${enc}/profile?market=${m}` : null);
  return active ? { quote, history, profile } : null;
}
