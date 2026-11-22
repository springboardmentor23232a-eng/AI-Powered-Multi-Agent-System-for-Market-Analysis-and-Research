import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { currencyLabel, formatUtc } from "../format";

const W = 700;
const PADL = 56;
const PADR = 12;
const PRICE_TOP = 10;
const PRICE_H = 230;
const VOL_TOP = 258;
const VOL_H = 64;
const H = 346;

const UP = "#16a34a";
const DOWN = "#dc2626";
const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });

export default function PriceChart({ ticker, period, onClose }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState("candles");
  const [hover, setHover] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    setData(null);
    setHover(null);
    api
      .get(`/stocks/${ticker}/history`, { params: { period } })
      .then((res) => !cancelled && setData(res.data))
      .catch((err) => !cancelled && setError(errorMessage(err)))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [ticker, period]);

  // Work out all the chart geometry once the data has arrived
  let view = null;
  if (data && data.points.length > 1) {
    const pts = data.points;
    const n = pts.length;
    const step = (W - PADL - PADR) / n; // horizontal slot per candle
    const lo = Math.min(...pts.map((p) => p.low));
    const hi = Math.max(...pts.map((p) => p.high));
    const pad = (hi - lo) * 0.05 || 1;
    const minP = lo - pad;
    const maxP = hi + pad;
    const maxVol = Math.max(...pts.map((p) => p.volume)) || 1;
    view = {
      pts,
      n,
      step,
      lo,
      hi,
      maxVol,
      cx: (i) => PADL + step * i + step / 2,
      yP: (v) => PRICE_TOP + (1 - (v - minP) / (maxP - minP)) * PRICE_H,
      yV: (v) => VOL_TOP + VOL_H - (v / maxVol) * VOL_H,
      ticks: [0, 1, 2, 3].map((k) => minP + ((maxP - minP) * k) / 3),
      bodyW: Math.max(1, Math.min(10, step * 0.7)),
      change: ((pts[n - 1].close - pts[0].close) / pts[0].close) * 100,
      avgVol: pts.reduce((s, p) => s + p.volume, 0) / n,
    };
  }

  const active = view ? view.pts[hover ?? view.n - 1] : null;

  const onMove = (e) => {
    if (!view) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * W;
    const i = Math.floor((x - PADL) / view.step);
    setHover(i >= 0 && i < view.n ? i : null);
  };

  const toggle = (m) =>
    `rounded-lg border px-3 py-1 text-sm ${
      mode === m ? "border-blue-600 bg-blue-600 text-white" : "border-gray-300 hover:bg-gray-50"
    }`;

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-semibold text-gray-900">
            {data ? `${data.name} (${data.ticker})` : ticker} · price history
            {data ? ` (${data.period})` : ""}
          </h3>
          {data?.currency && (
            <p className="mt-0.5 text-xs text-gray-500">
              Prices in {currencyLabel(data.currency)} · {data.market}
            </p>
          )}
          {view && (
            <p className="mt-1 text-sm text-gray-600">
              Last close {view.pts[view.n - 1].close} ·{" "}
              <span className={view.change >= 0 ? "text-green-600" : "text-red-600"}>
                {view.change >= 0 ? "+" : ""}
                {view.change.toFixed(2)}%
              </span>{" "}
              over the period · High {view.hi} · Low {view.lo} · Avg volume{" "}
              {compact.format(view.avgVol)}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button onClick={() => setMode("candles")} className={toggle("candles")}>Candles</button>
          <button onClick={() => setMode("line")} className={toggle("line")}>Line</button>
          <button onClick={onClose} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50">
            Close
          </button>
        </div>
      </div>

      {loading && <p className="mt-4 text-sm text-gray-500">Loading price data from Yahoo Finance...</p>}
      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {data && !view && (
        <p className="mt-4 text-sm text-gray-500">Not enough data points to draw a chart.</p>
      )}

      {view && (
        <>
          <p className="mt-3 text-sm text-gray-700">
            <span className="font-medium">{active.date}</span> · Open {active.open} · High{" "}
            {active.high} · Low {active.low} · Close {active.close} · Volume{" "}
            {active.volume.toLocaleString()}
          </p>

          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="mt-2 w-full"
            onMouseMove={onMove}
            onMouseLeave={() => setHover(null)}
          >
            {/* price grid and labels */}
            {view.ticks.map((t, k) => (
              <g key={k}>
                <line x1={PADL} x2={W - PADR} y1={view.yP(t)} y2={view.yP(t)} stroke="#e5e7eb" />
                <text x={PADL - 6} y={view.yP(t) + 3} fontSize="10" textAnchor="end" fill="#6b7280">
                  {t.toFixed(2)}
                </text>
              </g>
            ))}

            {/* candles or line */}
            {mode === "candles" ? (
              view.pts.map((p, i) => {
                const color = p.close >= p.open ? UP : DOWN;
                const x = view.cx(i);
                const top = view.yP(Math.max(p.open, p.close));
                const bottom = view.yP(Math.min(p.open, p.close));
                return (
                  <g key={p.date}>
                    <line x1={x} x2={x} y1={view.yP(p.high)} y2={view.yP(p.low)} stroke={color} />
                    <rect
                      x={x - view.bodyW / 2}
                      y={top}
                      width={view.bodyW}
                      height={Math.max(1, bottom - top)}
                      fill={color}
                    />
                  </g>
                );
              })
            ) : (
              <path
                d={view.pts
                  .map((p, i) => `${i === 0 ? "M" : "L"}${view.cx(i).toFixed(1)},${view.yP(p.close).toFixed(1)}`)
                  .join(" ")}
                fill="none"
                stroke="#2563eb"
                strokeWidth="2"
              />
            )}

            {/* volume bars */}
            {view.pts.map((p, i) => (
              <rect
                key={p.date}
                x={view.cx(i) - view.bodyW / 2}
                y={view.yV(p.volume)}
                width={view.bodyW}
                height={VOL_TOP + VOL_H - view.yV(p.volume)}
                fill={p.close >= p.open ? UP : DOWN}
                opacity="0.45"
              />
            ))}
            <text x={PADL - 6} y={VOL_TOP + 8} fontSize="10" textAnchor="end" fill="#6b7280">
              {compact.format(view.maxVol)}
            </text>
            <text x={PADL - 6} y={VOL_TOP + VOL_H} fontSize="10" textAnchor="end" fill="#6b7280">
              Vol
            </text>

            {/* hover marker */}
            {hover !== null && (
              <line
                x1={view.cx(hover)}
                x2={view.cx(hover)}
                y1={PRICE_TOP}
                y2={VOL_TOP + VOL_H}
                stroke="#9ca3af"
                strokeDasharray="3 3"
              />
            )}

            {/* date labels */}
            <text x={PADL} y={H - 6} fontSize="10" fill="#6b7280">{view.pts[0].date}</text>
            <text x={W - PADR} y={H - 6} fontSize="10" textAnchor="end" fill="#6b7280">
              {view.pts[view.n - 1].date}
            </text>
          </svg>
          <p className="mt-2 text-xs text-gray-400">
            Source: {data.source} · retrieved {formatUtc(data.retrieved_at)} · latest data point {data.as_of}
          </p>
        </>
      )}
    </div>
  );
}