/**
 * RegisterPage.jsx
 * Full-page layout that wraps RegistrationForm inside a glass card
 * centred on a dark gradient background with decorative market-chart SVG.
 * Color theme: Pitch black (#060608), dark charcoal (#0d0d13), crimson accents (#e11d48)
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp } from 'lucide-react';
import RegistrationForm from '../components/auth/RegistrationForm';

// ── Decorative background financial chart line ───────
function ChartDecoration() {
  return (
    <svg
      viewBox="0 0 500 120"
      xmlns="http://www.w3.org/2000/svg"
      className="absolute bottom-0 left-0 right-0 w-full opacity-35"
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="registerCrimsonGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#e11d48" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#060608" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        points="0,95 40,82 85,88 130,62 175,70 220,40 265,52 310,28 355,42 400,18 450,30 500,12"
        fill="none"
        stroke="#f43f5e"
        strokeWidth="2.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <polygon
        points="0,95 40,82 85,88 130,62 175,70 220,40 265,52 310,28 355,42 400,18 450,30 500,12 500,120 0,120"
        fill="url(#registerCrimsonGrad)"
      />
    </svg>
  );
}

export default function RegisterPage() {
  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-[#060608] px-4 py-12">
      {/* ── Ambient Crimson Lighting ── */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-32 left-1/2 -translate-x-1/2 h-[500px] w-[800px] rounded-full bg-gradient-to-b from-rose-600/20 via-red-600/10 to-transparent blur-3xl opacity-80"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-48 right-1/4 h-80 w-80 rounded-full bg-rose-600/10 blur-3xl"
      />

      {/* Chart decoration */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-44 overflow-hidden">
        <ChartDecoration />
      </div>

      {/* ── Card ── */}
      <div className="glass-card relative z-10 w-full max-w-md animate-fade-in p-8 sm:p-10 border border-white/[0.08] bg-[#0d0d13]/90">
        {/* Brand header */}
        <header className="mb-8 text-center">
          {/* Logo mark */}
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-950/70 to-[#120a0e] border border-rose-500/30 text-rose-500 shadow-crimson-md">
            <TrendingUp className="h-7 w-7 text-rose-500" aria-hidden="true" />
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 mb-2.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px] font-semibold tracking-wider uppercase text-zinc-300">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
            SAI ANALYSIS
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Create an <span className="text-crimson-gradient">Account</span>
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-zinc-400">
            Multi-Agent Stock Research & Market Intelligence
          </p>
        </header>

        {/* Registration form */}
        <RegistrationForm />

        {/* Footer link to login */}
        <p className="mt-7 text-center text-xs sm:text-sm text-zinc-400">
          Already have an account?{' '}
          <Link
            to="/login"
            className="font-semibold text-rose-400 underline-offset-2 hover:underline hover:text-rose-300 transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>

      {/* Footer stamp */}
      <p className="relative z-10 mt-6 text-xs text-zinc-600 select-none font-mono">
        © {new Date().getFullYear()} SAI ANALYSIS • Multi-Agent Stock Research & Market Intelligence
      </p>
    </div>
  );
}
