/**
 * TerminalSidebar.jsx
 * Premium Financial Terminal Sidebar for SAI ANALYSIS.
 *
 * Dynamically generated from the central agent registry:
 * - Platform Workspaces: Terminal Overview, Watchlist, Research Archive
 * - Categorized Autonomous AI Agents: Data Intelligence, Financial Analysis, Market Analysis,
 *   Market Intelligence, Risk Intelligence, Orchestration
 * - Expandable / collapsible category groups
 * - Visual status badges: Green "Active" and Amber "Planned"
 * - Stable workspace/agent IDs for active highlighting and navigation routing
 * - Engine status card & user profile with authenticated sign-out
 */

import React, { useState } from 'react';
import {
  TrendingUp,
  LayoutDashboard,
  Bookmark,
  History,
  Database,
  CandlestickChart,
  Newspaper,
  ShieldAlert,
  Cpu,
  BarChart2,
  ChevronDown,
  ChevronRight,
  LogOut,
  Sliders,
  Search,
} from 'lucide-react';
import {
  getAllCategories,
  getAllPlatformWorkspaces,
  getAgentsByCategory,
} from '../../config/agentRegistry';

// Safe icon dictionary mapping registry icon names to Lucide icon components
const ICON_MAP = {
  TrendingUp,
  LayoutDashboard,
  Bookmark,
  History,
  Database,
  CandlestickChart,
  Newspaper,
  ShieldAlert,
  Cpu,
  BarChart2,
  Sliders,
  Search,
};

const getIcon = (iconName, fallback = Cpu) => {
  if (!iconName) return fallback;
  return ICON_MAP[iconName] || fallback;
};

export default function TerminalSidebar({
  activeWorkspace = 'overview',
  onSelectWorkspace = () => {},
  user = {},
  onLogout = () => {},
  watchlistCount = 0,
  historyCount = 0,
}) {
  const workspaces = getAllPlatformWorkspaces();
  const categories = getAllCategories();

  // Expandable category groups state (default all expanded for full discovery)
  const [expandedCategories, setExpandedCategories] = useState(() => {
    const initial = {};
    categories.forEach((cat) => {
      initial[cat.id] = true;
    });
    return initial;
  });

  const toggleCategory = (categoryId, e) => {
    if (e) e.stopPropagation();
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }));
  };

  return (
    <aside className="w-full md:w-64 lg:w-72 bg-[#09090d] border-r border-white/[0.07] flex flex-col justify-between shrink-0 md:sticky md:top-0 md:h-screen z-30 select-none">
      {/* ── Brand Logo Header ── */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.06] shrink-0">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-rose-600 via-red-600 to-rose-700 text-white font-bold shadow-crimson-sm shrink-0">
          <TrendingUp className="h-5 w-5" />
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-base font-extrabold tracking-tight text-white font-sans uppercase">
            SAI ANALYSIS
          </span>
          <span className="text-[9px] font-mono font-medium text-rose-400 uppercase tracking-wider truncate">
            Financial Terminal • AI
          </span>
        </div>
      </div>

      {/* ── Dynamic Scrollable Navigation Body ── */}
      <div className="flex-1 overflow-y-auto min-h-0 px-3 py-3 space-y-4">
        {/* ── Platform Workspaces Section ── */}
        <div className="space-y-1">
          <div className="px-2 pb-1.5 flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase font-semibold text-zinc-500 tracking-wider">
              Workspaces
            </span>
            <span className="text-[9px] font-mono text-zinc-600">Core</span>
          </div>

          <div className="space-y-0.5">
            {workspaces.map((ws) => {
              const IconComponent = getIcon(ws.icon, LayoutDashboard);
              const isActive = activeWorkspace === ws.id;
              const countBadge =
                ws.id === 'watchlist'
                  ? watchlistCount
                  : ws.id === 'history'
                  ? historyCount
                  : null;

              return (
                <button
                  key={ws.id}
                  type="button"
                  onClick={() => onSelectWorkspace(ws.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-all text-left ${
                    isActive
                      ? 'bg-gradient-to-r from-rose-950/70 via-red-950/30 to-transparent border-l-2 border-rose-500 text-white font-semibold shadow-sm'
                      : 'text-zinc-400 hover:text-white hover:bg-white/[0.03] font-medium'
                  }`}
                  title={ws.description}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <IconComponent
                      className={`h-4 w-4 shrink-0 ${
                        isActive ? 'text-rose-500' : 'text-zinc-400'
                      }`}
                    />
                    <span className="truncate">{ws.name}</span>
                  </div>

                  {countBadge !== null && countBadge > 0 && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.05] text-zinc-300 border border-white/[0.08] shrink-0">
                      {countBadge}
                    </span>
                  )}
                  {isActive && countBadge === null && (
                    <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse shrink-0" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── Visual Section Divider ── */}
        <div className="h-px bg-white/[0.06] mx-1" />

        {/* ── AI Agent Categories Section ── */}
        <div className="space-y-3">
          <div className="px-2 pb-0.5 flex items-center justify-between">
            <span className="text-[10px] font-mono uppercase font-semibold text-zinc-500 tracking-wider">
              Autonomous Agents
            </span>
            <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-semibold">
              Registry
            </span>
          </div>

          <div className="space-y-2">
            {categories.map((category) => {
              const CategoryIcon = getIcon(category.icon, Cpu);
              const agents = getAgentsByCategory(category.id);
              const isExpanded = expandedCategories[category.id] ?? true;

              return (
                <div key={category.id} className="space-y-1">
                  {/* Category Header (Expand / Collapse Trigger) */}
                  <button
                    type="button"
                    onClick={(e) => toggleCategory(category.id, e)}
                    className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.02] text-left transition-colors group"
                    title={category.description}
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <CategoryIcon className="h-3.5 w-3.5 text-zinc-500 group-hover:text-rose-400 transition-colors shrink-0" />
                      <span className="text-[11px] font-semibold tracking-wide uppercase font-mono text-zinc-400 group-hover:text-zinc-200 truncate">
                        {category.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <span className="text-[9px] font-mono px-1 rounded bg-white/[0.04] text-zinc-500 border border-white/[0.04]">
                        {agents.length}
                      </span>
                      {isExpanded ? (
                        <ChevronDown className="h-3 w-3 text-zinc-500 group-hover:text-zinc-300" />
                      ) : (
                        <ChevronRight className="h-3 w-3 text-zinc-500 group-hover:text-zinc-300" />
                      )}
                    </div>
                  </button>

                  {/* Agents under this Category */}
                  {isExpanded && (
                    <div className="pl-3 space-y-0.5 border-l border-white/[0.04] ml-3.5">
                      {agents.map((agent) => {
                        const AgentIcon = getIcon(agent.icon, Cpu);
                        const isActive = activeWorkspace === agent.id;
                        const isLive = agent.status === 'active';

                        return (
                          <button
                            key={agent.id}
                            type="button"
                            onClick={() => onSelectWorkspace(agent.id)}
                            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-all text-left ${
                              isActive
                                ? 'bg-gradient-to-r from-rose-950/70 via-red-950/30 to-transparent border-l-2 border-rose-500 text-white font-semibold shadow-sm'
                                : 'text-zinc-400 hover:text-white hover:bg-white/[0.03] font-medium'
                            }`}
                            title={agent.description}
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <AgentIcon
                                className={`h-3.5 w-3.5 shrink-0 ${
                                  isActive ? 'text-rose-500' : 'text-zinc-500'
                                }`}
                              />
                              <span className="truncate text-[11px]">
                                {agent.shortName || agent.name}
                              </span>
                            </div>
                            <span
                              className={`text-[8px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded font-semibold shrink-0 ml-1.5 ${
                                isLive
                                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                  : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                              }`}
                            >
                              {isLive ? 'Active' : 'Planned'}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Sidebar Footer Area ── */}
      <div className="p-3 border-t border-white/[0.06] space-y-2.5 shrink-0 bg-[#07070a]">
        {/* Engine Health Card */}
        <div className="p-3 rounded-xl border border-white/[0.08] bg-[#120f16]/90 relative overflow-hidden">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-bold text-white flex items-center gap-1.5">
              <Cpu className="h-3.5 w-3.5 text-rose-500" />
              Stock Engine
            </span>
            <span className="text-[9px] font-mono text-emerald-400 font-semibold uppercase">
              Active
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 leading-snug">
            Milestone 1 • Fast multi-agent analytics & validation pipeline.
          </p>
          <div className="mt-2 flex items-center gap-1.5 text-[10px] text-zinc-400 font-mono">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            PostgreSQL Connected
          </div>
        </div>

        {/* User Profile Pill */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02] border border-white/[0.06]">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-bold font-mono shrink-0">
              {user.full_name?.charAt(0) || 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-white truncate leading-tight">
                {user.full_name || 'Mathew Andersson'}
              </p>
              <p className="text-[10px] text-zinc-400 font-mono truncate">
                {user.email || 'user@example.com'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onLogout}
            className="p-1.5 text-zinc-400 hover:text-rose-400 hover:bg-rose-950/30 rounded-lg transition-colors"
            title="Sign Out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
