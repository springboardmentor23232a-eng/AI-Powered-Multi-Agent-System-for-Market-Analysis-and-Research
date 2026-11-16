/**
 * LoginPage.jsx
 * Full-page login interface for SAI ANALYSIS:
 * Pitch black (#060608), dark charcoal (#0d0d13), crimson accents (#e11d48), and subtle red ambient glow.
 */

import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { TrendingUp, LogIn, Eye, EyeOff } from 'lucide-react';
import InputField from '../components/ui/InputField';
import AlertBanner from '../components/ui/AlertBanner';
import Spinner from '../components/ui/Spinner';

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
        <linearGradient id="loginCrimsonGrad" x1="0%" y1="0%" x2="0%" y2="100%">
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
        fill="url(#loginCrimsonGrad)"
      />
    </svg>
  );
}

export default function LoginPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // Pick up pre-filled email and success notice if navigated from registration
  const redirectedEmail = location.state?.registeredEmail || '';
  const redirectedNotice = location.state?.message || null;

  const [email, setEmail] = useState(redirectedEmail);
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [infoMessage, setInfoMessage] = useState(redirectedNotice);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;
    setError(null);

    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }
    if (!password) {
      setError('Password is required.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          email: email.trim().toLowerCase(),
          password: password,
        }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch {
        // Fallback for non-JSON response
      }

      if (!response.ok) {
        throw new Error(data.detail || 'Invalid email or password. Please try again.');
      }

      // Store authenticated user session
      localStorage.setItem('currentUser', JSON.stringify(data.data));

      setInfoMessage(`Welcome back, ${data.data.full_name}! Redirecting to dashboard…`);
      
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    } catch (err) {
      if (err.name === 'TypeError' && err.message.toLowerCase().includes('fetch')) {
        setError('Unable to connect to the backend server. Please verify the API is running.');
      } else {
        setError(err.message || 'Login failed. Please check your credentials.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

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

      {/* Background financial chart curve */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-44 overflow-hidden">
        <ChartDecoration />
      </div>

      {/* ── Login Glass Card ── */}
      <div className="glass-card relative z-10 w-full max-w-md animate-fade-in p-8 sm:p-10 border border-white/[0.08] bg-[#0d0d13]/90">
        {/* Brand header */}
        <header className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-950/70 to-[#120a0e] border border-rose-500/30 text-rose-500 shadow-crimson-md">
            <TrendingUp className="h-7 w-7 text-rose-500" aria-hidden="true" />
          </div>

          <div className="inline-flex items-center gap-1.5 px-3 py-1 mb-2.5 rounded-full bg-white/[0.04] border border-white/[0.08] text-[11px] font-semibold tracking-wider uppercase text-zinc-300">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-500 animate-pulse" />
            SAI ANALYSIS
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Welcome <span className="text-crimson-gradient">Back</span>
          </h1>
          <p className="mt-2 text-xs sm:text-sm text-zinc-400">
            Multi-Agent Stock Research & Market Intelligence
          </p>
        </header>

        {/* Notifications */}
        <div className="mb-5 space-y-3">
          {infoMessage && <AlertBanner message={infoMessage} variant="info" />}
          {error && <AlertBanner message={error} variant="error" />}
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
          <InputField
            id="loginEmail"
            name="email"
            label="Email Address"
            type="email"
            value={email}
            placeholder="jane@example.com"
            required
            autoComplete="email"
            onChange={(e) => {
              setEmail(e.target.value);
              setError(null);
            }}
          />

          <InputField
            id="loginPassword"
            name="password"
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            placeholder="Enter your password"
            required
            autoComplete="current-password"
            onChange={(e) => {
              setPassword(e.target.value);
              setError(null);
            }}
            rightSlot={
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="text-zinc-400 hover:text-rose-400 transition-colors focus:outline-none"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" aria-hidden="true" />
                ) : (
                  <Eye className="h-4 w-4" aria-hidden="true" />
                )}
              </button>
            }
          />

          <div className="flex items-center justify-between text-xs text-zinc-400 mt-0.5">
            <label className="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                className="h-3.5 w-3.5 rounded border-white/[0.15] bg-[#0c0c12] text-rose-600 focus:ring-rose-500/30"
              />
              <span>Remember me</span>
            </label>
            <span className="cursor-pointer text-zinc-400 hover:text-rose-400 transition-colors">
              Forgot password?
            </span>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
            className="btn-primary mt-2 py-3"
          >
            {isSubmitting ? (
              <>
                <Spinner className="h-4 w-4" />
                <span>Signing in…</span>
              </>
            ) : (
              <>
                <LogIn className="h-4 w-4" aria-hidden="true" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        {/* Link back to registration */}
        <p className="mt-7 text-center text-xs sm:text-sm text-zinc-400">
          Don't have an account?{' '}
          <Link
            to="/register"
            className="font-semibold text-rose-400 underline-offset-2 hover:underline hover:text-rose-300 transition-colors"
          >
            Create an account
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

