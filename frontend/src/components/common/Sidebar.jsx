import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Compass,
  History,
  Bookmark,
  Sliders,
  User,
  LogOut,
  Cpu,
  Radio,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar({ mobileOpen, setMobileOpen, onOpenLogoutModal }) {
  const { user } = useAuth();

  const navItems = [
    { name: 'Command Deck', to: '/dashboard', icon: LayoutDashboard, tag: 'HOME' },
    { name: 'Live Explorer', to: '/explorer', icon: Compass, tag: 'LIVE' },
    { name: 'Dossier Archive', to: '/history', icon: History, tag: 'LOGS' },
    { name: 'Radar Watchlist', to: '/watchlist', icon: Bookmark, tag: 'WATCH' },
    { name: 'Market Config', to: '/preferences', icon: Sliders, tag: 'CFG' },
    { name: 'Analyst Profile', to: '/profile', icon: User, tag: 'ID' },
  ];

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/35 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-72 bg-[#FCFBF8]/95 backdrop-blur-xl text-slate-700 flex flex-col border-r border-[#E4E1D8] transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="h-20 px-6 flex items-center justify-between border-b border-[#E4E1D8]">
          <div className="flex items-center gap-3">
            <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-[#0A624C] to-[#0D7A5F] flex items-center justify-center text-white shadow-md shadow-emerald-900/15">
              <Cpu className="w-5 h-5 stroke-[2.2]" />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-amber-500 ring-2 ring-[#FCFBF8]" />
            </div>
            <div>
              <h1 className="font-display text-base font-bold text-slate-900 tracking-tight">
                QUANT<span className="text-[#0D7A5F]">AGENT</span>
              </h1>
              <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
                Research Studio • M1–M4
              </p>
            </div>
          </div>
        </div>

        {/* Live Agent Mesh Status */}
        <div className="mx-4 mt-4 p-3 rounded-2xl bg-[#F6F5F0] border border-[#E4E1D8] space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Radio className="w-3 h-3 text-emerald-600 animate-pulse" />
              Agent Mesh Ready
            </span>
            <span className="text-[10px] font-mono text-[#0A624C] font-bold">3 ACTIVE</span>
          </div>
          <div className="grid grid-cols-3 gap-1.5 text-[10px] font-mono font-semibold">
            <div className="px-2 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-center">
              OHLCV
            </div>
            <div className="px-2 py-1 rounded-lg bg-sky-50 border border-sky-200 text-sky-800 text-center">
              FUND
            </div>
            <div className="px-2 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-center">
              TECH
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-5 space-y-1 overflow-y-auto">
          <div className="px-3 pb-2 text-[10px] font-mono font-semibold uppercase tracking-widest text-slate-400">
            Workspace Modules
          </div>

          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={({ isActive }) =>
                  `group flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-[#0A624C] text-white shadow-sm shadow-emerald-900/15 font-semibold'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-[#EFECE4]'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon className="w-4 h-4 flex-shrink-0" />
                      <span>{item.name}</span>
                    </div>
                    <span
                      className={`text-[9px] font-mono tracking-wider px-1.5 py-0.5 rounded ${
                        isActive
                          ? 'bg-white/15 text-emerald-50'
                          : 'bg-[#F6F5F0] text-slate-500 border border-[#E4E1D8]'
                      }`}
                    >
                      {item.tag}
                    </span>
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* User Card & Logout Footer */}
        <div className="p-4 border-t border-[#E4E1D8] bg-[#F6F5F0]/80">
          <div className="px-3 py-2.5 rounded-2xl bg-white border border-[#E4E1D8] mb-3 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 border border-emerald-200 text-[#0A624C] flex items-center justify-center font-mono font-bold text-xs uppercase">
              {user?.full_name ? user.full_name.charAt(0) : 'Q'}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-slate-900 truncate">
                {user?.full_name || 'Quant Analyst'}
              </p>
              <p className="text-[11px] font-mono text-slate-500 truncate">{user?.email}</p>
            </div>
          </div>

          <button
            onClick={() => {
              setMobileOpen(false);
              onOpenLogoutModal();
            }}
            className="w-full flex items-center justify-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-mono font-semibold text-slate-600 hover:text-rose-700 hover:bg-rose-50 bg-white border border-[#E4E1D8] hover:border-rose-200 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5 flex-shrink-0" />
            <span>SIGN OUT</span>
          </button>
        </div>
      </aside>
    </>
  );
}
