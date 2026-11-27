import React, { useState } from 'react';
import { Building2, ChevronDown, ChevronUp, RefreshCw, Layers } from 'lucide-react';
import Spinner from '../ui/Spinner';
import AlertBanner from '../ui/AlertBanner';

export default function FinancialStatementsView({
  financials,
  loading = false,
  error = null,
  onRefresh,
  currency = 'USD',
  ticker = '',
}) {
  const [statementType, setStatementType] = useState('income'); // 'income' | 'balance' | 'cash'
  const [frequency, setFrequency] = useState('annual'); // 'annual' | 'quarterly'
  const [isExpanded, setIsExpanded] = useState(true);

  if (loading) {
    return (
      <div className="glass-card p-6 border border-white/[0.08] bg-[#0d0d13]/90 flex items-center justify-center rounded-2xl">
        <div className="flex items-center gap-2.5 text-xs font-mono text-zinc-400">
          <Spinner className="h-4 w-4 text-rose-500" />
          <span>Retrieving financial statements from market provider…</span>
        </div>
      </div>
    );
  }

  const section =
    statementType === 'income'
      ? financials?.income_statement
      : statementType === 'balance'
      ? financials?.balance_sheet
      : financials?.cash_flow;

  const activeData = frequency === 'annual' ? section?.annual : section?.quarterly;
  const periods = activeData?.periods || [];
  const items = activeData?.items || [];
  const hasData = periods.length > 0 && items.length > 0;

  const curr = financials?.currency || currency;
  const currSym = curr === 'INR' ? '₹' : '$';

  const formatNumber = (val) => {
    if (val === null || val === undefined || isNaN(val)) return '—';
    const absVal = Math.abs(val);
    const sign = val < 0 ? '-' : '';
    if (absVal >= 1e9) {
      return `${sign}${currSym}${(absVal / 1e9).toFixed(2)}B`;
    }
    if (absVal >= 1e6) {
      return `${sign}${currSym}${(absVal / 1e6).toFixed(2)}M`;
    }
    if (absVal >= 1e3) {
      return `${sign}${currSym}${(absVal / 1e3).toFixed(2)}K`;
    }
    return `${sign}${currSym}${Math.round(absVal).toLocaleString()}`;
  };

  return (
    <div className="glass-card p-5 border border-white/[0.08] bg-[#0d0d13]/90 rounded-2xl space-y-4">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/10 border border-rose-500/25 text-rose-400">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-tight uppercase">
                Financial Statements & Accounting Disclosures
              </h3>
              <span className="text-[10px] font-mono font-semibold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                {financials?.data_source || 'yfinance'}
              </span>
            </div>
            <p className="text-[11px] text-zinc-400 mt-0.5">
              Annual & Quarterly reports in <span className="text-zinc-200 font-mono">{curr}</span>
              {ticker ? ` for ${ticker}` : ''}
              {financials?.retrieved_at ? ` • Updated ${new Date(financials.retrieved_at).toLocaleDateString()}` : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {onRefresh && (
            <button
              type="button"
              onClick={onRefresh}
              className="btn-secondary py-1 px-2.5 text-[11px] flex items-center gap-1.5"
              title="Refresh statements"
            >
              <RefreshCw className="h-3 w-3 text-zinc-400" />
              <span>Refresh</span>
            </button>
          )}
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="btn-secondary py-1 px-2.5 text-[11px] flex items-center gap-1.5"
          >
            <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
            {isExpanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="space-y-4 animate-fade-in">
          {/* Controls: Statement tabs & Frequency toggle */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            {/* Statement Type Tabs */}
            <div className="flex items-center gap-1.5 bg-white/[0.03] p-1 rounded-xl border border-white/[0.06]">
              {[
                { id: 'income', label: 'Income Statement' },
                { id: 'balance', label: 'Balance Sheet' },
                { id: 'cash', label: 'Cash Flow' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setStatementType(tab.id)}
                  className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
                    statementType === tab.id
                      ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold'
                      : 'text-zinc-400 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Frequency Toggle */}
            <div className="flex items-center gap-1.5 bg-white/[0.03] p-1 rounded-xl border border-white/[0.06]">
              <button
                type="button"
                onClick={() => setFrequency('annual')}
                className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
                  frequency === 'annual'
                    ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white font-bold shadow-sm'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Annual
              </button>
              <button
                type="button"
                onClick={() => setFrequency('quarterly')}
                className={`px-3 py-1 text-xs rounded-lg font-medium transition-all ${
                  frequency === 'quarterly'
                    ? 'bg-gradient-to-r from-red-600 to-rose-600 text-white font-bold shadow-sm'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                Quarterly
              </button>
            </div>
          </div>

          {error && <AlertBanner message={error} variant="error" />}

          {/* Statements Table */}
          {hasData ? (
            <div className="overflow-x-auto max-h-96 rounded-xl border border-white/[0.08]">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-white/[0.04] text-zinc-300 sticky top-0 uppercase tracking-wider text-[10px] border-b border-white/[0.08]">
                  <tr>
                    <th className="py-2.5 px-3 min-w-[220px]">Line Item</th>
                    {periods.map((p) => (
                      <th key={p} className="py-2.5 px-3 text-right min-w-[110px] font-semibold text-rose-300">
                        {p}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04] bg-[#0b0b10] text-zinc-200">
                  {items.map((item, idx) => (
                    <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                      <td className="py-2 px-3 font-sans font-medium text-zinc-300 whitespace-nowrap">
                        {item.metric}
                      </td>
                      {periods.map((p) => (
                        <td key={p} className="py-2 px-3 text-right text-zinc-300 whitespace-nowrap">
                          {formatNumber(item.values?.[p])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8 px-4 border border-dashed border-white/[0.08] rounded-xl bg-white/[0.01]">
              <Building2 className="h-6 w-6 text-zinc-600 mx-auto mb-2 opacity-50" />
              <p className="text-xs text-zinc-400 font-medium">
                No {frequency} {statementType === 'income' ? 'income statement' : statementType === 'balance' ? 'balance sheet' : 'cash flow'} data available.
              </p>
              <p className="text-[11px] text-zinc-500 mt-0.5">
                Financial disclosure records may be pending or unavailable from the market data provider.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
