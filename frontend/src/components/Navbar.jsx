import React from 'react';
import { LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Navbar = () => {
  const { user, logout } = useAuth();

  // Compute initials from full_name
  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const displayName = user?.full_name || 'Stock Researcher';
  const initials = getInitials(displayName);

  return (
    <header className="w-full bg-[#070a0e] border-b border-[#1c2533] sticky top-0 z-40 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand / Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
            <svg className="w-5 h-5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 3v18h18" />
              <path d="M18 9l-5 5-4-4-3 3" />
              <path d="M18 9h-4" />
              <path d="M18 9v4" />
            </svg>
          </div>
          <span className="text-base sm:text-lg font-bold text-white tracking-tight">
            Multi-Agent Stock Research Analyst
          </span>
        </div>

        {/* User Info & Logout */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#1c2533] border border-[#2b394e] flex items-center justify-center text-xs font-bold text-slate-200">
              {initials}
            </div>
            <div className="flex items-center gap-1 text-sm font-medium text-slate-200 cursor-default">
              <span>{displayName}</span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </div>
          </div>

          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#2b394e] hover:border-slate-500 bg-[#0e141e] text-xs sm:text-sm font-medium text-slate-300 hover:text-white transition-all shadow-sm"
            title="Logout"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Logout</span>
          </button>
        </div>

      </div>
    </header>
  );
};

export default Navbar;

