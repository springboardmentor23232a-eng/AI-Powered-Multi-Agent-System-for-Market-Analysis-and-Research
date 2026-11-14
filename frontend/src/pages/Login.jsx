import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { LogIn, Eye, EyeOff, Lock, Mail, AlertCircle, ArrowRight, ShieldCheck, UserPlus, Loader2 } from 'lucide-react';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [noAccountFoundUser, setNoAccountFoundUser] = useState(null);

  const { isDark } = useTheme();
  const { login, googleSignIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Official Google Identity Services (GIS) Callback
  const handleGoogleCredentialResponse = async (response) => {
    try {
      setGoogleLoading(true);
      setError('');
      setNoAccountFoundUser(null);

      // Decode the JWT payload returned by Google
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

      try {
        // Authenticate with backend in 'login' mode (strictly checks if account exists)
        await googleSignIn({
          email,
          full_name: name,
          mode: 'login',
        });
        navigate('/dashboard');
      } catch (err) {
        const detail = err.response?.data?.detail;
        if (
          err.response?.status === 404 ||
          (typeof detail === 'string' && detail.toLowerCase().includes('create an account'))
        ) {
          // Account not in database - notify user and prompt to create account
          setNoAccountFoundUser({ email, name });
        } else {
          setError(typeof detail === 'string' ? detail : 'Google Log In failed. Please try again.');
        }
      }
    } catch (err) {
      console.error('Google token decoding failed:', err);
      setError('Unable to authenticate with Google. Please try again.');
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

          const btnContainer = document.getElementById('googleLoginBtnWrapper');
          if (btnContainer) {
            btnContainer.innerHTML = '';
            window.google.accounts.id.renderButton(btnContainer, {
              type: 'standard',
              theme: isDark ? 'filled_black' : 'outline',
              size: 'large',
              text: 'continue_with',
              shape: 'rectangular',
              width: 384,
              logo_alignment: 'left',
            });
          }

          // Trigger One Tap if supported in this browser session
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
    setNoAccountFoundUser(null);

    if (!formData.email || !formData.password) {
      setError('Please enter both your email address and password.');
      return;
    }

    setIsSubmitting(true);

    try {
      await login(formData);
      navigate('/dashboard');
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError('Invalid credentials. Please verify your email and password.');
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
            <LogIn className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-black tracking-tight">Log In</h1>
          <p className={`text-xs mt-1.5 ${isDark ? 'text-slate-400' : 'text-slate-600'}`}>
            Access your stock research workspace
          </p>
        </div>

        {/* 1. Official Google Identity Button */}
        <div className="mb-4">
          <div className="flex justify-center min-h-[44px]">
            <div id="googleLoginBtnWrapper" className="w-full flex justify-center"></div>
          </div>

          {googleLoading && (
            <div className="mt-2 flex items-center justify-center space-x-2 text-xs text-sky-500">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Checking account with Google...</span>
            </div>
          )}
        </div>

        {/* Account Not Found Notification Banner */}
        {noAccountFoundUser && (
          <div className="mb-5 p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-200 text-xs">
            <div className="flex items-start space-x-2.5">
              <AlertCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-bold text-amber-300">Account Not Found</p>
                <p className="mt-1 text-slate-300 leading-relaxed">
                  No existing account found for{' '}
                  <span className="font-semibold text-white font-mono bg-slate-800/80 px-1.5 py-0.5 rounded border border-slate-700">
                    {noAccountFoundUser.email}
                  </span>
                  . Please create an account first to continue.
                </p>
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() =>
                      navigate('/register', {
                        state: { prefillGoogle: noAccountFoundUser },
                      })
                    }
                    className="w-full py-2 px-3 rounded-lg bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs transition flex items-center justify-center space-x-1.5 shadow-md cursor-pointer"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Create an Account with this Google Email</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

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
              Or log in with email
            </span>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-start space-x-3 text-rose-500 text-xs">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 2. Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
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
                className={`w-full rounded-xl pl-10 pr-4 py-2.5 text-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 border ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-white placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <Mail className="h-4 w-4 text-slate-400 absolute left-3.5 top-3" />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className={`block text-xs font-semibold ${isDark ? 'text-slate-300' : 'text-slate-700'}`}>
                Password
              </label>
            </div>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter password"
                required
                className={`w-full rounded-xl pl-10 pr-10 py-2.5 text-sm transition focus:outline-none focus:ring-2 focus:ring-sky-500 border ${
                  isDark
                    ? 'bg-slate-950 border-slate-800 text-white placeholder-slate-600'
                    : 'bg-slate-50 border-slate-300 text-slate-900 placeholder-slate-400'
                }`}
              />
              <Lock className="h-4 w-4 text-slate-400 absolute left-3.5 top-3" />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-3 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full mt-2 bg-sky-600 hover:bg-sky-500 text-white font-bold py-2.5 px-4 rounded-xl shadow-lg shadow-sky-600/20 transition flex items-center justify-center space-x-2 text-sm disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting ? (
              <span>Logging in...</span>
            ) : (
              <>
                <span>Log In</span>
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
          <span>Don't have an account? </span>
          <Link to="/register" className="text-sky-500 hover:text-sky-600 font-bold transition">
            Create an Account
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

export default Login;
