import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import Sparkline from './Sparkline';

/**
 * MarketSnapshotBento
 * 4-Card Bento Financial Snapshot Grid with embedded real SVG sparklines.
 */
export default function MarketSnapshotBento({
  overview,
  recentCloses = [],
  recentVolumes = [],
  isPriceUp = false,
  priceChange = 0,
}) {
  if (!overview) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Bento Card 1: Active Price & Change */}
      <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
              {overview.ticker} • {overview.exchange}
            </span>
            <h4 className="text-xs font-medium text-zinc-300 truncate max-w-[150px]">
              {overview.company_name}
            </h4>
          </div>
          {isPriceUp ? (
            <span className="inline-flex items-center gap-0.5 text-xs font-mono font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
              <ArrowUpRight className="h-3 w-3" />+{priceChange.toFixed(2)}%
            </span>
          ) : (
            <span className="inline-flex items-center gap-0.5 text-xs font-mono font-bold text-rose-400 bg-rose-950/40 px-2 py-0.5 rounded border border-rose-800/40">
              <ArrowDownRight className="h-3 w-3" />{priceChange.toFixed(2)}%
            </span>
          )}
        </div>

        <div className="mt-4 flex items-end justify-between">
          <div>
            <div className="text-2xl lg:text-3xl font-extrabold font-mono text-white tracking-tight">
              {overview.currency === 'INR' ? '₹' : '$'}
              {overview.current_price?.toLocaleString() || 'N/A'}
            </div>
            <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
              Prev: {overview.currency === 'INR' ? '₹' : '$'}{overview.previous_close || 'N/A'}
            </p>
          </div>

          <Sparkline data={recentCloses} height={36} width={90} color={isPriceUp ? '#34d399' : '#f43f5e'} />
        </div>
      </div>

      {/* Bento Card 2: Day Range */}
      <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            Day Trading Range
          </span>
          <span className="text-[10px] font-mono text-zinc-500">Intraday</span>
        </div>

        <div className="mt-4 flex items-end justify-between">
          <div>
            <div className="text-base font-mono font-bold text-white tracking-tight">
              {overview.day_low || 'N/A'} — {overview.day_high || 'N/A'}
            </div>
            <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
              Currency: {overview.currency}
            </p>
          </div>

          <Sparkline data={recentCloses} height={36} width={85} color="#f43f5e" />
        </div>
      </div>

      {/* Bento Card 3: 52-Week Range & Position */}
      <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            52-Week Range
          </span>
          <span className="text-[10px] font-mono text-rose-400">Annual</span>
        </div>

        <div className="mt-4">
          <div className="text-base font-mono font-bold text-white tracking-tight">
            {overview.fifty_two_week_low || 'N/A'} — {overview.fifty_two_week_high || 'N/A'}
          </div>

          {/* 52-Week Position Bar */}
          {overview.fifty_two_week_low && overview.fifty_two_week_high && overview.current_price && (
            <div className="mt-2.5">
              <div className="h-1.5 w-full rounded-full bg-white/[0.08] overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-red-600 via-rose-500 to-emerald-400 rounded-full"
                  style={{
                    width: `${Math.min(
                      Math.max(
                        ((overview.current_price - overview.fifty_two_week_low) /
                          (overview.fifty_two_week_high - overview.fifty_two_week_low)) *
                          100,
                        5
                      ),
                      100
                    )}%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-[9px] font-mono text-zinc-500 mt-1">
                <span>Low: {overview.fifty_two_week_low}</span>
                <span>High: {overview.fifty_two_week_high}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bento Card 4: Valuation & Volume */}
      <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 flex flex-col justify-between hover:border-white/[0.15] transition-all">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
            P/E Ratio & Volume
          </span>
          <span className="text-[10px] font-mono font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
            P/E: {overview.pe_ratio || 'N/A'}
          </span>
        </div>

        <div className="mt-4 flex items-end justify-between">
          <div>
            <div className="text-lg lg:text-xl font-mono font-extrabold text-white">
              {overview.volume ? overview.volume.toLocaleString() : 'N/A'}
            </div>
            <p className="text-[10px] text-zinc-500 font-mono mt-0.5">
              Shares Traded
            </p>
          </div>

          <Sparkline data={recentVolumes} height={36} width={85} color="#fb7185" />
        </div>
      </div>
    </div>
  );
}
