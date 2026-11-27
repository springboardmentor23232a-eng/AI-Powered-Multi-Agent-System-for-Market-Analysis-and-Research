import React, { useState, useMemo } from 'react';
import {
  normalizeCandles,
  formatNumericPrice,
  formatNumericVolume,
} from './chartHelpers';

// ── Chart Error Boundary Protection ─────────────────────────────────────────
export class ChartErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  componentDidCatch(error, info) {
    console.error('Chart visualization error caught by boundary:', error, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col items-center justify-center min-h-[220px] text-center gap-2">
          <p className="text-xs font-mono font-semibold text-rose-400">
            Stock chart visualization currently unavailable for this dataset format.
          </p>
          <p className="text-[11px] text-zinc-500">
            Telemetry data and validation records remain accessible below.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Interactive High-Definition Stock Performance Chart ─────────────────────
export default function StockPerformanceChart({ history, period, onPeriodChange, currency = 'USD' }) {
  const candles = useMemo(() => normalizeCandles(history?.candles), [history?.candles]);
  const [hoveredIndex, setHoveredIndex] = useState(null);

  if (candles.length === 0) return null;

  const validCloses = candles
    .map((c) => c.close)
    .filter((v) => typeof v === 'number' && !Number.isNaN(v) && Number.isFinite(v));
  const hasValidCloses = validCloses.length > 0;
  const minPrice = hasValidCloses ? Math.min(...validCloses) : 0;
  const maxPrice = hasValidCloses ? Math.max(...validCloses) : 1;
  const priceRange = maxPrice - minPrice || 1;

  const validVolumes = candles
    .map((c) => c.volume)
    .filter((v) => typeof v === 'number' && !Number.isNaN(v) && Number.isFinite(v));
  const maxVolume = validVolumes.length > 0 ? Math.max(...validVolumes) : 1;

  const width = 800;
  const height = 280;
  const paddingTop = 25;
  const paddingBottom = 45;
  const paddingX = 25;
  const chartHeight = height - paddingTop - paddingBottom;

  const points = candles.map((c, i) => {
    const x = paddingX + (i / Math.max(candles.length - 1, 1)) * (width - 2 * paddingX);
    const priceVal = typeof c.close === 'number' && !Number.isNaN(c.close) ? c.close : minPrice;
    const y = paddingTop + (1 - (priceVal - minPrice) / priceRange) * chartHeight;
    return { ...c, x, y };
  });

  const lineD = points.length > 0
    ? points.reduce((acc, p, i) => (i === 0 ? `M ${p.x.toFixed(1)},${p.y.toFixed(1)}` : `${acc} L ${p.x.toFixed(1)},${p.y.toFixed(1)}`), '')
    : '';
  const lastPointX = points[points.length - 1]?.x ?? (width - paddingX);
  const firstPointX = points[0]?.x ?? paddingX;
  const areaD = lineD
    ? `${lineD} L ${lastPointX.toFixed(1)},${(height - paddingBottom).toFixed(1)} L ${firstPointX.toFixed(1)},${(height - paddingBottom).toFixed(1)} Z`
    : '';

  // X-axis date labels (sample 5 dates)
  const step = Math.max(Math.floor(candles.length / 5), 1);
  const dateIndices = [0, step, step * 2, step * 3, candles.length - 1].filter((idx, i, arr) => arr.indexOf(idx) === i && idx < candles.length);

  const activeCandle = hoveredIndex !== null && points[hoveredIndex] ? points[hoveredIndex] : points[points.length - 1];
  const isUp = typeof activeCandle?.close === 'number' && typeof activeCandle?.open === 'number'
    ? activeCandle.close >= activeCandle.open
    : true;

  const periods = [
    { label: '1M', value: '1mo' },
    { label: '3M', value: '3mo' },
    { label: '6M', value: '6mo' },
    { label: '1Y', value: '1y' },
    { label: '5Y', value: '5y' },
  ];

  return (
    <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col gap-4 relative overflow-hidden">
      {/* Chart Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white tracking-tight uppercase">
              Stock Performance Overview
            </h3>
            <span className="text-xs font-mono font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
              {candles.length} Trading Days
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            Verified OHLCV trajectory • Provider: <span className="text-zinc-200 font-mono">{history.data_source || 'Market API'}</span>
          </p>
        </div>

        {/* Timeframe Selector Pills */}
        <div className="flex items-center gap-1 bg-white/[0.03] p-1 rounded-xl border border-white/[0.08] self-start sm:self-auto">
          {periods.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => onPeriodChange(p.value)}
              className={`px-3 py-1 text-xs font-mono font-semibold rounded-lg transition-all ${period === p.value
                  ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-sm shadow-rose-950'
                  : 'text-zinc-400 hover:text-white hover:bg-white/[0.05]'
                }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Hover Active Stats Callout */}
      <div className="flex flex-wrap items-center justify-between text-xs font-mono px-2 py-1 bg-white/[0.02] rounded-lg border border-white/[0.04]">
        <div className="flex items-center gap-4">
          <span className="text-zinc-400">Date: <strong className="text-white">{activeCandle?.date || 'N/A'}</strong></span>
          <span className="text-zinc-400">
            Close: <strong className={isUp ? 'text-emerald-400' : 'text-rose-400'}>
              {typeof activeCandle?.close === 'number'
                ? `${currency === 'INR' ? '₹' : '$'}${activeCandle.close.toFixed(2)}`
                : 'N/A'}
            </strong>
          </span>
          <span className="text-zinc-400 hidden sm:inline">Open: <strong className="text-zinc-200">{formatNumericPrice(activeCandle?.open, 2)}</strong></span>
          <span className="text-zinc-400 hidden sm:inline">High: <strong className="text-emerald-400">{formatNumericPrice(activeCandle?.high, 2)}</strong></span>
          <span className="text-zinc-400 hidden sm:inline">Low: <strong className="text-rose-400">{formatNumericPrice(activeCandle?.low, 2)}</strong></span>
        </div>
        <div className="text-zinc-400 hidden md:block">
          Volume: <strong className="text-white">{formatNumericVolume(activeCandle?.volume)}</strong>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto max-h-[300px] overflow-visible select-none"
          preserveAspectRatio="none"
          onMouseLeave={() => setHoveredIndex(null)}
        >
          <defs>
            <linearGradient id="chartGradientMain" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#e11d48" stopOpacity="0.45" />
              <stop offset="60%" stopColor="#be123c" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#060608" stopOpacity="0" />
            </linearGradient>

            <linearGradient id="volBarGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#881337" stopOpacity="0.1" />
            </linearGradient>
          </defs>

          {/* Horizontal Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const y = paddingTop + pct * chartHeight;
            const price = maxPrice - pct * priceRange;
            return (
              <g key={idx}>
                <line
                  x1={paddingX}
                  y1={y}
                  x2={width - paddingX}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeDasharray="4 4"
                />
                <text
                  x={width - paddingX + 8}
                  y={y + 3}
                  fill="rgba(161, 161, 170, 0.6)"
                  fontSize="9"
                  fontFamily="monospace"
                  textAnchor="start"
                >
                  {typeof price === 'number' && !Number.isNaN(price)
                    ? `${currency === 'INR' ? '₹' : '$'}${price.toFixed(0)}`
                    : ''}
                </text>
              </g>
            );
          })}

          {/* Volume Bars at Bottom */}
          {points.map((p, i) => {
            const volNum = typeof p.volume === 'number' && !Number.isNaN(p.volume) ? p.volume : 0;
            const barHeight = Math.max((volNum / (maxVolume || 1)) * 35, 2);
            const y = height - paddingBottom - barHeight;
            const barWidth = Math.max((width - 2 * paddingX) / candles.length - 2, 2);
            return (
              <rect
                key={`vol-${i}`}
                x={p.x - barWidth / 2}
                y={y}
                width={barWidth}
                height={barHeight}
                fill="url(#volBarGrad)"
                opacity="0.6"
              />
            );
          })}

          {/* Main Area Fill */}
          {areaD && <path d={areaD} fill="url(#chartGradientMain)" />}

          {/* Main Stroke Line */}
          {lineD && (
            <path
              d={lineD}
              fill="none"
              stroke="#f43f5e"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Interactive Hover Point & Vertical Crosshair */}
          {hoveredIndex !== null && points[hoveredIndex] && (
            <g>
              <line
                x1={points[hoveredIndex].x}
                y1={paddingTop}
                x2={points[hoveredIndex].x}
                y2={height - paddingBottom}
                stroke="#f43f5e"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              <circle
                cx={points[hoveredIndex].x}
                cy={points[hoveredIndex].y}
                r="5"
                fill="#ffffff"
                stroke="#e11d48"
                strokeWidth="2.5"
              />
            </g>
          )}

          {/* Transparent Hover Hitboxes */}
          {points.map((p, i) => {
            const hitWidth = width / candles.length;
            return (
              <rect
                key={`hit-${i}`}
                x={p.x - hitWidth / 2}
                y={0}
                width={hitWidth}
                height={height}
                fill="transparent"
                className="cursor-crosshair"
                onMouseEnter={() => setHoveredIndex(i)}
              />
            );
          })}

          {/* X-axis Date Labels */}
          {dateIndices.map((idx) => {
            const p = points[idx];
            if (!p) return null;
            return (
              <text
                key={`date-${idx}`}
                x={p.x}
                y={height - 12}
                fill="rgba(161, 161, 170, 0.7)"
                fontSize="10"
                fontFamily="monospace"
                textAnchor="middle"
              >
                {p.date}
              </text>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
