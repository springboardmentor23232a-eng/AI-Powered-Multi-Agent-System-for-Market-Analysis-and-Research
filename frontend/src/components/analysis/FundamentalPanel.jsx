import React from 'react';
import {
  TrendingUp,
  PieChart,
  Landmark,
  Calculator,
  Users,
  AlertTriangle,
  History,
  Info,
} from 'lucide-react';

function formatMoney(val, currency = 'USD') {
  if (val === null || val === undefined || Number.isNaN(val)) return 'N/A';
  const sym = currency === 'INR' ? '₹' : '$';
  const abs = Math.abs(val);
  const sign = val < 0 ? '-' : '';
  if (currency === 'INR') {
    if (abs >= 1e7) return `${sign}${sym}${(abs / 1e7).toFixed(2)} Cr`;
    if (abs >= 1e5) return `${sign}${sym}${(abs / 1e5).toFixed(2)} L`;
    return `${sign}${sym}${abs.toLocaleString()}`;
  }
  if (abs >= 1e12) return `${sign}${sym}${(abs / 1e12).toFixed(2)}T`;
  if (abs >= 1e9) return `${sign}${sym}${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}${sym}${(abs / 1e6).toFixed(2)}M`;
  return `${sign}${sym}${abs.toLocaleString()}`;
}

export default function FundamentalPanel({ fundamental }) {
  if (!fundamental) return null;

  const currency = fundamental.currency || 'USD';
  const rev = fundamental.revenue_and_earnings || {};
  const prof = fundamental.profitability || {};
  const stab = fundamental.debt_and_stability || {};
  const ratios = fundamental.financial_ratios || {};
  const hist = fundamental.historical_comparison || [];
  const peers = fundamental.peer_comparison || [];
  const gaps = fundamental.data_gaps || [];

  const ratioCards = [
    { label: 'P/E Ratio', data: ratios.pe_ratio, suffix: 'x' },
    { label: 'P/B Ratio', data: ratios.pb_ratio, suffix: 'x' },
    { label: 'Return on Equity (ROE)', data: ratios.roe_pct, suffix: '%' },
  ];

  return (
    <div className="space-y-6">
      <div className="glass-panel p-6 rounded-3xl space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#E4E1D8]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-50 border border-emerald-200 text-[#0A624C]">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-display text-base font-bold text-slate-900">Fundamental Analysis Agent Summary</h3>
              <p className="text-xs text-slate-500">Revenue, profitability, balance sheet stability & valuation</p>
            </div>
          </div>
          <span className="text-[11px] font-mono font-bold px-3 py-1 rounded-full bg-sky-50 text-sky-800 border border-sky-200">
            STABILITY: {(stab.stability_rating || 'N/A').toUpperCase()}
          </span>
        </div>
        <p className="text-sm text-slate-700 leading-relaxed">{fundamental.explanation}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {ratioCards.map((item) => {
          const r = item.data || {};
          return (
            <div key={item.label} className="glass-card p-5 rounded-2xl space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                  <Calculator className="w-3.5 h-3.5 text-[#0A624C]" />
                  {item.label}
                </span>
                <span
                  className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                    r.status === 'COMPUTED'
                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      : r.status === 'PROVIDER_FALLBACK'
                      ? 'bg-sky-50 text-sky-800 border border-sky-200'
                      : 'bg-stone-100 text-slate-600'
                  }`}
                >
                  {r.status || 'UNAVAILABLE'}
                </span>
              </div>
              <div className="font-mono text-2xl font-extrabold text-slate-900">
                {r.value !== null && r.value !== undefined ? `${r.value}${item.suffix}` : 'N/A'}
              </div>
              <p className="text-[11px] font-mono text-[#0A624C]">{r.formula}</p>
              <p className="text-[11px] text-slate-500 leading-snug">{r.note}</p>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass-panel p-5 rounded-3xl space-y-3">
          <h4 className="text-xs font-mono font-bold text-[#0A624C] uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-[#E4E1D8]">
            <TrendingUp className="w-4 h-4" />
            Revenue & Earnings
          </h4>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Latest Revenue</span>
              <span className="font-mono font-bold text-slate-900">{formatMoney(rev.latest_revenue, currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Revenue YoY Growth</span>
              <span className={`font-mono font-bold ${(rev.revenue_yoy_growth_pct || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                {rev.revenue_yoy_growth_pct !== null && rev.revenue_yoy_growth_pct !== undefined
                  ? `${rev.revenue_yoy_growth_pct > 0 ? '+' : ''}${rev.revenue_yoy_growth_pct}%`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Multi-Year Rev CAGR</span>
              <span className="font-mono font-bold text-slate-900">
                {rev.revenue_cagr_pct !== null && rev.revenue_cagr_pct !== undefined ? `${rev.revenue_cagr_pct}%` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Latest Net Income</span>
              <span className="font-mono font-bold text-slate-900">{formatMoney(rev.latest_net_income, currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Earnings YoY Growth</span>
              <span className={`font-mono font-bold ${(rev.earnings_yoy_growth_pct || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`}>
                {rev.earnings_yoy_growth_pct !== null && rev.earnings_yoy_growth_pct !== undefined
                  ? `${rev.earnings_yoy_growth_pct > 0 ? '+' : ''}${rev.earnings_yoy_growth_pct}%`
                  : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Operating Income (EBIT)</span>
              <span className="font-mono font-bold text-slate-900">{formatMoney(rev.operating_income, currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Diluted EPS</span>
              <span className="font-mono font-bold text-slate-900">
                {rev.diluted_eps !== null && rev.diluted_eps !== undefined
                  ? `${currency === 'INR' ? '₹' : '$'}${rev.diluted_eps}`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-3xl space-y-3">
          <h4 className="text-xs font-mono font-bold text-[#1E3A5F] uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-[#E4E1D8]">
            <PieChart className="w-4 h-4" />
            Profitability Metrics
          </h4>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Gross Profit Margin</span>
              <span className="font-mono font-bold text-slate-900">
                {prof.gross_margin_pct !== null && prof.gross_margin_pct !== undefined ? `${prof.gross_margin_pct}%` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Operating Margin</span>
              <span className="font-mono font-bold text-slate-900">
                {prof.operating_margin_pct !== null && prof.operating_margin_pct !== undefined ? `${prof.operating_margin_pct}%` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Net Profit Margin</span>
              <span className="font-mono font-bold text-slate-900">
                {prof.net_margin_pct !== null && prof.net_margin_pct !== undefined ? `${prof.net_margin_pct}%` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Return on Assets (ROA)</span>
              <span className="font-mono font-bold text-slate-900">
                {prof.roa_pct !== null && prof.roa_pct !== undefined ? `${prof.roa_pct}%` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Margin Trajectory</span>
              <span className="font-mono font-bold text-amber-700">{prof.margin_trend || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Forward P/E</span>
              <span className="font-mono font-bold text-slate-900">{ratios.forward_pe ? `${ratios.forward_pe}x` : 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">EV / EBITDA</span>
              <span className="font-mono font-bold text-slate-900">{ratios.ev_to_ebitda ? `${ratios.ev_to_ebitda}x` : 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-5 rounded-3xl space-y-3">
          <h4 className="text-xs font-mono font-bold text-amber-700 uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-[#E4E1D8]">
            <Landmark className="w-4 h-4" />
            Debt & Stability
          </h4>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Total Debt</span>
              <span className="font-mono font-bold text-slate-900">{formatMoney(stab.total_debt, currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Cash & Equivalents</span>
              <span className="font-mono font-bold text-slate-900">{formatMoney(stab.cash_and_equivalents, currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Net Debt</span>
              <span className="font-mono font-bold text-slate-900">{formatMoney(stab.net_debt, currency)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Debt-to-Equity</span>
              <span className="font-mono font-bold text-slate-900">
                {stab.debt_to_equity !== null && stab.debt_to_equity !== undefined ? `${stab.debt_to_equity}x` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Current / Quick Ratio</span>
              <span className="font-mono font-bold text-slate-900">
                {stab.current_ratio !== null && stab.current_ratio !== undefined ? `${stab.current_ratio}x` : 'N/A'} /{' '}
                {stab.quick_ratio !== null && stab.quick_ratio !== undefined ? `${stab.quick_ratio}x` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Interest Coverage</span>
              <span className="font-mono font-bold text-slate-900">
                {stab.interest_coverage !== null && stab.interest_coverage !== undefined ? `${stab.interest_coverage}x` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Free Cash Flow</span>
              <span className="font-mono font-bold text-emerald-700">{formatMoney(stab.free_cash_flow, currency)}</span>
            </div>
          </div>
        </div>
      </div>

      {hist.length > 0 && (
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <div className="flex items-center gap-2.5 pb-2 border-b border-[#E4E1D8]">
            <History className="w-5 h-5 text-[#1E3A5F]" />
            <h3 className="font-display text-base font-bold text-slate-900">Historical Financial Performance Comparison</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E4E1D8] text-slate-500 font-mono uppercase bg-[#FAF9F5]">
                  <th className="py-2.5 px-3">Period</th>
                  <th className="py-2.5 px-3">Revenue</th>
                  <th className="py-2.5 px-3">Rev YoY</th>
                  <th className="py-2.5 px-3">EBIT</th>
                  <th className="py-2.5 px-3">Net Income</th>
                  <th className="py-2.5 px-3">Net Margin</th>
                  <th className="py-2.5 px-3">FCF</th>
                  <th className="py-2.5 px-3">ROE</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EDEAE0] font-mono">
                {hist.map((row) => (
                  <tr key={row.fiscal_period} className="hover:bg-[#FAF9F5]">
                    <td className="py-2.5 px-3 font-bold text-[#1E3A5F]">{row.fiscal_period}</td>
                    <td className="py-2.5 px-3 text-slate-900 font-semibold">{formatMoney(row.revenue, currency)}</td>
                    <td className="py-2.5 px-3">
                      {row.revenue_growth_pct !== null && row.revenue_growth_pct !== undefined ? (
                        <span className={row.revenue_growth_pct >= 0 ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>
                          {row.revenue_growth_pct > 0 ? '+' : ''}
                          {row.revenue_growth_pct}%
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-slate-700">{formatMoney(row.operating_income, currency)}</td>
                    <td className="py-2.5 px-3 text-slate-900 font-semibold">{formatMoney(row.net_income, currency)}</td>
                    <td className="py-2.5 px-3 text-slate-700">
                      {row.net_margin_pct !== null && row.net_margin_pct !== undefined ? `${row.net_margin_pct}%` : 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 text-emerald-700 font-semibold">{formatMoney(row.free_cash_flow, currency)}</td>
                    <td className="py-2.5 px-3 text-slate-700">
                      {row.roe_pct !== null && row.roe_pct !== undefined ? `${row.roe_pct}%` : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {peers.length > 0 && (
        <div className="glass-panel p-6 rounded-3xl space-y-4">
          <div className="flex items-center gap-2.5 pb-2 border-b border-[#E4E1D8]">
            <Users className="w-5 h-5 text-[#0A624C]" />
            <h3 className="font-display text-base font-bold text-slate-900">Sector Peer Comparison</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E4E1D8] text-slate-500 font-mono uppercase bg-[#FAF9F5]">
                  <th className="py-2.5 px-3">Peer</th>
                  <th className="py-2.5 px-3">Market Cap</th>
                  <th className="py-2.5 px-3">P/E</th>
                  <th className="py-2.5 px-3">P/B</th>
                  <th className="py-2.5 px-3">ROE</th>
                  <th className="py-2.5 px-3">Margin</th>
                  <th className="py-2.5 px-3">Rev Growth</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EDEAE0] font-mono">
                {peers.map((p) => (
                  <tr key={`${p.market}-${p.ticker}`} className="hover:bg-[#FAF9F5]">
                    <td className="py-2.5 px-3 font-sans">
                      <span className="font-mono font-bold text-slate-900">{p.ticker}</span>
                      <span className="ml-1.5 text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-[#0A624C] border border-emerald-200">
                        {p.market}
                      </span>
                      <div className="text-[11px] text-slate-500">{p.company_name}</div>
                    </td>
                    <td className="py-2.5 px-3 text-slate-900 font-semibold">{formatMoney(p.market_cap, p.currency)}</td>
                    <td className="py-2.5 px-3 text-slate-700">{p.pe_ratio !== null ? `${p.pe_ratio}x` : 'N/A'}</td>
                    <td className="py-2.5 px-3 text-slate-700">{p.pb_ratio !== null ? `${p.pb_ratio}x` : 'N/A'}</td>
                    <td className="py-2.5 px-3 text-slate-700">{p.roe_pct !== null ? `${p.roe_pct}%` : 'N/A'}</td>
                    <td className="py-2.5 px-3 text-slate-700">{p.profit_margin_pct !== null ? `${p.profit_margin_pct}%` : 'N/A'}</td>
                    <td className="py-2.5 px-3">
                      {p.revenue_growth_pct !== null ? (
                        <span className={p.revenue_growth_pct >= 0 ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>
                          {p.revenue_growth_pct > 0 ? '+' : ''}
                          {p.revenue_growth_pct}%
                        </span>
                      ) : (
                        'N/A'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {gaps.length > 0 && (
        <div className="p-5 rounded-3xl bg-amber-50 border border-amber-200 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-800 uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            Missing or Inconsistent Financial Information
          </div>
          <ul className="space-y-1 text-xs text-amber-900">
            {gaps.map((g, i) => (
              <li key={i} className="flex items-start gap-2">
                <Info className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-amber-700" />
                <span>{g}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
