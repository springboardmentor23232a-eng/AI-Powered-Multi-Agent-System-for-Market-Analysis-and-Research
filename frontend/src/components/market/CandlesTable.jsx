import React from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { formatNumericPrice, formatNumericVolume } from './chartHelpers';

/**
 * CandlesTable
 * Collapsible verified OHLCV trading records table.
 */
export default function CandlesTable({
  candles = [],
  showTable = false,
  onToggle = () => {},
}) {
  if (!candles || candles.length === 0) return null;

  return (
    <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Verified OHLCV Trading Records
          </h4>
          <p className="text-[11px] text-zinc-400 mt-0.5">
            {candles.length} verified market days stored for this session
          </p>
        </div>

        <button
          type="button"
          onClick={onToggle}
          className="btn-secondary py-1 px-3 text-xs flex items-center gap-1.5"
        >
          <span>{showTable ? 'Hide Table' : 'Show Trading Days'}</span>
          {showTable ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>
      </div>

      {showTable && (
        <div className="mt-4 overflow-x-auto max-h-64 rounded-xl border border-white/[0.08] animate-fade-in">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-white/[0.03] text-zinc-400 sticky top-0 uppercase tracking-wider text-[10px] border-b border-white/[0.08]">
              <tr>
                <th className="py-2.5 px-3">Date</th>
                <th className="py-2.5 px-3">Open</th>
                <th className="py-2.5 px-3">High</th>
                <th className="py-2.5 px-3">Low</th>
                <th className="py-2.5 px-3">Close</th>
                <th className="py-2.5 px-3">Volume</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] bg-[#0b0b10] text-zinc-200">
              {candles.slice(-20).reverse().map((candle, idx) => {
                const isGreen = typeof candle.close === 'number' && typeof candle.open === 'number'
                  ? candle.close >= candle.open
                  : true;
                return (
                  <tr key={candle.date || idx} className="hover:bg-white/[0.02]">
                    <td className="py-2 px-3 font-semibold text-zinc-300">{candle.date || 'N/A'}</td>
                    <td className="py-2 px-3">{formatNumericPrice(candle.open, 2)}</td>
                    <td className="py-2 px-3 text-emerald-400">{formatNumericPrice(candle.high, 2)}</td>
                    <td className="py-2 px-3 text-rose-400">{formatNumericPrice(candle.low, 2)}</td>
                    <td className={`py-2 px-3 font-bold ${isGreen ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {formatNumericPrice(candle.close, 2)}
                    </td>
                    <td className="py-2 px-3 text-zinc-400">{formatNumericVolume(candle.volume)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
