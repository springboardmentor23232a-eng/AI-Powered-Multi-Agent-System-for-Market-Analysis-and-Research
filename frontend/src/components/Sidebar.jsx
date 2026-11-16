import React from 'react';
import {
  LayoutDashboard,
  Search,
  History,
  GitCompare,
  LogOut,
  TrendingUp,
  ShieldAlert,
  ChevronRight,
} from 'lucide-react';
import FinCrewLogo from './FinCrewLogo';

export default function Sidebar({
  activeTab,
  setActiveTab,
  user,
  onLogout,
  pendingCount = 0,
}) {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Workspace analytics & activity',
    },
    {
      id: 'research',
      label: 'Stock Research',
      icon: Search,
      description: 'Multi-agent equity analysis',
      badge: pendingCount > 0 ? `${pendingCount} active` : null,
      badgeColor: 'bg-[#9bd946] text-[#111827]',
    },
    {
      id: 'history',
      label: 'Research History',
      icon: History,
      description: 'Previous reports & archives',
    },
    {
      id: 'compare',
      label: 'Stock Comparison',
      icon: GitCompare,
      description: 'Side-by-side stock matrix',
    },
  ];

  const userInitial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : (user?.email ? user.email.charAt(0).toUpperCase() : 'U');

  return (
    <aside className="w-72 bg-[#0d1512] text-white flex flex-col shrink-0 border-r border-[#1a2e24] select-none">
      {/* Brand Header */}
      <div className="p-6 border-b border-[#1a2e24]">
        <div className="flex items-center gap-3">
          <FinCrewLogo size="md" />
        </div>
        <p className="mt-2 text-[11px] font-semibold tracking-wider text-[#9bd946] uppercase">
          Autonomous Investment Committee
        </p>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider px-3 mb-3">
          Core Workflows
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-3 rounded-2xl text-left transition-all group cursor-pointer ${
                isActive
                  ? 'bg-[#1f4631] text-[#9bd946] font-bold shadow-md shadow-black/20'
                  : 'text-gray-300 hover:bg-[#13221b] hover:text-white font-medium'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                    isActive
                      ? 'bg-[#9bd946] text-[#0d1512]'
                      : 'bg-[#182b21] text-gray-400 group-hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-[14px] leading-tight">{item.label}</div>
                  <div className="text-[11px] text-gray-500 font-normal mt-0.5">
                    {item.description}
                  </div>
                </div>
              </div>

              {item.badge ? (
                <span
                  className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              ) : (
                <ChevronRight
                  className={`w-4 h-4 transition-transform ${
                    isActive
                      ? 'text-[#9bd946] translate-x-0.5'
                      : 'text-gray-600 opacity-0 group-hover:opacity-100'
                  }`}
                />
              )}
            </button>
          );
        })}
      </nav>

      {/* Specialist Agents Indicator */}
      <div className="mx-4 mb-4 p-3.5 rounded-2xl bg-[#13221b] border border-[#1f4631]/60">
        <div className="flex items-center gap-2 text-xs font-bold text-[#9bd946] mb-2">
          <TrendingUp className="w-3.5 h-3.5" />
          <span>5 Specialist AI Agents</span>
        </div>
        <div className="text-[11px] text-gray-400 space-y-1">
          <div className="flex items-center justify-between">
            <span>Market Research</span>
            <span className="w-2 h-2 rounded-full bg-[#9bd946]" />
          </div>
          <div className="flex items-center justify-between">
            <span>Financial Valuation</span>
            <span className="w-2 h-2 rounded-full bg-[#9bd946]" />
          </div>
          <div className="flex items-center justify-between">
            <span>Technical Signals</span>
            <span className="w-2 h-2 rounded-full bg-[#9bd946]" />
          </div>
          <div className="flex items-center justify-between">
            <span>Sentiment Catalysts</span>
            <span className="w-2 h-2 rounded-full bg-[#9bd946]" />
          </div>
          <div className="flex items-center justify-between">
            <span>Risk Severity</span>
            <span className="w-2 h-2 rounded-full bg-[#9bd946]" />
          </div>
        </div>
      </div>

      {/* User Profile & Logout */}
      <div className="p-4 border-t border-[#1a2e24] bg-[#09100d]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-full bg-[#9bd946] text-[#0d1512] font-black text-sm flex items-center justify-center shrink-0 shadow-sm">
              {userInitial}
            </div>
            <div className="overflow-hidden">
              <div className="text-sm font-bold text-white truncate">
                {user?.full_name || 'Loading...'}
              </div>
              <div className="text-xs text-gray-400 truncate">
                {user?.email || ''}
              </div>
            </div>
          </div>

          <button
            onClick={onLogout}
            title="Log out of FinCrew"
            className="w-8 h-8 rounded-xl flex items-center justify-center text-gray-400 hover:text-red-400 hover:bg-red-950/30 transition-all shrink-0 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
