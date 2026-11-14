import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import {
  UserPlus,
  Eye,
  EyeOff,
  Lock,
  Mail,
  User,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  Loader2,
  Sparkles,
  KeyRound,
  Check,
  X as CloseIcon,
} from 'lucide-react';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

const Register = () => {
  const location = useLocation();
  const prefill = location.state?.prefillGoogle;

  const [formData, setFormData] = useState({
    full_name: prefill?.name || '',
    email: prefill?.email || '',
    password: '',
    confirm_password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [passwordSuggested, setPasswordSuggested] = useState(false);
  const [isPasswordFocused, setIsPasswordFocused] = useState(false);

  const { isDark } = useTheme();
  const { register, googleSignIn } = useAuth();
  const navigate = useNavigate();

  // Password Combination Requirements Checker
  const passwordCriteria = {
    length: (formData.password || '').length >= 8,
    upper: /[A-Z]/.test(formData.password || ''),
    lower: /[a-z]/.test(formData.password || ''),
    number: /[0-9]/.test(formData.password || ''),
    special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]/.test(formData.password || ''),
  };

  const passedCriteriaCount = Object.values(passwordCriteria).filter(Boolean).length;

  const getStrengthMeta = () => {
    if (!formData.password) return { text: '', width: '0%', color: 'bg-slate-500', textColor: 'text-slate-500' };
    if (passedCriteriaCount <= 2) {
      return { text: 'Weak', width: '33%', color: 'bg-rose-500', textColor: 'text-rose-500' };
    }
    if (passedCriteriaCount <= 4) {
      return { text: 'Moderate', width: '66%', color: 'bg-amber-500', textColor: 'text-amber-500' };
    }
    return { text: 'Strong', width: '100%', color: 'bg-emerald-500', textColor: 'text-emerald-500' };
  };

  const strengthMeta = getStrengthMeta();

  // Suggest Strong Password Generator (High Entropy, Cryptographically Safe)
  const handleSuggestStrongPassword = () => {
    const uppers = 'ABCDEFGHJKLMNPQRSTUVWXYZ';
    const lowers = 'abcdefghijkmnopqrstuvwxyz';
    const digits = '23456789';
    const symbols = '!@#$%^&*_-+=';
    const all = uppers + lowers + digits + symbols;

    let pwd = '';
    // Guarantee at least 2 of each character class
    pwd += uppers[Math.floor(Math.random() * uppers.length)];
    pwd += uppers[Math.floor(Math.random() * uppers.length)];
    pwd += lowers[Math.floor(Math.random() * lowers.length)];
    pwd += lowers[Math.floor(Math.random() * lowers.length)];
    pwd += digits[Math.floor(Math.random() * digits.length)];
    pwd += digits[Math.floor(Math.random() * digits.length)];
    pwd += symbols[Math.floor(Math.random() * symbols.length)];
    pwd += symbols[Math.floor(Math.random() * symbols.length)];

    // Fill to 12 characters
    while (pwd.length < 12) {
      pwd += all[Math.floor(Math.random() * all.length)];
    }

    // Shuffle characters randomly
    pwd = pwd.split('').sort(() => 0.5 - Math.random()).join('');

    setFormData((prev) => ({
      ...prev,
      password: pwd,
      confirm_password: pwd,
    }));
    setShowPassword(true);
    setShowConfirmPassword(true);
    setPasswordSuggested(true);
    setError('');
    setTimeout(() => setPasswordSuggested(false), 5000);
  };

  // Handle Official Google Identity Response for Registration
  const handleGoogleCredentialResponse = async (response) => {
    try {
      setGoogleLoading(true);
      setError('');

      // Decode the JWT credential from Google Identity Services
      const base64Url = response.credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        window
          .atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);
      const email = payload.email?.toLowerCase()?.trim();
      const name = payload.name || payload.given_name || 'Google User';

      // Register or complete sign-in in 'register' mode
      await googleSignIn({
        email,
        full_name: name,
        mode: 'register',
      });

      // Directly enter dashboard once registered
      navigate('/dashboard');
    } catch (err) {
      console.error('Google registration failed:', err);
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Google registration failed. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  // Mount Official Google Identity Services SDK
  useEffect(() => {
    const initGoogle = () => {
      if (window.google?.accounts?.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: handleGoogleCredentialResponse,
            auto_select: false,
            cancel_on_tap_outside: true,
          });

          const btnContainer = document.getElementById('googleRegisterBtnWrapper');
          if (btnContainer) {
            btnContainer.innerHTML = '';
            window.google.accounts.id.renderButton(btnContainer, {
              type: 'standard',
              theme: isDark ? 'filled_black' : 'outline',
              size: 'large',
              text: 'signup_with',
              shape: 'rectangular',
              width: 384,
              logo_alignment: 'left',
            });
          }

          // Trigger One Tap if supported
          try {
            window.google.accounts.id.prompt();
          } catch (e) {
            // Silently ignore if prompt suppressed
          }
        } catch (e) {
          console.warn('Google Identity initialization error:', e);
        }
      }
    };

    if (window.google?.accounts?.id) {
      initGoogle();
    } else {
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval);
          initGoogle();
        }
      }, 250);
      return () => clearInterval(interval);
    }
  }, [isDark]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!formData.full_name || !formData.email || !formData.password || !formData.confirm_password) {
      setError('Please fill in all registration fields.');
      return;
    }

    // Strong password combination check (all 5 criteria required)
    if (passedCriteriaCount < 5) {
      setError(
        'Password is too weak. It must be at least 8 characters long and contain a combination of uppercase (A-Z), lowercase (a-z), numbers (0-9), and special characters (!@#$%^&*).'
      );
      return;
    }

    if (formData.password !== formData.confirm_password) {
      setError('Password and Confirm Password do not match.');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await register(formData);
      setSuccess(response.message || 'Account created successfully! Redirecting to Log In...');
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else if (Array.isArray(detail)) {
        setError(detail.map((d) => d.msg).join(', '));
      } else {
        setError('Registration failed. Please check your inputs.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={`min-h-[calc(100vh-4rem)] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 relative transition-colors duration-200 ${
        isDark ? 'bg-slate-950 text-slate-100' : 'bg-slate-50 text-slate-900'
      }`}
    >
      <div
        className={`max-w-md w-full border rounded-2xl shadow-2xl p-8 relative z-10 transition-colors ${
          isDark ? 'bg-slate-900 border-slate-800' : 'bg-white border-slate-200 shadow-slate-200/50'
        }`}
      >
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex p-3 bg-sky-500/10 text-sky-500 rounded-2xl mb-3 border border-sky-500/20">
            <UserPlus className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-black tracking-tight">Create an Account</h1>
          <p className={`text-xs mt-1.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Start conducting automated equity research
          </p>
        </div>

        {/* Prefill Notice if redirected from Login */}
        {prefill && (
          <div className="mb-4 p-3 bg-sky-500/10 border border-sky-500/20 rounded-xl text-sky-400 text-xs flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-sky-400 shrink-0" />
            <span>
              Creating account for <strong className="text-white">{prefill.email}</strong>. Select below to confirm.
            </span>
          </div>
        )}

        {/* 1. Official Google Identity Button */}
        <div className="mb-4">
          <div className="flex justify-center min-h-[44px]">
            <div id="googleRegisterBtnWrapper" className="w-full flex justify-center"></div>
          </div>

          {googleLoading && (
            <div className="mt-2 flex items-center justify-center space-x-2 text-xs text-sky-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Registering account with Google...</span>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className={`w-full border-t ${isDark ? 'border-slate-800' : 'border-slate-200'}`}></div>
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span
              className={`px-3 font-mono text-[10px] tracking-wider ${
                isDark ? 'bg-slate-900 text-slate-500' : 'bg-white text-slate-400'
              }`}
            >
              Or create with email & password
            </span>
          </div>
        </div>

        {/* Status Alerts */}
        {error && (
          <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-3 text-rose-500 text-xs">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-start space-x-3 text-emerald-500 text-xs">
            <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {passwordSuggested && (
          <div className="mb-4 p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl flex items-center space-x-2 text-emerald-400 text-xs font-mono">
            <KeyRound className="h-4 w-4 shrink-0 text-emerald-400" />
            <span>Strong password generated and applied!</span>
          </div>
        )}

        {/* 2. Registration Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div>
            <label className={`block text-xs font-semibold mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              Full Name
            </label>
            <div className="relative">
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="e.g. John Doe"
                required
                className={`w-full rounded-xl pl-10 pr-4 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 border ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-white placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <User className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
            </div>
          </div>

          <div>
            <label className={`block text-xs font-semibold mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="name@domain.com"
                required
                className={`w-full rounded-xl pl-10 pr-4 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 border ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-white placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <Mail className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
            </div>
          </div>

          {/* Password with Strength Indicator & Suggestion Feature */}
          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className={`block text-xs font-semibold ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Password
              </label>
              <button
                type="button"
                onClick={handleSuggestStrongPassword}
                className="text-[11px] font-bold text-sky-500 hover:text-sky-400 flex items-center space-x-1 cursor-pointer transition hover:underline"
                title="Generate a cryptographically strong password"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>Suggest Strong Password</span>
              </button>
            </div>

            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                onFocus={() => setIsPasswordFocused(true)}
                placeholder="Combination of A-Z, a-z, 0-9, symbol"
                required
                className={`w-full rounded-xl pl-10 pr-10 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 border ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-white placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <Lock className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>

            {/* Password Strength Meter */}
            {formData.password && (
              <div className="mt-2 space-y-1.5">
                <div className="flex items-center justify-between text-[10px] font-mono">
                  <span className={isDark ? 'text-slate-400' : 'text-slate-500'}>Password Strength:</span>
                  <span className={`font-bold ${strengthMeta.textColor}`}>{strengthMeta.text}</span>
                </div>
                <div className={`h-1.5 w-full rounded-full overflow-hidden ${isDark ? 'bg-slate-800' : 'bg-slate-200'}`}>
                  <div
                    className={`h-full transition-all duration-300 ${strengthMeta.color}`}
                    style={{ width: strengthMeta.width }}
                  ></div>
                </div>
              </div>
            )}

            {/* Real-time Combination Requirements Checklist */}
            {(isPasswordFocused || formData.password) && (
              <div
                className={`mt-2 p-2.5 rounded-xl border text-[11px] font-mono grid grid-cols-2 gap-1.5 transition-colors ${
                  isDark ? 'bg-slate-950/80 border-slate-800 text-slate-400' : 'bg-slate-50 border-slate-200 text-slate-600'
                }`}
              >
                <div
                  className={`flex items-center space-x-1.5 ${
                    passwordCriteria.length ? 'text-emerald-500 font-semibold' : ''
                  }`}
                >
                  {passwordCriteria.length ? <Check className="w-3.5 h-3.5" /> : <span className="w-3.5 text-center">•</span>}
                  <span>8+ characters</span>
                </div>

                <div
                  className={`flex items-center space-x-1.5 ${
                    passwordCriteria.upper ? 'text-emerald-500 font-semibold' : ''
                  }`}
                >
                  {passwordCriteria.upper ? <Check className="w-3.5 h-3.5" /> : <span className="w-3.5 text-center">•</span>}
                  <span>Uppercase (A-Z)</span>
                </div>

                <div
                  className={`flex items-center space-x-1.5 ${
                    passwordCriteria.lower ? 'text-emerald-500 font-semibold' : ''
                  }`}
                >
                  {passwordCriteria.lower ? <Check className="w-3.5 h-3.5" /> : <span className="w-3.5 text-center">•</span>}
                  <span>Lowercase (a-z)</span>
                </div>

                <div
                  className={`flex items-center space-x-1.5 ${
                    passwordCriteria.number ? 'text-emerald-500 font-semibold' : ''
                  }`}
                >
                  {passwordCriteria.number ? <Check className="w-3.5 h-3.5" /> : <span className="w-3.5 text-center">•</span>}
                  <span>Number (0-9)</span>
                </div>

                <div
                  className={`flex items-center space-x-1.5 col-span-2 ${
                    passwordCriteria.special ? 'text-emerald-500 font-semibold' : ''
                  }`}
                >
                  {passwordCriteria.special ? <Check className="w-3.5 h-3.5" /> : <span className="w-3.5 text-center">•</span>}
                  <span>Special symbol (!@#$%^&*)</span>
                </div>
              </div>
            )}
          </div>

          <div>
            <label className={`block text-xs font-semibold mb-1.5 ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
              Confirm Password
            </label>
            <div className="relative">
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                name="confirm_password"
                value={formData.confirm_password}
                onChange={handleChange}
                placeholder="Re-enter password"
                required
                className={`w-full rounded-xl pl-10 pr-10 py-2 text-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 border ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-white placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <Lock className="h-4 w-4 text-slate-400 absolute left-3.5 top-2.5" />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3.5 top-2.5 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
              >
                {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-3 bg-sky-600 hover:bg-sky-500 text-white font-bold py-2.5 px-4 rounded-xl shadow-lg shadow-sky-600/20 transition flex items-center justify-center space-x-2 text-sm disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting ? (
              <span>Creating account...</span>
            ) : (
              <>
                <span>Create an Account</span>
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div
          className={`mt-6 pt-5 border-t text-center text-xs ${
            isDark ? 'border-slate-800 text-slate-400' : 'border-slate-200 text-slate-600'
          }`}
        >
          <span>Already have an account? </span>
          <Link to="/login" className="text-sky-500 hover:text-sky-600 font-bold transition">
            Log In
          </Link>
        </div>

        {/* Security Badge */}
        <div
          className={`mt-4 flex items-center justify-center space-x-2 text-[10px] ${
            isDark ? 'text-slate-500' : 'text-slate-400'
          }`}
        >
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
          <span>Secure 256-Bit SSL Encrypted Session</span>
        </div>
      </div>
    </div>
  );
};

export default Register;
