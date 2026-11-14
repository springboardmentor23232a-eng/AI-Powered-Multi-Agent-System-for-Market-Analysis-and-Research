import React from 'react';
import { TrendingUp, Newspaper, ShieldAlert } from 'lucide-react';

// Custom Candlestick Icon matching Reference Image 2
const CandlestickIcon = () => (
  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none">
    {/* First Green Candlestick */}
    <line x1="7" y1="4" x2="7" y2="20" stroke="#00d084" strokeWidth="1.5" strokeLinecap="round" />
    <rect x="5.5" y="8" width="3" height="8" rx="0.5" fill="#00d084" />
    {/* Second Red Candlestick */}
    <line x1="15" y1="6" x2="15" y2="18" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
    <rect x="13.5" y="9" width="3" height="6" rx="0.5" fill="#ef4444" />
  </svg>
);

export const AgentCard = ({ title, description, iconType }) => {
  const renderIcon = () => {
    switch (iconType) {
      case 'fundamental':
        return (
          <div className="w-10 h-10 rounded-lg bg-[#141b25] border border-[#232f42] flex items-center justify-center shrink-0">
            <TrendingUp className="w-5 h-5 text-slate-100" />
          </div>
        );
      case 'technical':
        return (
          <div className="w-10 h-10 rounded-lg bg-[#141b25] border border-[#232f42] flex items-center justify-center shrink-0">
            <CandlestickIcon />
          </div>
        );
      case 'news':
        return (
          <div className="w-10 h-10 rounded-lg bg-[#141b25] border border-[#232f42] flex items-center justify-center shrink-0">
            <Newspaper className="w-5 h-5 text-slate-100" />
          </div>
        );
      case 'risk':
        return (
          <div className="w-10 h-10 rounded-lg bg-[#141b25] border border-[#232f42] flex items-center justify-center shrink-0">
            <ShieldAlert className="w-5 h-5 text-red-400" />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-[#0b0f15] hover:bg-[#0e141d] border border-[#1c2533] hover:border-slate-600/70 rounded-2xl p-5 sm:p-6 transition-all duration-200 cursor-default shadow-sm group">
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-3.5">
          {renderIcon()}
          <h3 className="text-base sm:text-lg font-bold text-white group-hover:text-emerald-400/90 transition-colors">
            {title}
          </h3>
        </div>
        <span className="shrink-0 px-2.5 py-1 text-[11px] font-medium rounded-full bg-[#161d28] text-slate-300 border border-[#232f42]">
          Coming Soon
        </span>
      </div>
      <p className="text-xs sm:text-sm text-slate-400 leading-relaxed pl-[54px]">
        {description}
      </p>
    </div>
  );
};

export default AgentCard;

