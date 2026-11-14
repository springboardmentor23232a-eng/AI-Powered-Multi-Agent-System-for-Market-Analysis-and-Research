import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { marketAPI } from '../services/api';
import {
  TrendingUp,
  BarChart3,
  Newspaper,
  ShieldAlert,
  Bot,
  Layers,
  ArrowRight,
  CheckCircle2,
  UserPlus,
  LogIn,
  Search,
  Sparkles,
  Zap,
  Globe2,
  RefreshCw,
} from 'lucide-react';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const { isDark } = useTheme();

  // Active Preview Ticker for the Live Interactive Quote Card
  const [selectedTicker, setSelectedTicker] = useState('RELIANCE');
  const [loadingPreview, setLoadingPreview] = useState(false);

  // Dynamic Live Preview Quote from Yahoo Finance (Zero hardcoded data)
  const [livePreview, setLivePreview] = useState({
    ticker: 'RELIANCE',
    company_name: 'Connecting to Live Market Feed...',
    market: 'NSE',
    price: '--',
    change: '0.00%',
    isPositive: true,
    pe_ratio: 'N/A',
    pb_ratio: 'N/A',
    roe: 'N/A',
    high_52w: '--',
    low_52w: '--',
  });

  const previewOptions = [
    { ticker: 'RELIANCE', market: 'NSE', label: 'Reliance' },
    { ticker: 'TCS', market: 'NSE', label: 'TCS' },
    { ticker: 'INFY', market: 'NSE', label: 'Infosys' },
    { ticker: 'AAPL', market: 'NASDAQ', label: 'Apple' },
  ];

  // Fetch Live Quote for the Selected Stock from Yahoo Finance
  const fetchLiveStockQuote = async (ticker, market) => {
    setLoadingPreview(true);
    try {
      const quote = await marketAPI.getQuote(ticker, market);
      if (quote && quote.price > 0) {
        const isPositive = quote.change >= 0;
        const currencySymbol = market === 'NASDAQ' || market === 'NYSE' ? '$' : '₹';
        setLivePreview({
          ticker: quote.ticker,
          company_name: quote.company_name || ticker,
          market: quote.market || market,
          price: `${currencySymbol}${quote.price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`,
          change: `${isPositive ? '+' : ''}${quote.change_percent.toFixed(2)}%`,
          isPositive: isPositive,
          pe_ratio: quote.pe_ratio ? quote.pe_ratio.toFixed(2) : 'N/A',
          pb_ratio: quote.pb_ratio ? quote.pb_ratio.toFixed(2) : 'N/A',
          roe: quote.roe ? `${quote.roe.toFixed(2)}%` : 'N/A',
          high_52w: `${currencySymbol}${quote.fifty_two_week_high?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '--'}`,
          low_52w: `${currencySymbol}${quote.fifty_two_week_low?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || '--'}`,
        });
      }
    } catch (err) {
      console.warn('Hero live quote fetch error:', err);
    } finally {
      setLoadingPreview(false);
    }
  };

  useEffect(() => {
    fetchLiveStockQuote('RELIANCE', 'NSE');
  }, []);

  const handleTickerSelect = (opt) => {
    setSelectedTicker(opt.ticker);
    fetchLiveStockQuote(opt.ticker, opt.market);
  };

  const features = [
    {
      title: 'Fundamental Analysis',
      icon: <BarChart3 className="h-6 w-6 text-emerald-500" />,
      desc: 'Instant financial health checks: P/E, P/B, ROE, operating margins, debt ratios, and historical earnings performance.',
      highlights: ['P/E & P/B Ratios', 'Return on Equity (ROE)', 'Debt-to-Equity', 'Historical Growth'],
    },
    {
      title: 'Technical Analysis',
      icon: <TrendingUp className="h-6 w-6 text-sky-500" />,
      desc: 'Quantitative technical indicators: 50 & 200 Moving Averages, RSI momentum oscillator, and MACD crossover signals.',
      highlights: ['SMA 50 / 200 Cross', 'RSI (14) Momentum', 'MACD Signals', 'Annualized Volatility'],
    },
    {
      title: 'News & Sentiment Intelligence',
      icon: <Newspaper className="h-6 w-6 text-amber-500" />,
      desc: 'Real-time financial headlines ingested with sentiment analysis, publication timestamps, and direct verified source links.',
      highlights: ['Sentiment Classification', 'Live Media Ingestion', 'Official Filings', 'Source Citations'],
    },
    {
      title: 'Risk & Stress Testing',
      icon: <ShieldAlert className="h-6 w-6 text-rose-500" />,
      desc: 'Quantitative risk assessment with 52-week peak-to-trough maximum drawdown, volatility tracking, and scenario analysis.',
      highlights: ['Maximum Drawdown %', 'Volatility Spectrum', 'Downside Stress Test', 'Conflict Checking'],
    },
    {
      title: 'Autonomous AI Supervisor',
      icon: <Bot className="h-6 w-6 text-indigo-500" />,
      desc: 'Multi-agent orchestration coordinating research agents to synthesize structured, unbiased equity dossiers.',
      highlights: ['Multi-Agent Pipeline', 'Structured Output', 'Complete Synthesis', 'Audit Log Trail'],
    },
    {
      title: 'Personalized Workspace',
      icon: <Layers className="h-6 w-6 text-cyan-500" />,
      desc: 'Build custom watchlists, switch market preferences (NSE, BSE, US), and access your isolated research task history.',
      highlights: ['Live Watchlists', 'Market Preferences', 'Task History Log', 'JWT Secure Session'],
    },
  ];

  const steps = [
    {
      step: '1',
      title: 'Create Your Account',
      desc: 'Sign up in 10 seconds using your Google account or email. It is 100% free and requires zero setup.',
    },
    {
      step: '2',
      title: 'Select Any Stock',
      desc: 'Choose from popular Indian or US stocks like Reliance, TCS, Infosys, or Apple, or search any ticker symbol.',
    },
    {
      step: '3',
      title: 'Get Instant Research',
      desc: 'View real-time prices, financial ratios, chart signals, live news sentiment, and automated research dossiers.',
    },
  ];

  return (
    <div className={`min-h-screen transition-colors duration-200 ${isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'}`}>
      {/* 1. Hero Section */}
      <section className="relative overflow-hidden pt-12 pb-16 sm:pt-16 sm:pb-24 border-b border-slate-700/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          {/* Welcome Pill */}
          <div className={`inline-flex items-center space-x-2 px-4 py-1.5 rounded-full mb-6 border shadow-sm transition-colors text-xs font-semibold ${
            isDark ? 'bg-slate-900 border-slate-800 text-slate-300' : 'bg-white border-slate-200 text-slate-700'
          }`}>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>AI-POWERED STOCK RESEARCH PLATFORM</span>
          </div>

          {/* Headline */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tight max-w-4xl mx-auto leading-tight">
            Research Any Stock in Seconds,{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-500 via-indigo-500 to-cyan-400">
              Powered by Specialized AI Agents
            </span>
          </h1>

          {/* Subtitle */}
          <p className={`mt-5 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Automated company valuation, quantitative technical indicators, real-time news sentiment,
            and portfolio risk analysis — all in one simple, powerful workspace.
          </p>

          {/* Primary Action Button (Clean, single high-impact CTA) */}
          <div className="mt-8 flex justify-center items-center max-w-md mx-auto">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="flex items-center justify-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-lg shadow-sky-600/30 transition cursor-pointer"
              >
                <span>Open Research Workspace</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            ) : (
              <Link
                to="/register"
                className="flex items-center justify-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-lg shadow-sky-600/30 transition cursor-pointer"
              >
                <span>Get Started Free</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            )}
          </div>

          {/* Key Trust Highlights (No external scraping sources mentioned) */}
          <div className={`mt-10 flex flex-wrap justify-center items-center gap-6 text-xs font-medium ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>Real-Time Market Feeds</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>One-Click Google Sign-In</span>
            </span>
            <span className="flex items-center space-x-1.5">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>NSE, BSE, NASDAQ, NYSE Supported</span>
            </span>
          </div>
        </div>
      </section>

      {/* 2. Interactive Real Live Stock Preview Card (No Hardcoded Numbers) */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 mb-16 relative z-20">
        <div className={`border rounded-2xl shadow-xl overflow-hidden transition-colors ${
          isDark ? 'bg-slate-900 border-slate-800 text-white' : 'bg-white border-slate-200 text-slate-900'
        }`}>
          {/* Card Header with Quick Stock Selection Tabs */}
          <div className={`px-5 py-3 border-b flex flex-wrap items-center justify-between gap-3 text-xs ${
            isDark ? 'bg-slate-950 border-slate-800 text-slate-400' : 'bg-slate-100 border-slate-200 text-slate-600'
          }`}>
            <div className="flex items-center space-x-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block animate-pulse"></span>
              <span className="font-bold uppercase tracking-wider text-[11px]">LIVE MARKET QUOTE PREVIEW</span>
            </div>

            {/* Quick Clickable Ticker Selector */}
            <div className="flex items-center space-x-1.5">
              {previewOptions.map((opt) => (
                <button
                  key={opt.ticker}
                  onClick={() => handleTickerSelect(opt)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold transition cursor-pointer ${
                    selectedTicker === opt.ticker
                      ? 'bg-sky-600 text-white shadow-sm'
                      : isDark
                      ? 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      : 'bg-white text-slate-700 border border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Card Body */}
          <div className="p-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <div className="flex items-center space-x-3">
                  <h2 className="text-2xl font-black font-mono">{livePreview.ticker}</h2>
                  <span className="bg-sky-500/10 text-sky-500 border border-sky-500/30 text-xs font-bold px-2.5 py-0.5 rounded font-mono">
                    {livePreview.market}
                  </span>
                  <span className={`text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                    {livePreview.company_name}
                  </span>
                </div>
              </div>

              <div className="text-left sm:text-right">
                <span className="text-2xl font-black font-mono block">
                  {loadingPreview ? (
                    <span className="text-slate-400 animate-pulse text-lg">Fetching live LTP...</span>
                  ) : (
                    livePreview.price
                  )}
                </span>
                <span className={`text-xs font-bold font-mono ${livePreview.isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
                  {livePreview.change} Today
                </span>
              </div>
            </div>

            {/* Key Ratios Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-5">
              <div className={`p-3 rounded-xl border ${isDark ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>P/E RATIO</span>
                <span className="text-base font-bold font-mono mt-0.5 block">{livePreview.pe_ratio}</span>
              </div>
              <div className={`p-3 rounded-xl border ${isDark ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>P/B RATIO</span>
                <span className="text-base font-bold font-mono mt-0.5 block">{livePreview.pb_ratio}</span>
              </div>
              <div className={`p-3 rounded-xl border ${isDark ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>RETURN ON EQ (ROE)</span>
                <span className="text-base font-bold font-mono text-emerald-500 mt-0.5 block">{livePreview.roe}</span>
              </div>
              <div className={`p-3 rounded-xl border ${isDark ? 'bg-slate-950/80 border-slate-800' : 'bg-slate-50 border-slate-200'}`}>
                <span className={`text-[10px] font-mono uppercase block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>52W RANGE</span>
                <span className="text-xs font-bold font-mono mt-0.5 block truncate">{livePreview.high_52w} / {livePreview.low_52w}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. How It Works in 3 Simple Steps */}
      <section className={`py-16 border-t ${isDark ? 'border-slate-800 bg-slate-900/40' : 'border-slate-200 bg-slate-100/50'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <span className="text-xs font-bold text-sky-500 uppercase tracking-wider font-mono">
              SIMPLE 3-STEP WORKFLOW
            </span>
            <h2 className="text-2xl sm:text-3xl font-black mt-2">
              How It Works
            </h2>
            <p className={`mt-2 text-sm max-w-xl mx-auto ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
              Get started in under a minute without any complicated financial background.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {steps.map((st, i) => (
              <div
                key={i}
                className={`p-6 rounded-2xl border transition-all ${
                  isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-sm'
                }`}
              >
                <div className="w-10 h-10 rounded-xl bg-sky-600 text-white font-black flex items-center justify-center text-base mb-4 shadow-md">
                  {st.step}
                </div>
                <h3 className="text-lg font-bold mb-2">{st.title}</h3>
                <p className={`text-xs leading-relaxed ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  {st.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Core Features Grid */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          <span className="text-xs font-bold text-sky-500 uppercase tracking-wider font-mono">
            COMPREHENSIVE RESEARCH SUITE
          </span>
          <h2 className="text-2xl sm:text-4xl font-black mt-2">
            Multi-Agent Intelligence Capabilities
          </h2>
          <p className={`mt-2 text-sm sm:text-base max-w-2xl mx-auto ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Explore specialized engines designed to provide institutional-grade insights for any stock.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((item, idx) => (
            <div
              key={idx}
              className={`p-6 rounded-2xl border transition-all hover:scale-[1.01] flex flex-col justify-between ${
                isDark ? 'bg-slate-900 border-slate-800 hover:border-slate-700' : 'bg-white border-slate-200 shadow-sm hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className={`p-2.5 rounded-xl border ${isDark ? 'bg-slate-800 border-slate-700' : 'bg-slate-100 border-slate-200'}`}>
                    {item.icon}
                  </div>
                </div>
                <h3 className="text-base font-bold mb-2">{item.title}</h3>
                <p className={`text-xs leading-relaxed mb-4 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
                  {item.desc}
                </p>
              </div>

              <div className={`pt-3 border-t flex flex-wrap gap-1.5 ${isDark ? 'border-slate-800' : 'border-slate-100'}`}>
                {item.highlights.map((h, hIdx) => (
                  <span
                    key={hIdx}
                    className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                      isDark ? 'bg-slate-950 text-slate-300 border-slate-800' : 'bg-slate-100 text-slate-700 border-slate-200'
                    }`}
                  >
                    {h}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Bottom Call to Action */}
      <section className={`py-16 border-t text-center ${isDark ? 'border-slate-800 bg-slate-900/50' : 'border-slate-200 bg-slate-100'}`}>
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-2xl sm:text-3xl font-black">
            Ready to Start Researching?
          </h2>
          <p className={`mt-2 text-sm ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Join now to access real-time stock quotes, automated financial audits, and personal watchlists.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3">
            <Link
              to="/register"
              className="flex items-center space-x-2 bg-sky-600 hover:bg-sky-500 text-white font-bold text-sm px-8 py-3.5 rounded-xl shadow-md transition cursor-pointer"
            >
              <UserPlus className="h-4 w-4" />
              <span>Create Account</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <p className={`text-xs ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
              Already have an account?{' '}
              <Link to="/login" className="text-sky-500 hover:text-sky-600 font-bold transition">
                Log In
              </Link>
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Home;
