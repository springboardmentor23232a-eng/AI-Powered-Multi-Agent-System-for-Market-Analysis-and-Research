import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

export default function PriceChart({ ticker, period, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setData(null);
    api
      .get(`/stocks/${ticker}/history`, { params: { period } })
      .then((res) => !cancelled && setData(res.data))
      .catch((err) => !cancelled && setError(errorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [ticker, period]);

  const W = 600, H = 220, PAD = 28;
  let chart = null;
  if (data && data.points.length > 1) {
    const closes = data.points.map((p) => p.close);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const x = (i) => PAD + (i / (closes.length - 1)) * (W - 2 * PAD);
    const y = (v) => H - PAD - ((v - min) / (max - min || 1)) * (H - 2 * PAD);
    const path = closes
      .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
      .join(" ");
    const first = closes[0];
    const last = closes[closes.length - 1];
    const change = ((last - first) / first) * 100;
    chart = { path, min, max, last, change, start: data.points[0].date, end: data.points[data.points.length - 1].date };
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold text-gray-900">
            {data ? `${data.name} (${data.ticker})` : ticker} · price history ({period})
          </h3>
          {chart && (
            <p className="mt-1 text-sm text-gray-600">
              Last close {chart.last} ·{" "}
              <span className={chart.change >= 0 ? "text-green-600" : "text-red-600"}>
                {chart.change >= 0 ? "+" : ""}{chart.change.toFixed(2)}%
              </span>{" "}
              over the period
            </p>
          )}
        </div>
        <button onClick={onClose} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50">
          Close
        </button>
      </div>

      {loading && <p className="mt-4 text-sm text-gray-500">Loading price data from Yahoo Finance...</p>}
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {chart && (
        <>
          <svg viewBox={`0 0 ${W} ${H}`} className="mt-4 w-full text-blue-600">
            <path d={chart.path} fill="none" stroke="currentColor" strokeWidth="2" />
            <text x={PAD} y={14} fontSize="11" fill="#6b7280">High {chart.max}</text>
            <text x={PAD} y={H - 6} fontSize="11" fill="#6b7280">Low {chart.min}</text>
          </svg>
          <div className="flex justify-between text-xs text-gray-500">
            <span>{chart.start}</span>
            <span>{chart.end}</span>
          </div>
        </>
      )}
    </div>
  );
}