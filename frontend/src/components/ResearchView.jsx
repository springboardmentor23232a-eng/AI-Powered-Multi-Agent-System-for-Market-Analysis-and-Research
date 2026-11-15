import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  BarChart2,
  Database,
  LineChart,
  MessageSquareText,
  Layers,
  Loader2,
  Check,
} from 'lucide-react';
import { api } from '../api/client';
import StockLogo from './StockLogo';

export default function ResearchView({ initialSessionId = null, onViewReport }) {
  const [ticker, setTicker] = useState('AAPL');
  const [activeSession, setActiveSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const pollIntervalRef = useRef(null);

  const quickTickers = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'TSLA'];

  // Load initial session if provided from dashboard/history
  useEffect(() => {
    if (initialSessionId) {
      loadSession(initialSessionId);
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [initialSessionId]);

  const loadSession = async (sessionId) => {
    try {
      const session = await api.getSession(sessionId);
      setActiveSession(session);
      if (session.status === 'PENDING' || session.status === 'IN_PROGRESS') {
        startPolling(sessionId);
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to load research session.');
    }
  };

  const startPolling = (sessionId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setPolling(true);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const session = await api.getSession(sessionId);
        setActiveSession(session);

        if (session.status === 'COMPLETED' || session.status === 'FAILED') {
          clearInterval(pollIntervalRef.current);
          setPolling(false);
        }
      } catch {
        clearInterval(pollIntervalRef.current);
        setPolling(false);
      }
    }, 2000);
  };

  const handleStartAnalysis = async (customTicker = null) => {
    const targetTicker = (customTicker || ticker).trim().toUpperCase();

    if (!targetTicker) {
      setErrorMessage('Please enter a valid stock ticker symbol.');
      return;
    }

    if (!/^[A-Z0-9.-]{1,10}$/.test(targetTicker)) {
      setErrorMessage('Invalid ticker format. Please enter 1-10 alphanumeric characters (e.g. AAPL, BRK.B).');
      return;
    }

    setErrorMessage(null);
    setLoading(true);

    try {
      // Initiate analysis via POST /api/research/analyze
      const session = await api.startAnalysis(targetTicker, false);
      setActiveSession(session);
      setLoading(false);
      startPolling(session.id);
    } catch (err) {
      setErrorMessage(err.message || 'Failed to initiate research analysis.');
      setLoading(false);
    }
  };

  const isCompleted = activeSession?.status === 'COMPLETED';
  const isInProgress = polling || loading || activeSession?.status === 'IN_PROGRESS' || activeSession?.status === 'PENDING';
  const isFailed = activeSession?.status === 'FAILED';

  // 5 Specialist Agents specification matching reference image 2
  const specialistAgents = [
    {
      id: 'market',
      name: 'Market Research',
      subtitle: 'Price, volume, market trend',
      icon: BarChart2,
      cardBg: 'bg-[#F2FAF4]',
      border: 'border-[#E0F2E4]',
      iconColor: 'text-emerald-700',
    },
    {
      id: 'financial',
      name: 'Financial Valuation',
      subtitle: 'Ratios, DCF, fundamentals',
      icon: Database,
      cardBg: 'bg-[#F0F6FE]',
      border: 'border-[#D9E8FC]',
      iconColor: 'text-blue-700',
    },
    {
      id: 'technical',
      name: 'Technical Signals',
      subtitle: 'Indicators, patterns, entry/exit',
      icon: LineChart,
      cardBg: 'bg-[#F5F3FF]',
      border: 'border-[#E9E5FC]',
      iconColor: 'text-purple-700',
    },
    {
      id: 'sentiment',
      name: 'Sentiment Catalysts',
      subtitle: 'News, earnings, public sentiment',
      icon: MessageSquareText,
      cardBg: 'bg-[#FDF8EE]',
      border: 'border-[#FDEECF]',
      iconColor: 'text-amber-700',
    },
    {
      id: 'risk',
      name: 'Risk Severity',
      subtitle: 'Volatility, drawdown, stress test',
      icon: ShieldCheck,
      cardBg: 'bg-[#FDF2F4]',
      border: 'border-[#FCDCE1]',
      iconColor: 'text-rose-700',
    },
  ];

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* 1. STOCK EQUITY RESEARCH PIPELINE CARD */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#DCE7F6] shadow-xs space-y-6">
        <div>
          <h2 className="text-2xl sm:text-3xl font-black text-[#111318] tracking-tight">
            Stock Equity Research Pipeline
          </h2>
        </div>

        {/* Ticker Search & Analyze Input Group */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleStartAnalysis();
          }}
          className="space-y-4"
        >
          <div>
            <label
              htmlFor="stock-ticker"
              className="text-[11px] font-bold text-[#64748B] uppercase tracking-wider block mb-2"
            >
              Stock Ticker Symbol
            </label>

            <div className="flex flex-col sm:flex-row items-stretch gap-3">
              <div className="relative flex-1">
                <Search className="w-5 h-5 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                <input
                  id="stock-ticker"
                  type="text"
                  placeholder="Enter ticker (e.g. AAPL, NVDA, MSFT)"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  disabled={isInProgress}
                  className="w-full h-12 sm:h-13 pl-12 pr-4 rounded-full border border-[#DCE7F6] bg-white text-base sm:text-lg font-black text-[#111318] placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#C5F500] shadow-xs disabled:opacity-50 tracking-wider"
                />
              </div>

              <button
                type="submit"
                disabled={isInProgress || !ticker.trim()}
                className="h-12 sm:h-13 px-7 rounded-full bg-[#C5F500] hover:bg-[#b8e600] active:scale-98 text-[#111318] font-black text-sm flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer disabled:opacity-50 shrink-0"
              >
                {isInProgress ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin stroke-[2.5]" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 stroke-[2.5]" />
                    <span>Analyze Stock</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick Picks Row */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="font-bold text-[#64748B] mr-1">Quick Picks:</span>
            {quickTickers.map((t) => {
              const isSelected = ticker.toUpperCase() === t;
              return (
                <button
                  key={t}
                  type="button"
                  onClick={() => {
                    setTicker(t);
                    handleStartAnalysis(t);
                  }}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-black transition-all flex items-center gap-1.5 cursor-pointer ${
                    isSelected
                      ? 'bg-[#C5F500] text-[#111318] shadow-xs'
                      : 'bg-gray-100 hover:bg-gray-200/80 text-gray-700'
                  }`}
                >
                  <StockLogo ticker={t} size="xs" />
                  <span>{t}</span>
                </button>
              );
            })}
          </div>
        </form>

        {/* Error message banner */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2.5 animate-fadeIn">
            <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
            <span className="font-semibold">{errorMessage}</span>
          </div>
        )}
      </div>

      {/* 2. MULTI-AGENT ANALYSIS WORKFLOW CARD */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-[#DCE7F6] shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Layers className="w-5 h-5 text-[#111318]" />
            <h3 className="text-lg font-black text-[#111318] tracking-tight">
              Multi-Agent Analysis Workflow
            </h3>
          </div>

          {/* Status Chip */}
          {isInProgress && (
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-xs font-bold text-amber-800 animate-pulse">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Agents Dispatched (Session #{activeSession?.id})</span>
            </div>
          )}

          {isCompleted && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-800">
              <Check className="w-3.5 h-3.5 text-emerald-600 stroke-[3]" />
              <span>Consensus Synthesized</span>
            </div>
          )}
        </div>

        {/* 5 Specialist Agent Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
          {specialistAgents.map((agent) => {
            const Icon = agent.icon;

            return (
              <div
                key={agent.id}
                className={`p-5 rounded-2xl border ${agent.border} ${agent.cardBg} flex flex-col justify-between space-y-4 shadow-2xs transition-all`}
              >
                <div className="flex items-start justify-between">
                  <div className={`p-2.5 rounded-xl bg-white shadow-xs ${agent.iconColor}`}>
                    <Icon className="w-5 h-5" />
                  </div>

                  {/* Completion / Status Checkmark Badge */}
                  <div className="w-6 h-6 rounded-full bg-[#16A34A] text-white flex items-center justify-center shadow-xs">
                    {isInProgress ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                    ) : (
                      <Check className="w-3.5 h-3.5 stroke-[3] text-white" />
                    )}
                  </div>
                </div>

                <div className="space-y-1">
                  <h4 className="text-sm font-black text-[#111318]">
                    {agent.name}
                  </h4>
                  <p className="text-xs text-[#64748B] font-medium leading-relaxed">
                    {agent.subtitle}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Pipeline Completion Banner & Report Action */}
        {isCompleted && activeSession?.report && (
          <div className="p-6 rounded-2xl bg-gradient-to-r from-[#17191F] to-[#232731] text-white flex flex-col sm:flex-row sm:items-center justify-between gap-4 animate-fadeIn shadow-md">
            <div className="flex items-center gap-4">
              <StockLogo ticker={activeSession.ticker} size="lg" />
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-black text-white">
                    {activeSession.ticker}
                  </span>
                  <span className="text-xs text-gray-400 font-medium">
                    {activeSession.company_name}
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-[#C5F500] text-[#111318] text-xs font-black">
                    {activeSession.report.recommendation?.replace('_', ' ')}
                  </span>
                </div>
                <div className="text-xs text-gray-300 mt-1 flex items-center gap-3">
                  <span>Price: ${activeSession.report.current_price?.toFixed(2)}</span>
                  <span>•</span>
                  <span>Target: ${activeSession.report.target_price?.toFixed(2)}</span>
                  <span>•</span>
                  <span>Confidence: {Math.round((activeSession.report.confidence_score || 0) * 100)}%</span>
                </div>
              </div>
            </div>

            <button
              onClick={() => onViewReport(activeSession.id)}
              className="h-11 px-6 rounded-full bg-[#C5F500] hover:bg-[#b8e600] active:scale-98 text-[#111318] font-black text-xs sm:text-sm flex items-center justify-center gap-2 transition-all shadow-md cursor-pointer shrink-0"
            >
              <span>View Consensus Report</span>
              <ArrowRight className="w-4 h-4 stroke-[2.5]" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
