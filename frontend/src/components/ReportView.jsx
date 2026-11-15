import React, { useState, useEffect } from 'react';
import {
  ArrowLeft,
  Download,
  Building2,
  BarChart3,
  TrendingUp,
  MessageSquare,
  Shield,
  AlertTriangle,
  CheckCircle2,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  FileText,
  Info,
  Sparkles,
  Layers,
  ChevronRight,
  Target,
  LineChart,
} from 'lucide-react';
import { api } from '../api/client';
import StockLogo from './StockLogo';
import ExportModal from './ExportModal';

function formatSupportingMetric(key, val) {
  if (val === null || val === undefined || val === '') return 'Unavailable';
  if (typeof val === 'number') {
    // Large monetary values: free cash flow, total cash, total debt, market cap, etc.
    if (['free_cash_flow', 'total_cash', 'total_debt', 'market_cap', 'total_revenue', 'ebitda'].includes(key)) {
      const isNegative = val < 0;
      const absVal = Math.abs(val);
      if (absVal >= 1e12) {
        return `${isNegative ? '-' : ''}$${(absVal / 1e12).toFixed(2)}T USD`;
      } else if (absVal >= 1e9) {
        return `${isNegative ? '-' : ''}$${(absVal / 1e9).toFixed(2)}B USD`;
      } else if (absVal >= 1e6) {
        return `${isNegative ? '-' : ''}$${(absVal / 1e6).toFixed(2)}M USD`;
      } else if (absVal >= 1e3) {
        return `${isNegative ? '-' : ''}$${(absVal / 1e3).toFixed(2)}K USD`;
      }
      return `$${val.toFixed(2)} USD`;
    }

    // Margins and Growth Rates
    if (['profit_margins', 'operating_margins', 'gross_margins', 'revenue_growth', 'earnings_growth'].includes(key)) {
      return `${(val * 100).toFixed(1)}%`;
    }
    if (key === 'dividend_yield') {
      const pct = val <= 1.0 ? (val * 100).toFixed(2) : val.toFixed(2);
      return `${pct}%`;
    }

    // Solvency: Debt-to-Equity Ratio
    if (key === 'debt_to_equity') {
      return `${val.toFixed(2)}%`;
    }

    // Valuation Multiples
    if (['pe_ratio', 'forward_pe', 'price_to_book', 'enterprise_to_ebitda'].includes(key)) {
      return `${val.toFixed(2)}x`;
    }

    // Share Prices and Key Technical Levels
    if (['current_price', 'support_level', 'resistance_level', 'sma_50', 'sma_200'].includes(key)) {
      return `$${val.toFixed(2)} USD`;
    }

    // Percentage Price Changes
    if (['price_change_30d_pct', 'price_change_90d_pct'].includes(key)) {
      return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`;
    }

    return Number.isInteger(val) ? val.toLocaleString() : val.toFixed(2);
  }
  return String(val);
}

function parseExecutiveSummary(summary) {
  if (!summary) return { numberedPoints: [], thesis: null, otherText: null };
  const lines = summary.split(/\n\n+/).map((l) => l.trim()).filter(Boolean);

  const numberedPoints = [];
  let thesis = null;
  const remaining = [];

  for (const line of lines) {
    if (
      line.startsWith('FinCrew Investment Committee Consensus') ||
      line.startsWith('Consensus Rating:')
    ) {
      continue; // Handled in banner and page header
    }
    const match = line.match(/^(\d+)\.\s*([^:]+):\s*(.*)$/s);
    if (match) {
      numberedPoints.push({
        number: match[1],
        title: match[2].trim(),
        content: match[3].trim(),
      });
      continue;
    }
    if (line.toLowerCase().startsWith('investment thesis:')) {
      thesis = line.replace(/^investment thesis:\s*/i, '').trim();
      continue;
    }
    remaining.push(line);
  }

  return {
    numberedPoints,
    thesis,
    otherText: remaining.length > 0 ? remaining.join('\n\n') : null,
  };
}

export default function ReportView({ sessionId, onBack }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('consensus'); // 'consensus', 'financials', 'technical', 'sentiment', 'risk'
  const [showExportModal, setShowExportModal] = useState(false);

  useEffect(() => {
    loadReportData();
  }, [sessionId]);

  const loadReportData = async () => {
    setLoading(true);
    setError(null);
    try {
      let targetId = sessionId;

      // If no session ID passed directly, load the user's latest completed session
      if (!targetId) {
        const sessionsData = await api.listSessions(10, 0);
        const completed = (sessionsData.sessions || []).find((s) => s.status === 'COMPLETED');
        if (completed) {
          targetId = completed.id;
        } else {
          throw new Error('No completed research reports found in your workspace.');
        }
      }

      const data = await api.getReport(targetId);
      setReport(data);
    } catch (err) {
      setError(err.message || 'Failed to load research report.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fadeIn py-8">
        <div className="h-6 w-48 bg-gray-200/80 rounded-xl animate-pulse" />
        <div className="h-48 bg-white rounded-[28px] border border-gray-100 animate-pulse shadow-sm" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="h-28 bg-white rounded-[22px] border border-gray-100 animate-pulse" />
          <div className="h-28 bg-white rounded-[22px] border border-gray-100 animate-pulse" />
          <div className="h-28 bg-white rounded-[22px] border border-gray-100 animate-pulse" />
        </div>
        <div className="h-96 bg-white rounded-[28px] border border-gray-100 animate-pulse" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="p-12 max-w-xl mx-auto text-center space-y-4 rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] my-8">
        <div className="w-14 h-14 rounded-2xl bg-rose-50 border border-rose-100 text-rose-600 mx-auto flex items-center justify-center">
          <AlertTriangle className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-black text-[#111318]">Report Unavailable</h3>
        <p className="text-xs text-gray-500 leading-relaxed">
          {error || 'Could not find the requested research report.'}
        </p>
        <button
          onClick={onBack}
          className="px-5 py-2.5 rounded-full bg-[#17191F] hover:bg-black text-white text-xs font-black inline-flex items-center gap-2 cursor-pointer transition shadow-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </button>
      </div>
    );
  }

  // Parse structured specialist agent data
  const fundamental = report.fundamental_data || {};
  const marketResearch = fundamental.market_research || {};
  const technical = report.technical_data || {};
  const technicalSup = technical.supporting_data || {};
  const sentiment = report.sentiment_data || {};
  const risk = report.risk_data || {};

  const currentPrice = report.current_price;
  const targetPrice = report.target_price;
  const confidencePct = Math.round((report.confidence_score || 0) * 100);

  let impliedUpside = null;
  if (currentPrice && targetPrice && currentPrice > 0) {
    impliedUpside = Math.round(((targetPrice - currentPrice) / currentPrice) * 1000) / 10;
  }

  // Recommendation Badge Colors
  const rec = report.recommendation || 'HOLD';
  const isStrongBuy = rec === 'STRONG_BUY';
  const isBuy = rec === 'BUY' || isStrongBuy;
  const isSell = rec === 'SELL' || rec === 'STRONG_SELL';

  // Navigation Tabs matching Reference Screenshot 5
  const navTabs = [
    { id: 'consensus', label: 'Consensus', icon: FileText },
    { id: 'financials', label: 'Financials', icon: BarChart3 },
    { id: 'technical', label: 'Technical', icon: TrendingUp },
    { id: 'sentiment', label: 'Sentiment', icon: MessageSquare },
    { id: 'risk', label: 'Risk', icon: Shield },
  ];

  return (
    <div className="space-y-6 sm:space-y-7 animate-fadeIn">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center gap-2 text-xs font-bold text-gray-500">
        <button
          onClick={onBack}
          className="hover:text-[#111318] transition cursor-pointer flex items-center gap-1.5"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Research Sessions</span>
        </button>
        <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
        <span className="text-gray-400 font-medium">Session #{report.session_id}</span>
        <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
        <span className="text-[#111318] font-black">{report.ticker}</span>
      </div>

      {/* Main Grid: Left Column (Hero + Price Summary + Tabs + Tab Content) & Right Column (Export + Summary + Highlights) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* LEFT COLUMN (lg:col-span-8) */}
        <div className="lg:col-span-8 space-y-6">
          {/* HERO STOCK DOSSIER CARD matching Screenshot 5 */}
          <div className="p-6 sm:p-7 rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            {/* Left: Logo, Ticker, Company, Sector/Industry */}
            <div className="flex items-start gap-4 sm:gap-5">
              <StockLogo ticker={report.ticker} size="xl" />
              <div className="space-y-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
                    {report.ticker}
                  </span>
                  <h2 className="text-xl sm:text-2xl font-black text-[#111318] tracking-tight">
                    {report.company_name}
                  </h2>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs text-gray-500 font-semibold pt-0.5">
                  <span>{marketResearch.sector || 'Technology'}</span>
                  <span className="text-gray-300">•</span>
                  <span>{marketResearch.industry || 'Equities'}</span>
                  <span className="text-gray-300">•</span>
                  <span className="px-2.5 py-0.5 rounded-full bg-gray-100 border border-gray-200/60 text-gray-700 font-bold text-[11px]">
                    {marketResearch.market_cap_category || 'Mega-Cap'}
                  </span>
                </div>
              </div>
            </div>

            {/* Right: Committee Rating Badge & Confidence */}
            <div className="flex items-center gap-6 self-start sm:self-auto shrink-0 pt-2 sm:pt-0">
              <div className="text-center space-y-1">
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-wider block">
                  Committee Rating
                </span>
                <span
                  className={`inline-block px-4 py-1.5 rounded-full text-xs font-black tracking-wide shadow-xs ${
                    isBuy
                      ? 'bg-[#C5F500] text-[#111318]'
                      : isSell
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}
                >
                  {rec.replace('_', ' ')}
                </span>
              </div>

              <div className="text-center space-y-1 border-l border-gray-100 pl-6">
                <span className="text-[10px] font-black text-gray-400 uppercase tracking-wider block">
                  Confidence
                </span>
                <span className="text-2xl font-black text-[#111318] tracking-tight block">
                  {confidencePct}%
                </span>
              </div>
            </div>
          </div>

          {/* THREE PRICE SUMMARY CARDS matching Screenshot 5 */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Card 1: Current Market Price */}
            <div className="p-5 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] space-y-2">
              <div className="flex items-center gap-2 text-gray-400">
                <LineChart className="w-4 h-4 text-gray-500" />
                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                  Current Market Price
                </span>
              </div>
              <div className="text-2xl font-black text-[#111318] tracking-tight">
                {currentPrice !== null && currentPrice !== undefined
                  ? `$${currentPrice.toFixed(2)} USD`
                  : 'Unavailable'}
              </div>
            </div>

            {/* Card 2: 12-Month Target Price */}
            <div className="p-5 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] space-y-2">
              <div className="flex items-center gap-2 text-gray-400">
                <Target className="w-4 h-4 text-[#2E7D32]" />
                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                  12-Month Target Price
                </span>
              </div>
              <div className="text-2xl font-black text-[#2E7D32] tracking-tight">
                {targetPrice !== null && targetPrice !== undefined
                  ? `$${targetPrice.toFixed(2)} USD`
                  : 'Unavailable'}
              </div>
            </div>

            {/* Card 3: Implied Return Potential */}
            <div className="p-5 rounded-[22px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] space-y-2">
              <div className="flex items-center gap-2 text-gray-400">
                <ArrowUpRight className="w-4 h-4 text-[#2E7D32]" />
                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider">
                  Implied Return Potential
                </span>
              </div>
              <div
                className={`text-2xl font-black tracking-tight ${
                  impliedUpside !== null && impliedUpside >= 0
                    ? 'text-[#2E7D32]'
                    : impliedUpside !== null
                    ? 'text-rose-600'
                    : 'text-gray-400 font-medium text-lg'
                }`}
              >
                {impliedUpside !== null
                  ? `${impliedUpside >= 0 ? '+' : ''}${impliedUpside}%`
                  : 'Unavailable'}
              </div>
            </div>
          </div>

          {/* REPORT NAVIGATION TABS matching Screenshot 5 */}
          <div className="flex flex-wrap items-center gap-2 p-1 rounded-full bg-white border border-gray-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.02)] w-fit">
            {navTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-5 py-2.5 rounded-full text-xs font-black transition flex items-center gap-2 cursor-pointer whitespace-nowrap ${
                    isActive
                      ? 'bg-[#C5F500] text-[#111318] shadow-xs'
                      : 'text-gray-600 hover:text-[#111318]'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* TAB 1: CONSENSUS TAB CONTENT */}
          {activeTab === 'consensus' && (() => {
            const summaryData = parseExecutiveSummary(report.executive_summary);
            return (
              <div className="rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 space-y-6">
                {/* Header */}
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0 mt-0.5">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                      Executive Consensus Narrative
                    </h3>
                    <p className="text-xs text-gray-500 font-medium">
                      FinCrew Investment Committee Consensus for {report.company_name} ({report.ticker}).
                    </p>
                  </div>
                </div>

                {/* Horizontal Consensus Summary Capsule Banner (Responsive & Wrap-Friendly) */}
                <div className="p-3.5 px-4 rounded-2xl bg-[#E8F8EA] border border-[#C3E6CB] text-xs font-bold text-gray-800 flex flex-wrap items-center gap-x-4 gap-y-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-gray-500 font-medium">Consensus:</span>
                    <strong className="text-[#1E7E34] font-black">{rec.replace('_', ' ')}</strong>
                  </div>
                  <span className="text-gray-300 hidden sm:inline">|</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-gray-500 font-medium">Confidence:</span>
                    <strong className="text-[#1E7E34] font-black">{confidencePct}%</strong>
                  </div>
                  <span className="text-gray-300 hidden sm:inline">|</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-gray-500 font-medium">Current:</span>
                    <strong className="text-[#111318] font-black">
                      {currentPrice !== null ? `$${currentPrice.toFixed(2)}` : 'Unavailable'}
                    </strong>
                  </div>
                  <span className="text-gray-300 hidden sm:inline">|</span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-gray-500 font-medium">Target:</span>
                    <strong className="text-[#111318] font-black">
                      {targetPrice !== null ? `$${targetPrice.toFixed(2)}` : 'Unavailable'}
                    </strong>
                  </div>
                </div>

                {/* Structured Synthesis Narrative Highlights */}
                {summaryData.numberedPoints.length > 0 ? (
                  <div className="space-y-4 pt-1">
                    {summaryData.numberedPoints.map((pt) => (
                      <div key={pt.number} className="flex items-start gap-3.5">
                        <div className="w-6 h-6 rounded-full bg-[#C5F500]/30 text-[#111318] font-black text-xs flex items-center justify-center shrink-0 mt-0.5">
                          {pt.number}
                        </div>
                        <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-medium">
                          <strong className="text-[#111318] font-black">{pt.title}: </strong>
                          {pt.content}
                        </p>
                      </div>
                    ))}

                    {/* Prominent Investment Thesis Card */}
                    {summaryData.thesis && (
                      <div className="p-4 sm:p-5 rounded-2xl bg-[#F0F6FE] border border-[#DCE7F6] space-y-1.5 mt-2">
                        <div className="flex items-center gap-2 text-xs font-black text-[#111318] uppercase tracking-wider">
                          <Sparkles className="w-4 h-4 text-emerald-600" />
                          <span>Investment Thesis</span>
                        </div>
                        <p className="text-xs sm:text-sm text-gray-800 font-medium leading-relaxed">
                          {summaryData.thesis}
                        </p>
                      </div>
                    )}

                    {/* Any Additional Contextual Text */}
                    {summaryData.otherText && (
                      <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-normal whitespace-pre-line bg-gray-50/70 p-4 sm:p-5 rounded-2xl border border-gray-100">
                        {summaryData.otherText}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="pt-1">
                    <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-normal whitespace-pre-line bg-gray-50/70 p-4 sm:p-5 rounded-2xl border border-gray-100">
                      {report.executive_summary || 'Executive consensus narrative unavailable.'}
                    </p>
                  </div>
                )}

                {/* Committee Supporting Evidence Summary Table */}
                <div className="pt-2 border-t border-gray-100 space-y-3">
                  <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Cross-Specialist Supporting Evidence
                  </h5>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                      <span className="text-gray-400 font-bold block">Trailing P/E</span>
                      <span className="font-black text-sm text-[#111318] mt-0.5 block">
                        {fundamental.supporting_data?.pe_ratio
                          ? `${fundamental.supporting_data.pe_ratio.toFixed(2)}x`
                          : 'Unavailable'}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                      <span className="text-gray-400 font-bold block">Free Cash Flow</span>
                      <span className="font-black text-sm text-[#111318] mt-0.5 block">
                        {formatSupportingMetric('free_cash_flow', fundamental.supporting_data?.free_cash_flow)}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                      <span className="text-gray-400 font-bold block">RSI (14-Day)</span>
                      <span className="font-black text-sm text-[#111318] mt-0.5 block">
                        {technicalSup.rsi_14 ? technicalSup.rsi_14.toFixed(1) : 'Unavailable'}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                      <span className="text-gray-400 font-bold block">Risk Severity</span>
                      <span className="font-black text-sm text-[#111318] mt-0.5 block">
                        {risk.risk_score ? `${risk.risk_score.toFixed(1)} / 10` : 'Unavailable'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* TAB 2: FINANCIALS TAB CONTENT */}
          {activeTab === 'financials' && (
            <div className="rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 space-y-6">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0 mt-0.5">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                    Financial Valuation & Fundamentals
                  </h3>
                  <p className="text-xs text-gray-500 font-medium">
                    Valuation multiples, profitability margins, cash flows, and balance sheet solvency
                  </p>
                </div>
              </div>

              {/* 4 Financial KPI Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Valuation Status</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {fundamental.valuation_status?.replace('_', ' ') || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Profitability Grade</span>
                  <span className="font-black text-sm text-emerald-700 block">
                    {fundamental.profitability_grade || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Solvency Risk</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {fundamental.solvency_risk || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Financial Health</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {fundamental.financial_health_score !== undefined && fundamental.financial_health_score !== null
                      ? `${fundamental.financial_health_score} / 100`
                      : 'Unavailable'}
                  </span>
                </div>
              </div>

              {/* Detailed Financial Multiples & Cash Flow Grid */}
              <div className="space-y-3 pt-2 border-t border-gray-100">
                <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  Quantitative Valuation & Balance Sheet Metrics
                </h5>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {[
                    { label: 'Trailing P/E Ratio', key: 'pe_ratio' },
                    { label: 'Forward P/E Ratio', key: 'forward_pe' },
                    { label: 'Price to Book (P/B)', key: 'price_to_book' },
                    { label: 'Free Cash Flow', key: 'free_cash_flow' },
                    { label: 'Total Cash', key: 'total_cash' },
                    { label: 'Total Debt', key: 'total_debt' },
                    { label: 'Debt to Equity', key: 'debt_to_equity' },
                    { label: 'Profit Margin', key: 'profit_margins' },
                    { label: 'Operating Margin', key: 'operating_margins' },
                    { label: 'Total Revenue', key: 'total_revenue' },
                    { label: 'EBITDA', key: 'ebitda' },
                    { label: 'Dividend Yield', key: 'dividend_yield' },
                  ].map((m) => {
                    const sup = fundamental.supporting_data || {};
                    const rawVal = sup[m.key];
                    return (
                      <div key={m.key} className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                        <span className="text-gray-400 block truncate">{m.label}</span>
                        <span className="font-black text-sm text-[#111318] mt-0.5 block truncate">
                          {formatSupportingMetric(m.key, rawVal)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Specialist Narrative Analysis */}
              <div className="space-y-2 pt-2 border-t border-gray-100">
                <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  Specialist Financial Analysis
                </h5>
                <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-normal whitespace-pre-line bg-gray-50/70 p-4 sm:p-5 rounded-2xl border border-gray-100">
                  {fundamental.analysis || 'Fundamental valuation narrative unavailable.'}
                </p>
              </div>

              {/* Specialist Key Findings */}
              {fundamental.key_findings && fundamental.key_findings.length > 0 && (
                <div className="space-y-2.5 pt-2 border-t border-gray-100">
                  <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Key Valuation Findings
                  </h5>
                  <ul className="space-y-2">
                    {fundamental.key_findings.map((f, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-gray-700 font-medium">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warnings and Limitations */}
              {fundamental.warnings_and_limitations && fundamental.warnings_and_limitations.length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/80 space-y-2">
                  <h5 className="text-xs font-black text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                    <span>Valuation Warnings & Limitations</span>
                  </h5>
                  <ul className="space-y-1.5 text-xs text-amber-800">
                    {fundamental.warnings_and_limitations.map((w, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: TECHNICAL TAB CONTENT */}
          {activeTab === 'technical' && (
            <div className="rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 space-y-6">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0 mt-0.5">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                    Technical Signals & Momentum Analysis
                  </h3>
                  <p className="text-xs text-gray-500 font-medium">
                    Moving average posture, RSI oscillator, support/resistance levels, and directional bias
                  </p>
                </div>
              </div>

              {/* 4 Technical KPI Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Trend Direction</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {technical.trend_direction || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Momentum State</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {technical.momentum_state || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">RSI-14 (Daily)</span>
                  <span className="font-black text-sm text-emerald-700 block">
                    {technicalSup.rsi_14 !== null && technicalSup.rsi_14 !== undefined
                      ? technicalSup.rsi_14.toFixed(1)
                      : 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Key Support Level</span>
                  <span className="font-black text-sm text-emerald-700 block">
                    {technical.key_support ? `$${technical.key_support.toFixed(2)} USD` : 'Unavailable'}
                  </span>
                </div>
              </div>

              {/* Key Technical Boundary Levels */}
              <div className="space-y-3 pt-2 border-t border-gray-100">
                <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  Quantitative Technical Indicators & Price Moving Averages
                </h5>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                    <span className="text-gray-400 block truncate">Key Resistance Level</span>
                    <span className="font-black text-sm text-rose-700 mt-0.5 block truncate">
                      {technical.key_resistance ? `$${technical.key_resistance.toFixed(2)} USD` : 'Unavailable'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                    <span className="text-gray-400 block truncate">SMA-50 (50-Day)</span>
                    <span className="font-black text-sm text-[#111318] mt-0.5 block truncate">
                      {technicalSup.sma_50 ? `$${technicalSup.sma_50.toFixed(2)} USD` : 'Unavailable'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                    <span className="text-gray-400 block truncate">SMA-200 (200-Day)</span>
                    <span className="font-black text-sm text-[#111318] mt-0.5 block truncate">
                      {technicalSup.sma_200 ? `$${technicalSup.sma_200.toFixed(2)} USD` : 'Unavailable'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                    <span className="text-gray-400 block truncate">30-Day Return</span>
                    <span
                      className={`font-black text-sm mt-0.5 block truncate ${
                        technicalSup.price_change_30d_pct >= 0 ? 'text-emerald-700' : 'text-rose-700'
                      }`}
                    >
                      {technicalSup.price_change_30d_pct !== null && technicalSup.price_change_30d_pct !== undefined
                        ? `${technicalSup.price_change_30d_pct >= 0 ? '+' : ''}${technicalSup.price_change_30d_pct.toFixed(2)}%`
                        : 'Unavailable'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                    <span className="text-gray-400 block truncate">90-Day Return</span>
                    <span
                      className={`font-black text-sm mt-0.5 block truncate ${
                        technicalSup.price_change_90d_pct >= 0 ? 'text-emerald-700' : 'text-rose-700'
                      }`}
                    >
                      {technicalSup.price_change_90d_pct !== null && technicalSup.price_change_90d_pct !== undefined
                        ? `${technicalSup.price_change_90d_pct >= 0 ? '+' : ''}${technicalSup.price_change_90d_pct.toFixed(2)}%`
                        : 'Unavailable'}
                    </span>
                  </div>

                  <div className="p-3.5 rounded-xl bg-gray-50 border border-gray-100 text-xs">
                    <span className="text-gray-400 block truncate">Sample Bars Analyzed</span>
                    <span className="font-black text-sm text-[#111318] mt-0.5 block truncate">
                      {technicalSup.history_bars_analyzed ? `${technicalSup.history_bars_analyzed} daily bars` : '30 bars'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Specialist Narrative Analysis */}
              <div className="space-y-2 pt-2 border-t border-gray-100">
                <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  Specialist Technical Analysis
                </h5>
                <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-normal whitespace-pre-line bg-gray-50/70 p-4 sm:p-5 rounded-2xl border border-gray-100">
                  {technical.analysis || 'Technical narrative analysis unavailable.'}
                </p>
              </div>

              {/* Specialist Key Findings */}
              {technical.key_findings && technical.key_findings.length > 0 && (
                <div className="space-y-2.5 pt-2 border-t border-gray-100">
                  <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Key Technical Signals
                  </h5>
                  <ul className="space-y-2">
                    {technical.key_findings.map((f, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-gray-700 font-medium">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Warnings and Limitations */}
              {technical.warnings_and_limitations && technical.warnings_and_limitations.length > 0 && (
                <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/80 space-y-2">
                  <h5 className="text-xs font-black text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                    <span>Technical Indicator Caveats</span>
                  </h5>
                  <ul className="space-y-1.5 text-xs text-amber-800">
                    {technical.warnings_and_limitations.map((w, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: SENTIMENT TAB CONTENT */}
          {activeTab === 'sentiment' && (
            <div className="rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 space-y-6">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0 mt-0.5">
                  <MessageSquare className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                    Market Sentiment & Catalysts
                  </h3>
                  <p className="text-xs text-gray-500 font-medium">
                    Autonomous NLP news media analysis, public sentiment scoring, and catalyst tracking
                  </p>
                </div>
              </div>

              {/* 3 Sentiment KPI Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Media Stance</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {sentiment.sentiment_label?.replace('_', ' ') || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Sentiment Score (-1 to +1)</span>
                  <span className="font-black text-sm text-emerald-700 block">
                    {sentiment.sentiment_score !== undefined && sentiment.sentiment_score !== null
                      ? sentiment.sentiment_score > 0
                        ? `+${sentiment.sentiment_score.toFixed(2)}`
                        : sentiment.sentiment_score.toFixed(2)
                      : 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Publications Sampled</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {sentiment.news_sample_size || 0} financial articles
                  </span>
                </div>
              </div>

              {/* Specialist Narrative Analysis */}
              <div className="space-y-2 pt-2 border-t border-gray-100">
                <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  Specialist Sentiment Analysis
                </h5>
                <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-normal whitespace-pre-line bg-gray-50/70 p-4 sm:p-5 rounded-2xl border border-gray-100">
                  {sentiment.analysis || 'Sentiment narrative analysis unavailable.'}
                </p>
              </div>

              {/* Positive Catalysts vs Negative Concerns Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-gray-100">
                {/* Positive Catalysts */}
                <div className="p-4 rounded-2xl bg-[#E8F8EA] border border-[#C3E6CB] space-y-2">
                  <h5 className="text-xs font-black text-[#1E7E34] uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-[#1E7E34]" />
                    <span>Positive Growth Catalysts</span>
                  </h5>
                  <ul className="space-y-1.5 text-xs text-gray-700 font-medium">
                    {sentiment.positive_catalysts && sentiment.positive_catalysts.length > 0 ? (
                      sentiment.positive_catalysts.map((c, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-[#1E7E34] font-bold">•</span>
                          <span>{c}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-gray-500 italic">No positive catalysts flagged.</li>
                    )}
                  </ul>
                </div>

                {/* Negative Concerns */}
                <div className="p-4 rounded-2xl bg-rose-50/70 border border-rose-200/80 space-y-2">
                  <h5 className="text-xs font-black text-rose-800 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Headline & Market Concerns</span>
                  </h5>
                  <ul className="space-y-1.5 text-xs text-gray-700 font-medium">
                    {sentiment.negative_concerns && sentiment.negative_concerns.length > 0 ? (
                      sentiment.negative_concerns.map((c, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-rose-500 font-bold">•</span>
                          <span>{c}</span>
                        </li>
                      ))
                    ) : (
                      <li className="text-gray-500 italic">No negative headline concerns flagged.</li>
                    )}
                  </ul>
                </div>
              </div>

              {/* Specialist Key Findings */}
              {sentiment.key_findings && sentiment.key_findings.length > 0 && (
                <div className="space-y-2.5 pt-2 border-t border-gray-100">
                  <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Key Sentiment Findings
                  </h5>
                  <ul className="space-y-2">
                    {sentiment.key_findings.map((f, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-gray-700 font-medium">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* TAB 5: RISK TAB CONTENT */}
          {activeTab === 'risk' && (
            <div className="rounded-[28px] bg-white border border-gray-100 shadow-[0_4px_24px_rgba(0,0,0,0.03)] p-6 sm:p-7 space-y-6">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-xl bg-gray-100/80 border border-gray-200/60 flex items-center justify-center text-[#111318] shrink-0 mt-0.5">
                  <Shield className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base sm:text-lg font-black text-[#111318] tracking-tight">
                    Risk Severity & Bear Case Stress Test
                  </h3>
                  <p className="text-xs text-gray-500 font-medium">
                    Downside risk classification, capital preservation analysis, and stress testing
                  </p>
                </div>
              </div>

              {/* 3 Risk KPI Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Risk Classification</span>
                  <span className="font-black text-sm text-[#111318] block">
                    {risk.risk_level || 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Risk Severity Score (0-10)</span>
                  <span className="font-black text-sm text-rose-700 block">
                    {risk.risk_score !== undefined && risk.risk_score !== null
                      ? `${risk.risk_score.toFixed(1)} / 10`
                      : 'Unavailable'}
                  </span>
                </div>

                <div className="p-4 rounded-2xl bg-gray-50 border border-gray-100 text-xs space-y-1">
                  <span className="text-gray-400 font-bold block">Capital Protection Status</span>
                  <span className="font-black text-sm text-emerald-700 block">
                    ACTIVE MONITORING
                  </span>
                </div>
              </div>

              {/* Bear Case Scenario Card */}
              {risk.bear_case_scenario && (
                <div className="p-4 sm:p-5 rounded-2xl bg-rose-50/60 border border-rose-200/80 space-y-2">
                  <h5 className="text-xs font-black text-rose-900 uppercase tracking-wider flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4 text-rose-600" />
                    <span>Bear Case Stress Test Scenario</span>
                  </h5>
                  <p className="text-xs sm:text-sm text-rose-950 leading-relaxed font-medium">
                    {risk.bear_case_scenario}
                  </p>
                </div>
              )}

              {/* Primary Risk Factors */}
              {risk.primary_risk_factors && risk.primary_risk_factors.length > 0 && (
                <div className="space-y-2.5 pt-2 border-t border-gray-100">
                  <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Primary Downside Risk Factors
                  </h5>
                  <ul className="space-y-2">
                    {risk.primary_risk_factors.map((rf, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-gray-700 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0 mt-1.5" />
                        <span>{rf}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Specialist Narrative Analysis */}
              <div className="space-y-2 pt-2 border-t border-gray-100">
                <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                  Specialist Risk Analysis
                </h5>
                <p className="text-xs sm:text-sm text-gray-700 leading-relaxed font-normal whitespace-pre-line bg-gray-50/70 p-4 sm:p-5 rounded-2xl border border-gray-100">
                  {risk.analysis || 'Risk assessment narrative unavailable.'}
                </p>
              </div>

              {/* Specialist Key Findings */}
              {risk.key_findings && risk.key_findings.length > 0 && (
                <div className="space-y-2.5 pt-2 border-t border-gray-100">
                  <h5 className="text-[11px] font-black text-gray-400 uppercase tracking-wider">
                    Key Risk Findings
                  </h5>
                  <ul className="space-y-2">
                    {risk.key_findings.map((f, i) => (
                      <li key={i} className="flex items-start gap-2.5 text-xs text-gray-700 font-medium">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* RIGHT COLUMN (lg:col-span-4) matching Screenshot 5 */}
        <div className="lg:col-span-4 space-y-6">
          {/* EXPORT REPORT ACTION BUTTON matching Screenshot 5 */}
          <button
            onClick={() => setShowExportModal(true)}
            className="w-full h-12 px-6 rounded-2xl bg-[#17191F] hover:bg-black active:scale-[0.98] text-white font-black text-xs flex items-center justify-center gap-2.5 transition shadow-xs cursor-pointer"
          >
            <Download className="w-4 h-4 text-[#C5F500]" />
            <span>Export Report (PDF / JSON / HTML / MD)</span>
          </button>

          {/* CARD 1: REPORT SUMMARY matching Screenshot 5 */}
          <div className="p-6 rounded-[26px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] space-y-4">
            <div className="flex items-center gap-2.5">
              <FileText className="w-4 h-4 text-[#111318]" />
              <h4 className="text-sm font-black text-[#111318]">
                Report Summary
              </h4>
            </div>

            <div className="space-y-3 pt-2 text-xs divide-y divide-gray-100">
              <div className="flex items-center justify-between pb-1">
                <span className="text-gray-400 font-bold">Consensus Rating</span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-black ${
                    isBuy
                      ? 'bg-[#C5F500] text-[#111318]'
                      : isSell
                      ? 'bg-rose-50 text-rose-700 border border-rose-200'
                      : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }`}
                >
                  {rec.replace('_', ' ')}
                </span>
              </div>

              <div className="flex items-center justify-between pt-3">
                <span className="text-gray-400 font-bold">Confidence Level</span>
                <span className="font-black text-sm text-[#111318]">
                  {confidencePct}%
                </span>
              </div>

              <div className="flex items-center justify-between pt-3">
                <span className="text-gray-400 font-bold">Current Price</span>
                <span className="font-black text-sm text-[#111318]">
                  {currentPrice !== null && currentPrice !== undefined
                    ? `$${currentPrice.toFixed(2)}`
                    : 'Unavailable'}
                </span>
              </div>

              <div className="flex items-center justify-between pt-3">
                <span className="text-gray-400 font-bold">Target Price (12-Mo)</span>
                <span className="font-black text-sm text-[#2E7D32]">
                  {targetPrice !== null && targetPrice !== undefined
                    ? `$${targetPrice.toFixed(2)}`
                    : 'Unavailable'}
                </span>
              </div>

              <div className="flex items-center justify-between pt-3">
                <span className="text-gray-400 font-bold">Implied Upside</span>
                <span
                  className={`font-black text-sm ${
                    impliedUpside !== null && impliedUpside >= 0
                      ? 'text-[#2E7D32]'
                      : impliedUpside !== null
                      ? 'text-rose-600'
                      : 'text-gray-400 font-normal italic'
                  }`}
                >
                  {impliedUpside !== null
                    ? `${impliedUpside >= 0 ? '+' : ''}${impliedUpside}%`
                    : 'Unavailable'}
                </span>
              </div>
            </div>
          </div>

          {/* CARD 2: KEY HIGHLIGHTS matching Screenshot 5 */}
          <div className="p-6 rounded-[26px] bg-white border border-gray-100 shadow-[0_4px_20px_rgba(0,0,0,0.02)] space-y-4">
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-[#111318]" />
              <h4 className="text-sm font-black text-[#111318]">
                Key Highlights
              </h4>
            </div>

            <div className="space-y-3 pt-1 text-xs">
              {/* Highlight 1: Market Profile */}
              <div className="flex items-start gap-2.5">
                <div className="w-4 h-4 rounded-full bg-[#E8F8EA] border border-[#C3E6CB] text-[#1E7E34] flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3 h-3 text-[#1E7E34]" />
                </div>
                <p className="text-gray-700 font-medium leading-relaxed">
                  <strong className="text-[#111318] font-bold">
                    {marketResearch.market_cap_category || 'Large-Cap'} equity
                  </strong>{' '}
                  positioned in {marketResearch.sector || 'diversified'} sector
                  {marketResearch.industry ? ` (${marketResearch.industry})` : ''}.
                </p>
              </div>

              {/* Highlight 2: Fundamental Valuation */}
              <div className="flex items-start gap-2.5">
                <div className="w-4 h-4 rounded-full bg-[#E8F8EA] border border-[#C3E6CB] text-[#1E7E34] flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3 h-3 text-[#1E7E34]" />
                </div>
                <p className="text-gray-700 font-medium leading-relaxed">
                  Valuation evaluated as{' '}
                  <strong className="text-[#111318] font-bold">
                    {fundamental.valuation_status?.replace('_', ' ') || 'fairly valued'}
                  </strong>{' '}
                  with {fundamental.profitability_grade?.toLowerCase() || 'solid'} profitability and{' '}
                  {fundamental.solvency_risk?.toLowerCase() || 'low'} solvency risk.
                </p>
              </div>

              {/* Highlight 3: Technical Signals */}
              <div className="flex items-start gap-2.5">
                <div className="w-4 h-4 rounded-full bg-[#E8F8EA] border border-[#C3E6CB] text-[#1E7E34] flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3 h-3 text-[#1E7E34]" />
                </div>
                <p className="text-gray-700 font-medium leading-relaxed">
                  Technical posture is{' '}
                  <strong className="text-[#111318] font-bold">
                    {technical.trend_direction?.toLowerCase() || 'neutral'}
                  </strong>{' '}
                  with {technical.momentum_state?.toLowerCase() || 'steady'} momentum
                  {technicalSup.rsi_14 ? ` (RSI-14: ${technicalSup.rsi_14.toFixed(1)})` : ''}.
                </p>
              </div>

              {/* Highlight 4: Sentiment & Risk */}
              <div className="flex items-start gap-2.5">
                <div className="w-4 h-4 rounded-full bg-[#E8F8EA] border border-[#C3E6CB] text-[#1E7E34] flex items-center justify-center shrink-0 mt-0.5">
                  <CheckCircle2 className="w-3 h-3 text-[#1E7E34]" />
                </div>
                <p className="text-gray-700 font-medium leading-relaxed">
                  Media sentiment scores{' '}
                  <strong className="text-[#111318] font-bold">
                    {sentiment.sentiment_label?.replace('_', ' ').toLowerCase() || 'constructive'}
                  </strong>{' '}
                  with {risk.risk_level?.toLowerCase() || 'balanced'} risk severity
                  {risk.risk_score !== undefined && risk.risk_score !== null
                    ? ` (${risk.risk_score.toFixed(1)}/10)`
                    : ''}.
                </p>
              </div>
            </div>
          </div>

          {/* Investment Disclaimer Footer Card */}
          <div className="p-4 rounded-2xl bg-gray-100/80 border border-gray-200/60 text-[11px] text-gray-500 flex items-start gap-2.5 leading-relaxed">
            <Info className="w-4 h-4 text-gray-400 shrink-0 mt-0.5" />
            <p>
              <strong className="text-gray-700 font-bold">Disclaimer: </strong>
              FinCrew research dossiers synthesize quantitative market feeds and multi-agent AI assessments. All target prices, confidence levels, and committee ratings are for institutional analytical purposes and do not constitute personal financial advice.
            </p>
          </div>
        </div>
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <ExportModal
          sessionId={report.session_id}
          ticker={report.ticker}
          companyName={report.company_name}
          onClose={() => setShowExportModal(false)}
        />
      )}
    </div>
  );
}
