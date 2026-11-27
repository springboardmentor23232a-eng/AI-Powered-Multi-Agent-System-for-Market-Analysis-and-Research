import React from 'react';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Minus,
  AlertCircle,
  Gauge,
  CheckCircle2,
} from 'lucide-react';
import TechnicalCharts from '../charts/TechnicalCharts';

export default function TechnicalPanel({ technical }) {
  if (!technical) return null;

  const currency = technical.currency || 'USD';
  const curSym = currency === 'INR' ? '₹' : '$';
  const trend = technical.trend_summary || {};
  const ind = technical.latest_indicators || {};
  const vol = technical.volatility || {};
  const conditions = technical.technical_conditions || [];
  const limitations = technical.data_limitations || [];

  const signal = trend.overall_signal || 'Mixed Signals';
  const signalTheme =
    signal === 'Upward Trend'
      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
      : signal === 'Downward Trend'
      ? 'bg-rose-50 text-rose-800 border-rose-200'
      : 'bg-amber-50 text-amber-800 border-amber-200';

  const SignalIcon =
    signal === 'Upward Trend' ? TrendingUp : signal === 'Downward Trend' ? TrendingDown : Minus;

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-[#E4E1D8]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-50 border border-amber-200 text-amber-700">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-display text-base font-bold text-slate-900">Technical Analysis Agent Assessment</h3>
              <p className="text-xs font-mono text-slate-500">
                {trend.trading_days_analyzed || 0} trading sessions analyzed ({technical.period})
              </p>
            </div>
          </div>

          <span className={`inline-flex items-center gap-1.5 text-xs font-mono font-bold px-3.5 py-1.5 rounded-full border ${signalTheme}`}>
            <SignalIcon className="w-4 h-4" />
            {signal.toUpperCase()}
          </span>
        </div>

        <p className="text-sm text-slate-700 leading-relaxed">{technical.explanation}</p>

        {technical.disclaimer && (
          <div className="p-3.5 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] text-xs text-slate-600 flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <span>{technical.disclaimer}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {[
          { label: 'SMA 20', val: ind.sma_20 !== null && ind.sma_20 !== undefined ? `${curSym}${ind.sma_20}` : 'N/A', pct: trend.pct_from_sma_20 },
          { label: 'SMA 50', val: ind.sma_50 !== null && ind.sma_50 !== undefined ? `${curSym}${ind.sma_50}` : 'N/A', pct: trend.pct_from_sma_50 },
          { label: 'SMA 200', val: ind.sma_200 !== null && ind.sma_200 !== undefined ? `${curSym}${ind.sma_200}` : 'N/A', pct: trend.pct_from_sma_200 },
        ].map((m) => (
          <div key={m.label} className="glass-card p-4 rounded-2xl">
            <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase block">{m.label}</span>
            <span className="font-mono text-lg font-extrabold text-slate-900">{m.val}</span>
            {m.pct !== null && m.pct !== undefined && (
              <span className={`text-[11px] font-mono font-semibold block ${m.pct >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                {m.pct > 0 ? '+' : ''}
                {m.pct}% vs price
              </span>
            )}
          </div>
        ))}

        <div className="glass-card p-4 rounded-2xl">
          <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase block">EMA 12 / 26</span>
          <span className="font-mono text-sm font-extrabold text-slate-900 block mt-1">
            {ind.ema_12 !== null && ind.ema_12 !== undefined ? `${curSym}${ind.ema_12}` : 'N/A'} /{' '}
            {ind.ema_26 !== null && ind.ema_26 !== undefined ? `${curSym}${ind.ema_26}` : 'N/A'}
          </span>
          <span className="text-[11px] text-slate-500 block mt-0.5">Exponential MAs</span>
        </div>

        <div className="glass-card p-4 rounded-2xl">
          <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase block">RSI (14)</span>
          <span
            className={`font-mono text-lg font-extrabold ${
              ind.rsi_14 >= 70 ? 'text-rose-700' : ind.rsi_14 <= 30 ? 'text-emerald-700' : 'text-[#1E3A5F]'
            }`}
          >
            {ind.rsi_14 !== null && ind.rsi_14 !== undefined ? ind.rsi_14 : 'N/A'}
          </span>
          <span className="text-[11px] text-slate-500 block">
            {ind.rsi_14 >= 70 ? 'Overbought' : ind.rsi_14 <= 30 ? 'Oversold' : 'Neutral Band'}
          </span>
        </div>

        <div className="glass-card p-4 rounded-2xl">
          <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase block">Annual Vol</span>
          <span className="font-mono text-lg font-extrabold text-amber-700">
            {vol.annualized_volatility_pct !== null && vol.annualized_volatility_pct !== undefined
              ? `${vol.annualized_volatility_pct}%`
              : 'N/A'}
          </span>
          <span className="text-[11px] font-mono text-slate-500 block">
            {vol.volatility_regime} • DD {vol.max_drawdown_pct ?? 'N/A'}%
          </span>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-3xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#E4E1D8]">
          <div>
            <h3 className="font-display text-base font-bold text-slate-900">Interactive Price & Indicator Charts</h3>
            <p className="text-xs text-slate-500">
              OHLCV price action with SMA/EMA overlays, Volume, RSI(14), and MACD(12,26,9)
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-500 font-mono">
            <span>MACD: <strong className="text-[#0A624C]">{ind.macd ?? 'N/A'}</strong></span>
            <span>SIG: <strong className="text-amber-700">{ind.macd_signal ?? 'N/A'}</strong></span>
            <span>ATR-14: <strong className="text-[#1E3A5F]">{vol.atr_14 ?? 'N/A'}</strong></span>
          </div>
        </div>
        <TechnicalCharts chartSeries={technical.chart_series || []} ticker={technical.ticker} currency={currency} />
      </div>

      {conditions.length > 0 && (
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-[#E4E1D8]">
            <div className="flex items-center gap-2.5">
              <Gauge className="w-5 h-5 text-[#0A624C]" />
              <h3 className="font-display text-base font-bold text-slate-900">Predefined Technical Conditions</h3>
            </div>
            <div className="flex items-center gap-2 text-xs font-mono font-bold">
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                {trend.bullish_conditions || 0} BULLISH
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-800 border border-rose-200">
                {trend.bearish_conditions || 0} BEARISH
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {conditions.map((c) => {
              const badgeStyle =
                c.signal === 'Bullish'
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : c.signal === 'Bearish'
                  ? 'bg-rose-50 text-rose-800 border-rose-200'
                  : 'bg-stone-100 text-slate-700 border-stone-200';
              return (
                <div
                  key={c.id}
                  className="p-4 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] flex items-start justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-[#0A624C] flex-shrink-0" />
                      <span className="text-xs font-bold text-slate-900">{c.name}</span>
                    </div>
                    <p className="text-[11px] text-slate-600 leading-relaxed">{c.description}</p>
                    <span className="inline-block text-[10px] font-mono text-slate-400 uppercase">{c.category}</span>
                  </div>
                  <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border flex-shrink-0 ${badgeStyle}`}>
                    {c.signal.toUpperCase()}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {limitations.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-1">
          <p className="font-mono font-bold text-amber-800">INDICATOR WINDOW NOTES</p>
          {limitations.map((l, i) => (
            <p key={i}>• {l}</p>
          ))}
        </div>
      )}
    </div>
  );
}
