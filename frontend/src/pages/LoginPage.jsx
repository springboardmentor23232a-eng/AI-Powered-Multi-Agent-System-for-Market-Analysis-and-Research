import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Cpu, Lock, Mail, ArrowRight, Eye, EyeOff, Zap, Activity, PieChart, ShieldCheck } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const DEMO_EMAIL = 'demo@quantagent.com';
const DEMO_PASSWORD = 'DemoAnalyst@2026';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState(
    location.search.includes('expired=1') ? 'Your session has expired. Please sign in again.' : ''
  );

  const handleDirectDemoLogin = async () => {
    setErrorMessage('');
    setDemoLoading(true);
    try {
      try {
        const ok = await login(DEMO_EMAIL, DEMO_PASSWORD);
        if (ok) {
          navigate('/dashboard');
          return;
        }
      } catch {
        await api.post('/auth/register', {
          full_name: 'Demo Analyst',
          email: DEMO_EMAIL,
          password: DEMO_PASSWORD,
          confirm_password: DEMO_PASSWORD,
        });
        const ok = await login(DEMO_EMAIL, DEMO_PASSWORD);
        if (ok) {
          navigate('/dashboard');
        }
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(detail || 'Direct demo sign in failed.');
    } finally {
      setDemoLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSubmitting(true);

    try {
      const success = await login(email, password);
      if (success) {
        navigate('/dashboard');
      }
    } catch (err) {
      const detail = err.response?.data?.detail;
      setErrorMessage(detail || 'Authentication failed. Please verify your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen terminal-grid-bg flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Left Editorial Wealth Showcase */}
        <div className="lg:col-span-6 glass-panel rounded-3xl p-8 sm:p-10 flex flex-col justify-between relative overflow-hidden">
          <div className="absolute -right-20 -top-20 w-64 h-64 rounded-full bg-emerald-100/70 blur-3xl pointer-events-none" />
          <div className="space-y-6 relative z-10">
            <div className="inline-flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#0A624C] to-[#0D7A5F] flex items-center justify-center text-white shadow-md shadow-emerald-900/15">
                <Cpu className="w-6 h-6 stroke-[2.2]" />
              </div>
              <div>
                <h1 className="font-display text-xl font-bold text-slate-900 tracking-tight">
                  QUANT<span className="text-[#0A624C]">AGENT</span> STUDIO
                </h1>
                <p className="text-[11px] font-mono text-slate-500 uppercase tracking-widest">
                  Multi-Agent Equity Terminal
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <h2 className="font-display text-3xl font-bold text-slate-900 leading-tight">
                Autonomous Market Research, <span className="text-[#0A624C]">Verified by Math.</span>
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Real-time OHLCV validation across NSE, BSE, NASDAQ & NYSE paired with transparent Fundamental ratios and interactive Plotly Technical charts.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-8 relative z-10">
            <div className="p-3.5 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] space-y-1.5">
              <ShieldCheck className="w-4 h-4 text-[#0A624C]" />
              <p className="text-xs font-bold text-slate-900">OHLCV Validator</p>
              <p className="text-[11px] text-slate-500">Dedup & provenance hashes</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] space-y-1.5">
              <PieChart className="w-4 h-4 text-[#1E3A5F]" />
              <p className="text-xs font-bold text-slate-900">Fundamental</p>
              <p className="text-[11px] text-slate-500">P/E, P/B, ROE & peers</p>
            </div>
            <div className="p-3.5 rounded-2xl bg-[#FAF9F5] border border-[#E4E1D8] space-y-1.5">
              <Activity className="w-4 h-4 text-amber-600" />
              <p className="text-xs font-bold text-slate-900">Technical</p>
              <p className="text-[11px] text-slate-500">SMA, EMA, RSI & MACD</p>
            </div>
          </div>
        </div>

        {/* Right Sign-In Card */}
        <div className="lg:col-span-6 glass-panel rounded-3xl p-8 sm:p-10 flex flex-col justify-center">
          <div className="mb-6">
            <span className="text-[10px] font-mono uppercase tracking-widest text-[#0A624C] font-bold">
              JWT Session Auth
            </span>
            <h3 className="font-display text-2xl font-bold text-slate-900 mt-1">Sign in to Workspace</h3>
            <p className="text-xs text-slate-500 mt-1">
              Use instant one-click demo access or sign in with your analyst credentials
            </p>
          </div>

          {errorMessage && (
            <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-medium">
              {errorMessage}
            </div>
          )}

          <button
            type="button"
            onClick={handleDirectDemoLogin}
            disabled={submitting || demoLoading}
            className="w-full py-3.5 px-4 mb-5 bg-[#0A624C] hover:bg-[#084C3B] text-white font-bold rounded-xl shadow-md shadow-emerald-900/15 transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-60"
          >
            {demoLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Entering Studio...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-amber-300 fill-amber-300" />
                <span>Quick Direct Sign In (Demo Analyst)</span>
              </>
            )}
          </button>

          <div className="relative flex py-2 items-center mb-5">
            <div className="flex-grow border-t border-[#E4E1D8]" />
            <span className="flex-shrink mx-3 text-[10px] font-mono uppercase text-slate-400">
              OR CREDENTIALS
            </span>
            <div className="flex-grow border-t border-[#E4E1D8]" />
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@quantagent.com"
                  className="w-full pl-10 pr-4 py-2.5 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-slate-900 placeholder:text-slate-400 text-sm focus:bg-white focus:outline-none focus:border-[#0A624C]"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-10 py-2.5 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-slate-900 placeholder:text-slate-400 text-sm focus:bg-white focus:outline-none focus:border-[#0A624C]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting || demoLoading}
              className="w-full py-3 px-4 bg-[#1E3A5F] hover:bg-[#162C49] text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2 text-sm disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Verifying Session...</span>
                </>
              ) : (
                <>
                  <span>Sign In with Credentials</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-[#E4E1D8] text-center">
            <p className="text-xs text-slate-500">
              Need an analyst account?{' '}
              <Link to="/register" className="font-semibold text-[#0A624C] hover:text-emerald-800">
                Register now
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
