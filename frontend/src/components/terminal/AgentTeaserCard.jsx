/**
 * AgentTeaserCard.jsx
 * Roadmap & Specification View for Planned AI Agents.
 *
 * Displays:
 * - Module designation and development status
 * - Planned analytical capabilities
 * - Expected Input / Output architecture contracts
 * - Multi-agent integration workflow
 * - Quick action links to active analytical agents
 */

import React from 'react';
import {
  Cpu,
  Clock,
  ArrowLeft,
  CheckCircle2,
  Database,
  TrendingUp,
  Layers,
  Sparkles,
  ArrowRight,
} from 'lucide-react';
import { getCategoryById } from '../../config/agentRegistry';

export default function AgentTeaserCard({
  agent,
  onBackToOverview = () => {},
  onSelectWorkspace = () => {},
}) {
  if (!agent) {
    return (
      <div className="p-8 text-center text-zinc-400">
        <p>No agent specification selected.</p>
        <button
          type="button"
          onClick={onBackToOverview}
          className="mt-4 px-4 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-white text-xs font-medium"
        >
          Return to Terminal Overview
        </button>
      </div>
    );
  }

  const category = getCategoryById(agent.categoryId);

  return (
    <div className="space-y-6 max-w-5xl mx-auto py-2 px-1">
      {/* ── Top Navigation & Breadcrumbs ── */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={onBackToOverview}
          className="flex items-center gap-2 text-xs font-mono text-zinc-400 hover:text-white transition-colors group"
        >
          <ArrowLeft className="h-4 w-4 group-hover:-translate-x-0.5 transition-transform text-rose-500" />
          <span>Back to Terminal Overview</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider">
            {category.label}
          </span>
          <span className="text-zinc-600">•</span>
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 uppercase tracking-wider flex items-center gap-1.5">
            <Clock className="h-3 w-3" />
            {agent.module || 'Planned'} • Roadmap
          </span>
        </div>
      </div>

      {/* ── Agent Hero Header ── */}
      <div className="glass-card p-6 md:p-8 rounded-2xl border border-white/[0.08] bg-gradient-to-br from-[#120f18]/90 via-[#0d0c14]/90 to-[#07060a]/95 relative overflow-hidden shadow-2xl">
        <div className="absolute top-0 right-0 w-80 h-80 bg-rose-600/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative z-10">
          <div className="flex items-start gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold shrink-0 shadow-lg shadow-amber-950/20">
              <Cpu className="h-7 w-7" />
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono text-rose-400 font-semibold tracking-wider uppercase">
                  {agent.module}
                </span>
                <span className="text-zinc-600">•</span>
                <span className="text-xs font-mono text-zinc-400">{agent.shortName}</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                {agent.name}
              </h1>
              <p className="text-sm text-zinc-300 leading-relaxed max-w-2xl pt-1">
                {agent.description}
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-2.5 w-full md:w-auto shrink-0">
            <button
              type="button"
              onClick={() => onSelectWorkspace('fundamental-analysis-agent')}
              className="px-4 py-2 rounded-xl text-xs font-medium text-white bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.08] transition-all flex items-center justify-center gap-2"
            >
              <TrendingUp className="h-3.5 w-3.5 text-rose-500" />
              <span>Explore Fundamental Agent</span>
            </button>
            <button
              type="button"
              onClick={() => onSelectWorkspace('dataset-validation-agent')}
              className="px-4 py-2 rounded-xl text-xs font-medium text-white bg-rose-600/20 hover:bg-rose-600/30 border border-rose-500/40 transition-all flex items-center justify-center gap-2"
            >
              <Database className="h-3.5 w-3.5 text-rose-400" />
              <span>Dataset Agent (Active)</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── Capabilities & Architecture Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Planned Capabilities */}
        <div className="glass-card p-6 rounded-2xl border border-white/[0.08] bg-[#0c0c12]/90 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Planned Analytical Capabilities
              </h2>
            </div>
            <span className="text-[10px] font-mono text-zinc-500">
              {agent.capabilities?.length || 0} Features
            </span>
          </div>

          <ul className="space-y-3">
            {agent.capabilities?.map((cap) => (
              <li key={cap} className="flex items-start gap-3 text-xs text-zinc-300 leading-relaxed">
                <div className="h-4 w-4 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5 text-amber-400">
                  <CheckCircle2 className="h-2.5 w-2.5" />
                </div>
                <span>{cap}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Right: Architecture I/O Contracts */}
        <div className="glass-card p-6 rounded-2xl border border-white/[0.08] bg-[#0c0c12]/90 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <Layers className="h-4 w-4 text-rose-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider font-mono">
                Architecture I/O Pipeline
              </h2>
            </div>
            <span className="text-[10px] font-mono text-zinc-500">Contract</span>
          </div>

          <div className="space-y-4">
            <div>
              <p className="text-[11px] font-mono uppercase text-zinc-400 font-semibold mb-2 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-500" />
                Expected Ingestion Inputs
              </p>
              <div className="flex flex-wrap gap-1.5">
                {agent.expectedInputs?.map((inp) => (
                  <span
                    key={inp}
                    className="px-2.5 py-1 rounded-lg text-xs font-mono bg-white/[0.04] text-zinc-300 border border-white/[0.08]"
                  >
                    {inp}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <p className="text-[11px] font-mono uppercase text-zinc-400 font-semibold mb-2 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Expected Analytical Outputs
              </p>
              <div className="flex flex-wrap gap-1.5">
                {agent.expectedOutputs?.map((out) => (
                  <span
                    key={out}
                    className="px-2.5 py-1 rounded-lg text-xs font-mono bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                  >
                    {out}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Multi-Agent Ecosystem Integration Notice ── */}
      <div className="glass-card p-5 rounded-xl border border-white/[0.07] bg-[#09090f]/90 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] text-zinc-400 shrink-0">
            <Cpu className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white">
              Supervisor Agent Orchestration Ready
            </h3>
            <p className="text-[11px] text-zinc-400">
              When activated, this agent registers directly into the Multi-Agent Router for unified synthesis.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onBackToOverview}
          className="text-xs font-mono text-rose-400 hover:text-rose-300 flex items-center gap-1.5 shrink-0"
        >
          <span>Return to Dashboard</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
