import React, { useEffect, useRef, useState } from 'react';
import Plotly from 'plotly.js-dist-min';
import { BarChart3, Activity, SlidersHorizontal } from 'lucide-react';

function PlotlyPlot({ data, layout, config, className = '' }) {
  const containerRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !data) return;

    Plotly.react(el, data, layout, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
      ...config,
    });

    const handleResize = () => {
      if (containerRef.current) {
        Plotly.Plots.resize(containerRef.current);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [data, layout, config]);

  useEffect(() => {
    const el = containerRef.current;
    return () => {
      if (el) {
        Plotly.purge(el);
      }
    };
  }, []);

  return <div ref={containerRef} className={className} />;
}

export default function TechnicalCharts({ chartSeries = [], ticker = '', currency = 'USD' }) {
  const [chartType, setChartType] = useState('candlestick');
  const [overlays, setOverlays] = useState({
    sma20: true,
    sma50: true,
    sma200: true,
    ema12: false,
    ema26: false,
  });

  if (!chartSeries || chartSeries.length === 0) {
    return (
      <div className="p-8 text-center rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-500">
        No chart series available for the selected horizon.
      </div>
    );
  }

  const dates = chartSeries.map((d) => d.date);
  const opens = chartSeries.map((d) => d.open);
  const highs = chartSeries.map((d) => d.high);
  const lows = chartSeries.map((d) => d.low);
  const closes = chartSeries.map((d) => d.close);
  const volumes = chartSeries.map((d) => d.volume);
  const sma20 = chartSeries.map((d) => d.sma_20);
  const sma50 = chartSeries.map((d) => d.sma_50);
  const sma200 = chartSeries.map((d) => d.sma_200);
  const ema12 = chartSeries.map((d) => d.ema_12);
  const ema26 = chartSeries.map((d) => d.ema_26);
  const rsi14 = chartSeries.map((d) => d.rsi_14);
  const macd = chartSeries.map((d) => d.macd);
  const macdSig = chartSeries.map((d) => d.macd_signal);
  const macdHist = chartSeries.map((d) => d.macd_histogram);

  const curSym = currency === 'INR' ? '₹' : '$';

  // Main Price + Volume Traces
  const priceTraces = [];
  if (chartType === 'candlestick') {
    priceTraces.push({
      type: 'candlestick',
      x: dates,
      open: opens,
      high: highs,
      low: lows,
      close: closes,
      name: `${ticker} OHLC`,
      increasing: { line: { color: '#10b981' } },
      decreasing: { line: { color: '#ef4444' } },
      yaxis: 'y',
    });
  } else {
    priceTraces.push({
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: closes,
      name: `${ticker} Close`,
      line: { color: '#2563eb', width: 2.2 },
      fill: 'tozeroy',
      fillcolor: 'rgba(37, 99, 235, 0.08)',
      yaxis: 'y',
    });
  }

  if (overlays.sma20 && sma20.some((v) => v !== null)) {
    priceTraces.push({
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: sma20,
      name: 'SMA 20',
      line: { color: '#f59e0b', width: 1.5 },
      yaxis: 'y',
    });
  }
  if (overlays.sma50 && sma50.some((v) => v !== null)) {
    priceTraces.push({
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: sma50,
      name: 'SMA 50',
      line: { color: '#8b5cf6', width: 1.6 },
      yaxis: 'y',
    });
  }
  if (overlays.sma200 && sma200.some((v) => v !== null)) {
    priceTraces.push({
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: sma200,
      name: 'SMA 200',
      line: { color: '#ec4899', width: 1.8, dash: 'dot' },
      yaxis: 'y',
    });
  }
  if (overlays.ema12 && ema12.some((v) => v !== null)) {
    priceTraces.push({
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: ema12,
      name: 'EMA 12',
      line: { color: '#06b6d4', width: 1.4, dash: 'dash' },
      yaxis: 'y',
    });
  }
  if (overlays.ema26 && ema26.some((v) => v !== null)) {
    priceTraces.push({
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: ema26,
      name: 'EMA 26',
      line: { color: '#6366f1', width: 1.4, dash: 'dash' },
      yaxis: 'y',
    });
  }

  const volColors = chartSeries.map((d) =>
    d.close >= d.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'
  );
  priceTraces.push({
    type: 'bar',
    x: dates,
    y: volumes,
    name: 'Volume',
    marker: { color: volColors },
    yaxis: 'y2',
  });

  const priceLayout = {
    height: 430,
    margin: { t: 20, r: 20, b: 30, l: 55 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: '#ffffff',
    hovermode: 'x unified',
    legend: { orientation: 'h', y: 1.08, x: 0, font: { size: 11 } },
    xaxis: {
      rangeslider: { visible: false },
      gridcolor: '#f1f5f9',
      tickfont: { size: 11, color: '#64748b' },
    },
    yaxis: {
      domain: [0.24, 1.0],
      title: { text: `Price (${curSym})`, font: { size: 11, color: '#64748b' } },
      gridcolor: '#f1f5f9',
      tickfont: { size: 11, color: '#64748b' },
    },
    yaxis2: {
      domain: [0.0, 0.18],
      title: { text: 'Vol', font: { size: 10, color: '#94a3b8' } },
      showgrid: false,
      tickfont: { size: 10, color: '#94a3b8' },
    },
  };

  // RSI Chart
  const rsiTraces = [
    {
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: rsi14,
      name: 'RSI (14)',
      line: { color: '#6366f1', width: 2 },
    },
  ];
  const rsiLayout = {
    height: 210,
    margin: { t: 15, r: 20, b: 30, l: 50 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: '#ffffff',
    hovermode: 'x unified',
    showlegend: false,
    xaxis: { gridcolor: '#f1f5f9', tickfont: { size: 10, color: '#64748b' } },
    yaxis: {
      range: [0, 100],
      gridcolor: '#f1f5f9',
      tickfont: { size: 10, color: '#64748b' },
      title: { text: 'RSI', font: { size: 11, color: '#64748b' } },
    },
    shapes: [
      {
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        y0: 70,
        y1: 70,
        line: { color: '#ef4444', width: 1, dash: 'dash' },
      },
      {
        type: 'line',
        xref: 'paper',
        x0: 0,
        x1: 1,
        y0: 30,
        y1: 30,
        line: { color: '#10b981', width: 1, dash: 'dash' },
      },
    ],
  };

  // MACD Chart
  const histColors = macdHist.map((v) =>
    v === null || v === undefined ? '#cbd5e1' : v >= 0 ? 'rgba(16, 185, 129, 0.65)' : 'rgba(239, 68, 68, 0.65)'
  );
  const macdTraces = [
    {
      type: 'bar',
      x: dates,
      y: macdHist,
      name: 'Histogram',
      marker: { color: histColors },
    },
    {
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: macd,
      name: 'MACD',
      line: { color: '#2563eb', width: 1.8 },
    },
    {
      type: 'scatter',
      mode: 'lines',
      x: dates,
      y: macdSig,
      name: 'Signal (9)',
      line: { color: '#f97316', width: 1.5 },
    },
  ];
  const macdLayout = {
    height: 220,
    margin: { t: 25, r: 20, b: 30, l: 50 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: '#ffffff',
    hovermode: 'x unified',
    legend: { orientation: 'h', y: 1.15, x: 0, font: { size: 10 } },
    xaxis: { gridcolor: '#f1f5f9', tickfont: { size: 10, color: '#64748b' } },
    yaxis: {
      gridcolor: '#f1f5f9',
      tickfont: { size: 10, color: '#64748b' },
      title: { text: 'MACD', font: { size: 11, color: '#64748b' } },
    },
  };

  const toggleOverlay = (key) => {
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-5">
      {/* Chart Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-2xl bg-slate-50 border border-slate-200/80">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold text-slate-700">Price & Overlays</span>
          <div className="ml-2 inline-flex rounded-xl bg-white p-0.5 border border-slate-200">
            <button
              type="button"
              onClick={() => setChartType('candlestick')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                chartType === 'candlestick' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Candlestick
            </button>
            <button
              type="button"
              onClick={() => setChartType('line')}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-colors ${
                chartType === 'line' ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Close Line
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <SlidersHorizontal className="w-3.5 h-3.5 text-slate-400 mr-1" />
          {[
            { key: 'sma20', label: 'SMA 20', color: 'text-amber-700 bg-amber-50 border-amber-200' },
            { key: 'sma50', label: 'SMA 50', color: 'text-purple-700 bg-purple-50 border-purple-200' },
            { key: 'sma200', label: 'SMA 200', color: 'text-pink-700 bg-pink-50 border-pink-200' },
            { key: 'ema12', label: 'EMA 12', color: 'text-cyan-700 bg-cyan-50 border-cyan-200' },
            { key: 'ema26', label: 'EMA 26', color: 'text-indigo-700 bg-indigo-50 border-indigo-200' },
          ].map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => toggleOverlay(item.key)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border transition-all ${
                overlays[item.key]
                  ? item.color
                  : 'text-slate-400 bg-white border-slate-200 opacity-70 hover:opacity-100'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Price + Volume Chart */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-3">
        <PlotlyPlot data={priceTraces} layout={priceLayout} className="w-full" />
      </div>

      {/* RSI & MACD Subplots */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-indigo-600" />
              Relative Strength Index (RSI-14)
            </span>
            <span className="text-[11px] text-slate-400">70 Overbought / 30 Oversold</span>
          </div>
          <PlotlyPlot data={rsiTraces} layout={rsiLayout} className="w-full" />
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white p-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-blue-600" />
              MACD (12, 26, 9)
            </span>
            <span className="text-[11px] text-slate-400">Trend Momentum</span>
          </div>
          <PlotlyPlot data={macdTraces} layout={macdLayout} className="w-full" />
        </div>
      </div>
    </div>
  );
}

