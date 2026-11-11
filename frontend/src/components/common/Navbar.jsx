import React from 'react';
import { Menu, Plus, Sparkles, Globe, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function Navbar({ setMobileOpen, onOpenNewResearchModal }) {
  const { user, preferences } = useAuth();

  return (
    <header className="sticky top-0 z-30 h-20 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-8 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Mobile menu button */}
        <button
          onClick={() => setMobileOpen(true)}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
          aria-label="Open sidebar"
        >
          <Menu className="w-6 h-6" />
        </button>

        {/* Market Badge */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700">
          <Globe className="w-3.5 h-3.5 text-blue-600" />
          <span>Active Market:</span>
          <span className="text-blue-700 font-bold">{preferences?.preferred_market || 'NASDAQ'}</span>
          <span className="text-slate-300">•</span>
          <span className="text-slate-500">{preferences?.analysis_period || '1 Year'}</span>
        </div>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-3">
        {/* Quick Launch Research Button */}
        <button
          onClick={onOpenNewResearchModal}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs sm:text-sm shadow-md shadow-blue-600/20 transition-all hover:shadow-lg hover:shadow-blue-600/30 active:scale-95"
        >
          <Plus className="w-4 h-4" />
          <span>Start Research</span>
        </button>

        {/* Profile Link Icon */}
        <Link
          to="/profile"
          className="p-2.5 rounded-xl text-slate-600 hover:text-blue-600 hover:bg-blue-50 border border-slate-200 transition-colors"
          title="Account Profile"
        >
          <User className="w-4 h-4" />
        </Link>
      </div>
    </header>
  );
}

