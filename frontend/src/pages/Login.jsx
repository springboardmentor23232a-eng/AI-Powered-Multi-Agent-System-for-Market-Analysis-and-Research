import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, Eye, EyeOff, LogIn, AlertCircle, Loader2, User } from 'lucide-react';
import AuthLayout from '../components/AuthLayout';
import SocialLogin from '../components/SocialLogin';
import { useAuth } from '../context/AuthContext';

export const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
    setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');

    if (!formData.email.trim() || !formData.password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    try {
      setLoading(true);
      await login(formData.email.trim(), formData.password);
      navigate('/dashboard');
    } catch (err) {
      setErrorMsg(err.message || 'Invalid email or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      headingTop="AI-Powered"
      headingHighlight="Stock Research Analyst"
      subtitle="Transform your investment strategy with multi-agent fundamental, technical, news, and risk intelligence."
    >
      {/* Header of Form Card */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-full border border-emerald-500/50 bg-emerald-950/20 flex items-center justify-center text-[#00d084]">
          <User className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Welcome Back</h2>
          <p className="text-xs sm:text-sm text-slate-400">Sign in to access your stock research workspace</p>
        </div>
      </div>

      {/* Error Notification */}
      {errorMsg && (
        <div className="mb-4 p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs sm:text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Email Address */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Email Address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email address"
              required
              className="w-full pl-10 pr-4 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
        </div>

        {/* Password */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
              className="w-full pl-10 pr-10 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Sign In Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full mt-3 py-3 px-4 rounded-lg bg-[#00a86b] hover:bg-[#00ba77] text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/30 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Signing In...</span>
            </>
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </>
          )}
        </button>
      </form>

      {/* Social Authentication */}
      <SocialLogin />

      {/* Bottom Redirect Link */}
      <div className="mt-5 text-center text-xs text-slate-400">
        Don't have an account?{' '}
        <Link to="/register" className="text-[#00d084] hover:underline font-medium">
          Create Account
        </Link>
      </div>
    </AuthLayout>
  );
};

export default Login;

