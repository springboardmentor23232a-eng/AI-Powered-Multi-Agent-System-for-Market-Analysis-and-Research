import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Mail, Lock, Eye, EyeOff, UserPlus, Check, AlertCircle, Loader2 } from 'lucide-react';
import AuthLayout from '../components/AuthLayout';
import SocialLogin from '../components/SocialLogin';
import { useAuth } from '../context/AuthContext';

export const Register = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  // Live password validation checks
  const password = formData.password;
  const checks = {
    length: password.length >= 8,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /[0-9]/.test(password),
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
  };

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
    setSuccessMsg('');

    // Client-side validations
    if (!formData.fullName.trim()) {
      setErrorMsg('Full Name is required.');
      return;
    }
    if (!formData.email.trim()) {
      setErrorMsg('Email Address is required.');
      return;
    }
    if (!checks.length || !checks.upper || !checks.lower || !checks.number || !checks.special) {
      setErrorMsg('Please ensure all password criteria are satisfied.');
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setErrorMsg('Passwords do not match.');
      return;
    }

    try {
      setLoading(true);
      await register({
        full_name: formData.fullName.trim(),
        email: formData.email.trim(),
        password: formData.password,
        confirm_password: formData.confirmPassword,
      });

      setSuccessMsg('Account created successfully! Please sign in to continue.');
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err) {
      setErrorMsg(err.message || 'Registration failed. Please try again.');
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
          <h2 className="text-2xl font-bold text-white tracking-tight">Sign Up</h2>
          <p className="text-xs sm:text-sm text-slate-400">Create your account to get started</p>
        </div>
      </div>

      {/* Success Notification */}
      {successMsg && (
        <div className="mb-4 p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs sm:text-sm flex items-center gap-2">
          <Check className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Error Notification */}
      {errorMsg && (
        <div className="mb-4 p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-300 text-xs sm:text-sm flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Full Name */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Full Name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <User className="w-4 h-4" />
            </div>
            <input
              type="text"
              name="fullName"
              value={formData.fullName}
              onChange={handleChange}
              placeholder="Enter your full name"
              required
              className="w-full pl-10 pr-4 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
          </div>
        </div>

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
              placeholder="Create a strong password"
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

          {/* Password Requirements Checklist (2 columns) */}
          <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 mt-2.5 text-[11px] text-slate-400">
            <div className="space-y-1">
              <div className={`flex items-center gap-1.5 ${checks.length ? 'text-emerald-400' : 'text-slate-400'}`}>
                <Check className={`w-3.5 h-3.5 ${checks.length ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span>At least 8 characters</span>
              </div>
              <div className={`flex items-center gap-1.5 ${checks.upper ? 'text-emerald-400' : 'text-slate-400'}`}>
                <Check className={`w-3.5 h-3.5 ${checks.upper ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span>One uppercase letter</span>
              </div>
              <div className={`flex items-center gap-1.5 ${checks.lower ? 'text-emerald-400' : 'text-slate-400'}`}>
                <Check className={`w-3.5 h-3.5 ${checks.lower ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span>One lowercase letter</span>
              </div>
            </div>

            <div className="space-y-1">
              <div className={`flex items-center gap-1.5 ${checks.number ? 'text-emerald-400' : 'text-slate-400'}`}>
                <Check className={`w-3.5 h-3.5 ${checks.number ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span>One number</span>
              </div>
              <div className={`flex items-center gap-1.5 ${checks.special ? 'text-emerald-400' : 'text-slate-400'}`}>
                <Check className={`w-3.5 h-3.5 ${checks.special ? 'text-emerald-400' : 'text-slate-600'}`} />
                <span>One special character</span>
              </div>
            </div>
          </div>
        </div>

        {/* Confirm Password */}
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1.5">
            Confirm Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showConfirmPassword ? 'text' : 'password'}
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="Confirm your password"
              required
              className="w-full pl-10 pr-10 py-2.5 bg-[#111620] border border-[#1e293b] rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-200"
            >
              {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Create Account Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full mt-3 py-3 px-4 rounded-lg bg-[#00a86b] hover:bg-[#00ba77] text-white font-semibold text-sm flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/30 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Creating Account...</span>
            </>
          ) : (
            <>
              <UserPlus className="w-4 h-4" />
              <span>Create Account</span>
            </>
          )}
        </button>
      </form>

      {/* Social Authentication */}
      <SocialLogin />

      {/* Bottom Redirect Link */}
      <div className="mt-5 text-center text-xs text-slate-400">
        Already have an account?{' '}
        <Link to="/login" className="text-[#00d084] hover:underline font-medium">
          Sign In
        </Link>
      </div>
    </AuthLayout>
  );
};

export default Register;

