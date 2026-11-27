import React from 'react';
import { Menu, Zap, Globe, User, Compass } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const TICKER_TAPE = [
  { ticker: 'AAPL', market: 'NASDAQ', label: 'Apple Inc.' },
  { ticker: 'NVDA', market: 'NASDAQ', label: 'NVIDIA' },
  { ticker: 'MSFT', market: 'NASDAQ', label: 'Microsoft' },
  { ticker: 'INFY', market: 'NSE', label: 'Infosys' },
  { ticker: 'RELIANCE', market: 'NSE', label: 'Reliance' },
  { ticker: 'TCS', market: 'NSE', label: 'TCS' },
  { ticker: 'JPM', market: 'NYSE', label: 'JPMorgan' },
];

export default function Navbar({ setMobileOpen, onOpenNewResearchModal }) {
  const { preferences } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-30 bg-[#FCFBF8]/90 backdrop-blur-xl border-b border-[#E4E1D8]">
      {/* Top Ticker Tape Strip */}
      <div className="hidden md:flex items-center justify-between h-8 px-6 border-b border-[#EAE7DF] bg-[#F2EFE8] overflow-hidden">
        <div className="flex items-center gap-2 text-[10px] font-mono text-[#0A624C] font-bold flex-shrink-0 pr-4 border-r border-[#DCD8CD]">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-ping" />
          EXCHANGE FEED
        </div>
        <div className="flex-1 overflow-hidden mx-4">
          <div className="flex items-center gap-6 animate-ticker whitespace-nowrap w-max">
            {[...TICKER_TAPE, ...TICKER_TAPE].map((item, idx) => (
              <button
                key={`${item.ticker}-${idx}`}
                type="button"
                onClick={() => navigate(`/explorer?ticker=${item.ticker}&market=${item.market}`)}
                className="inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-600 hover:text-[#0A624C] transition-colors"
              >
                <span className="font-bold text-slate-900">{item.ticker}</span>
                <span className="text-[9px] px-1.5 py-0.2 rounded bg-white text-slate-600 border border-[#DCD8CD]">
                  {item.market}
                </span>
                <span className="text-slate-500">• {item.label}</span>
              </button>
            ))}
          </div>
        </div>
        <Link
          to="/explorer"
          className="text-[10px] font-mono font-bold text-[#0A624C] hover:text-emerald-800 flex items-center gap-1 flex-shrink-0"
        >
          <Compass className="w-3 h-3" />
          OPEN EXPLORER
        </Link>
      </div>

      {/* Main Command Bar */}
      <div className="h-16 px-4 sm:px-7 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileOpen(true)}
            className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-[#EFECE4] border border-[#E4E1D8] transition-colors"
            aria-label="Open sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="hidden sm:flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-white border border-[#E4E1D8] text-xs font-mono shadow-sm">
            <Globe className="w-3.5 h-3.5 text-[#0D7A5F]" />
            <span className="text-slate-500">DESK:</span>
            <span className="text-[#0A624C] font-bold">{preferences?.preferred_market || 'NASDAQ'}</span>
            <span className="text-slate-300">|</span>
            <span className="text-amber-700 font-semibold">{preferences?.analysis_period || '1 Year'}</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={onOpenNewResearchModal}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[#0A624C] hover:bg-[#084C3B] text-white font-bold text-xs sm:text-sm shadow-sm shadow-emerald-900/15 transition-all active:scale-95"
          >
            <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
            <span>Launch Agent Run</span>
          </button>

          <Link
            to="/profile"
            className="p-2.5 rounded-xl text-slate-600 hover:text-[#0A624C] bg-white hover:bg-emerald-50 border border-[#E4E1D8] transition-colors"
            title="Analyst Profile"
          >
            <User className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </header>
  );
}
