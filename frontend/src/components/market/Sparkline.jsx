import React from 'react';

/**
 * Sparkline
 * Real data SVG sparkline component with gradient area fill.
 */
export default function Sparkline({ data = [], height = 38, width = 110, color = '#f43f5e' }) {
  const cleanData = Array.isArray(data)
    ? data.filter((v) => typeof v === 'number' && !Number.isNaN(v) && Number.isFinite(v))
    : [];

  if (cleanData.length < 2) return null;
  const min = Math.min(...cleanData);
  const max = Math.max(...cleanData);
  const range = max - min || 1;

  const points = cleanData.map((val, idx) => {
    const x = (idx / (cleanData.length - 1)) * (width - 6) + 3;
    const y = height - 5 - ((val - min) / range) * (height - 10);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const areaPoints = `3,${height} ${points} ${width - 3},${height}`;
  const gradId = `spark-${Math.abs(Math.round(cleanData[0] || 0))}-${cleanData.length}`;

  return (
    <svg width={width} height={height} className="overflow-visible shrink-0" aria-hidden="true">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.4" />
          <stop offset="100%" stopColor="#060608" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={areaPoints} fill={`url(#${gradId})`} />
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
