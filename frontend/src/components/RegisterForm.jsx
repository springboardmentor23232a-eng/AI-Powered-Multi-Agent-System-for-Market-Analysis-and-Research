import React, { useState } from 'react';
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react';
import FinCrewLogo from './FinCrewLogo';

export default function RegisterForm({ onSwitchToLogin, onRegisterSuccess }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const validateForm = () => {
    if (!fullName.trim()) {
      setErrorMessage('Please enter your full name.');
      return false;
    }
    if (!email.trim() || !email.includes('@')) {
      setErrorMessage('Please enter a valid email address.');
      return false;
    }
    if (password.length < 8) {
      setErrorMessage('Password must be at least 8 characters long.');
      return false;
    }
    if (!/[A-Z]/.test(password)) {
      setErrorMessage('Password must contain at least one uppercase letter.');
      return false;
    }
    if (!/[a-z]/.test(password)) {
      setErrorMessage('Password must contain at least one lowercase letter.');
      return false;
    }
    if (!/[0-9]/.test(password)) {
      setErrorMessage('Password must contain at least one number.');
      return false;
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      setErrorMessage('Password must contain at least one special character.');
      return false;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please re-enter.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    setSuccessMessage('');

    if (!validateForm()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: fullName.trim(),
          email: email.trim().toLowerCase(),
          password: password,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorDetail = 'Registration failed. Please try again.';
        if (typeof data.detail === 'string') {
          errorDetail = data.detail;
        } else if (Array.isArray(data.detail)) {
          errorDetail = data.detail.map((err) => err.msg || err.message).join(', ');
        }
        setErrorMessage(errorDetail);
        setLoading(false);
        return;
      }

      setSuccessMessage('Account created successfully! Logging you in...');
      if (onRegisterSuccess) {
        onRegisterSuccess(email, password);
      }
    } catch (err) {
      setErrorMessage('Network connection error. Is the FinCrew backend running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full flex flex-col items-center">
      {/* FinCrew Logo Badge & Wordmark */}
      <div className="mb-4 sm:mb-5">
        <FinCrewLogo size="md" />
      </div>

      {/* Heading matching reference typography */}
      <h1 className="text-3xl sm:text-[34px] leading-tight font-extrabold text-[#111827] text-center mb-6 tracking-tight">
        Create<br />account
      </h1>

      {/* Error Banner */}
      {errorMessage && (
        <div className="w-full mb-4 p-3 rounded-2xl bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-700 animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Success Banner */}
      {successMessage && (
        <div className="w-full mb-4 p-3 rounded-2xl bg-green-50 border border-green-200 text-xs text-green-700 text-center font-medium animate-fadeIn">
          {successMessage}
        </div>
      )}

      {/* Registration Form */}
      <form onSubmit={handleSubmit} className="w-full space-y-3.5">
        {/* Full Name */}
        <div>
          <label htmlFor="reg-fullname" className="sr-only">Full name</label>
          <input
            id="reg-fullname"
            type="text"
            placeholder="Full name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            disabled={loading}
            className="w-full h-11 sm:h-12 px-5 rounded-full border border-gray-200/90 bg-white text-[15px] text-[#111827] placeholder-gray-400 focus:outline-none focus:border-[#9bd946] focus:ring-2 focus:ring-[#9bd946]/25 transition-all shadow-sm disabled:opacity-50"
            required
          />
        </div>

        {/* Email Address */}
        <div>
          <label htmlFor="reg-email" className="sr-only">Email address</label>
          <input
            id="reg-email"
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            className="w-full h-11 sm:h-12 px-5 rounded-full border border-gray-200/90 bg-white text-[15px] text-[#111827] placeholder-gray-400 focus:outline-none focus:border-[#9bd946] focus:ring-2 focus:ring-[#9bd946]/25 transition-all shadow-sm disabled:opacity-50"
            required
          />
        </div>

        {/* Password */}
        <div className="relative">
          <label htmlFor="reg-password" className="sr-only">Password</label>
          <input
            id="reg-password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            className="w-full h-11 sm:h-12 pl-5 pr-12 rounded-full border border-gray-200/90 bg-white text-[15px] text-[#111827] placeholder-gray-400 focus:outline-none focus:border-[#9bd946] focus:ring-2 focus:ring-[#9bd946]/25 transition-all shadow-sm disabled:opacity-50"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition p-1 cursor-pointer"
            tabIndex={-1}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        {/* Confirm Password */}
        <div className="relative">
          <label htmlFor="reg-confirm" className="sr-only">Confirm password</label>
          <input
            id="reg-confirm"
            type={showConfirmPassword ? 'text' : 'password'}
            placeholder="Confirm password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading}
            className="w-full h-11 sm:h-12 pl-5 pr-12 rounded-full border border-gray-200/90 bg-white text-[15px] text-[#111827] placeholder-gray-400 focus:outline-none focus:border-[#9bd946] focus:ring-2 focus:ring-[#9bd946]/25 transition-all shadow-sm disabled:opacity-50"
            required
          />
          <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition p-1 cursor-pointer"
            tabIndex={-1}
            aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
          >
            {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>

        {/* Submit Button (Lime Green Pill matching reference) */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full h-11 sm:h-12 rounded-full bg-[#9bd946] hover:bg-[#8ec93b] active:scale-[0.99] font-bold text-[#111827] text-[15px] sm:text-[16px] transition-all shadow-md shadow-[#9bd946]/30 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-[#111827]" />
                <span>Creating account...</span>
              </>
            ) : (
              <span>Create account</span>
            )}
          </button>
        </div>
      </form>

      {/* Navigation Link to Login */}
      <div className="mt-6 sm:mt-7 text-center text-sm text-[#4b5563]">
        Have an account?{' '}
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="font-bold text-[#1f4631] hover:text-[#9bd946] transition underline-offset-2 hover:underline cursor-pointer ml-0.5"
        >
          Log in
        </button>
      </div>
    </div>
  );
}
