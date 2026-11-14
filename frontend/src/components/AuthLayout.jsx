import React from 'react';
import { TrendingUp, Zap, ShieldCheck } from 'lucide-react';

export const AuthLayout = ({ children, headingTop, headingHighlight, subtitle }) => {
  return (
    <div className="min-h-screen w-full bg-[#05080a] flex items-center justify-center p-3 sm:p-6 lg:p-8 relative overflow-hidden">
      {/* Background radial glow */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-950/20 rounded-full blur-3xl pointer-events-none -z-10" />
      <div className="absolute bottom-10 right-1/4 w-96 h-96 bg-teal-950/20 rounded-full blur-3xl pointer-events-none -z-10" />

      {/* Main 2-column container */}
      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center my-auto py-4">
        
        {/* LEFT COLUMN: Branding & Visuals (~46% width -> col-span-5) */}
        <div className="lg:col-span-5 flex flex-col justify-center space-y-6 px-2 sm:px-4 relative">
          
          <div>
            {/* Logo and App Title */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600/20 to-teal-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0 shadow-lg shadow-emerald-500/10">
                {/* Financial chart logo with upward bars & arrow */}
                <svg className="w-6 h-6 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M3 3v18h18" />
                  <path d="M18 9l-5 5-4-4-3 3" />
                  <path d="M18 9h-4" />
                  <path d="M18 9v4" />
                </svg>
              </div>
              <div className="leading-tight">
                <span className="block text-base font-bold text-white tracking-wide">
                  Multi-Agent Stock
                </span>
                <span className="block text-base font-bold text-white tracking-wide">
                  Research Analyst
                </span>
              </div>
            </div>

            {/* Main Heading */}
            <div className="mb-3">
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight leading-none mb-1">
                {headingTop}
              </h1>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#00d084] tracking-tight leading-none">
                {headingHighlight}
              </h1>
            </div>

            {/* Subtitle */}
            <p className="text-slate-400 text-sm sm:text-base mb-6 max-w-md font-normal leading-relaxed">
              {subtitle}
            </p>

            {/* 3 Feature Highlights with Green Outlined Icons */}
            <div className="space-y-3.5 mb-2">
              {/* Feature 1 */}
              <div className="flex items-center gap-3.5">
                <div className="w-9 h-9 rounded-full border border-emerald-500/40 bg-emerald-950/30 flex items-center justify-center shrink-0 shadow-sm shadow-emerald-500/20">
                  <TrendingUp className="w-4 h-4 text-[#00d084]" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Multi-Agent Analysis</h4>
                  <p className="text-xs text-slate-400">Fundamental, Technical, News & Risk</p>
                </div>
              </div>

              {/* Feature 2 */}
              <div className="flex items-center gap-3.5">
                <div className="w-9 h-9 rounded-full border border-emerald-500/40 bg-emerald-950/30 flex items-center justify-center shrink-0 shadow-sm shadow-emerald-500/20">
                  <Zap className="w-4 h-4 text-[#00d084]" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Real-Time Insights</h4>
                  <p className="text-xs text-slate-400">Stay ahead in the market</p>
                </div>
              </div>

              {/* Feature 3 */}
              <div className="flex items-center gap-3.5">
                <div className="w-9 h-9 rounded-full border border-emerald-500/40 bg-emerald-950/30 flex items-center justify-center shrink-0 shadow-sm shadow-emerald-500/20">
                  <ShieldCheck className="w-4 h-4 text-[#00d084]" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Secure & Personalized</h4>
                  <p className="text-xs text-slate-400">Your data, your workspace</p>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Financial Illustration: Digital Globe & Candlestick Chart (Seamless) */}
          <div className="relative pt-1 w-full max-w-md pointer-events-none select-none">
            <img
              src="/images/financial-globe.png"
              alt="Digital Globe and Candlestick Chart"
              className="w-full h-auto max-h-36 sm:max-h-44 object-contain object-left opacity-90"
            />
          </div>

        </div>

        {/* RIGHT COLUMN: Form Card (~54% width -> col-span-7) */}
        <div className="lg:col-span-7 flex justify-center">
          <div className="w-full max-w-xl bg-[#0b0f15] border border-[#1c2533] rounded-3xl p-6 sm:p-9 shadow-2xl shadow-black/80 relative">
            {children}
          </div>
        </div>

      </div>
    </div>
  );
};

export default AuthLayout;

