/**
 * chartHelpers.js
 * Robust normalization and formatting helpers for OHLCV candles and pricing telemetry.
 */

export const parseNumericValue = (val) => {
  if (val === null || val === undefined || val === '') return null;
  const num = typeof val === 'number' ? val : Number(val);
  return !Number.isNaN(num) && Number.isFinite(num) ? num : null;
};

export const normalizeCandle = (raw) => {
  if (!raw || typeof raw !== 'object') {
    return {
      date: 'N/A',
      open: null,
      high: null,
      low: null,
      close: null,
      volume: null,
    };
  }

  const dateVal = raw.date ?? raw.Date ?? raw.datetime ?? raw.Datetime ?? raw.timestamp ?? 'N/A';
  const openVal = parseNumericValue(raw.open ?? raw.Open);
  const highVal = parseNumericValue(raw.high ?? raw.High);
  const lowVal = parseNumericValue(raw.low ?? raw.Low);
  const closeVal = parseNumericValue(raw.close ?? raw.Close);
  const volumeVal = parseNumericValue(raw.volume ?? raw.Volume);

  return {
    ...raw,
    date: typeof dateVal === 'string' ? dateVal : String(dateVal || 'N/A'),
    open: openVal,
    high: highVal,
    low: lowVal,
    close: closeVal,
    volume: volumeVal !== null ? Math.round(volumeVal) : null,
  };
};

export const normalizeCandles = (rawCandles) => {
  if (!Array.isArray(rawCandles)) return [];
  return rawCandles.map(normalizeCandle);
};

export const formatNumericPrice = (val, decimals = 2) => {
  return typeof val === 'number' && !Number.isNaN(val) && Number.isFinite(val)
    ? val.toFixed(decimals)
    : 'N/A';
};

export const formatNumericVolume = (val) => {
  return typeof val === 'number' && !Number.isNaN(val) && Number.isFinite(val)
    ? Math.round(val).toLocaleString()
    : 'N/A';
};
