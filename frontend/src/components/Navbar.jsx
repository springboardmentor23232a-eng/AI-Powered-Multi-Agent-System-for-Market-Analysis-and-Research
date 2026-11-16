import React from 'react';
import { Sparkles, Activity, Menu, X, ArrowUpRight } from 'lucide-react';

export default function Navbar({
  title,
  subtitle,
  onOpenQuickResearch,
  onToggleMobileSidebar,
  isMobileSidebarOpen,
}) {
  return (
    <header className="h-18 bg-white border-b border-gray-200/80 px-6 sm:px-8 flex items-center justify-between shrink-0 sticky top-0 z-20">
      <div className="flex items-center gap-4">
        {/* Mobile menu toggle */}
        <button
          onClick={onToggleMobileSidebar}
          className="lg:hidden p-2 rounded-xl text-gray-600 hover:bg-gray-100 transition cursor-pointer"
          aria-label="Toggle Navigation Menu"
        >
          {isMobileSidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        <div>
          <h1 className="text-xl sm:text-2xl font-black text-[#111827] tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-gray-500 font-medium hidden sm:block">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3.5">
        {/* Engine status indicator */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#f1f9e8] border border-[#d6edbf] text-xs font-semibold text-[#1f4631]">
          <span className="w-2 h-2 rounded-full bg-[#9bd946] animate-pulse" />
          <span>Research Engine Active</span>
        </div>

        {/* Quick New Analysis Action Button */}
        {onOpenQuickResearch && (
          <button
            onClick={onOpenQuickResearch}
            className="h-10 px-4 rounded-full bg-[#9bd946] hover:bg-[#8ec93b] active:scale-[0.98] text-[#111827] font-bold text-xs sm:text-sm flex items-center gap-2 transition-all shadow-sm shadow-[#9bd946]/30 cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>New Research</span>
          </button>
        )}
      </div>
    </header>
  );
}
