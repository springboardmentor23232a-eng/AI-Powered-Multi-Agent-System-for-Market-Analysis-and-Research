/**
 * RegistrationForm.jsx
 * The core registration form component.
 * - Fully controlled via useRegistrationForm hook
 * - Show/hide password for both password fields
 * - Live password-strength bar
 * - Accessible (aria-* attributes, role="alert")
 * - Submission-safe (button disabled while in-flight)
 * - Ready for FastAPI integration (see useRegistrationForm.js)
 */

import React, { useState } from 'react';
import { Eye, EyeOff, UserPlus } from 'lucide-react';

import { useRegistrationForm } from '../../hooks/useRegistrationForm';
import InputField from '../ui/InputField';
import PasswordStrengthBar from '../ui/PasswordStrengthBar';
import AlertBanner from '../ui/AlertBanner';
import Spinner from '../ui/Spinner';

// Reusable toggle button for password visibility
function ToggleBtn({ visible, onToggle, label }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={visible ? `Hide ${label}` : `Show ${label}`}
      className="text-slate-500 transition-colors hover:text-slate-300 focus:outline-none focus-visible:text-slate-300"
      tabIndex={0}
    >
      {visible ? (
        <EyeOff className="h-4 w-4" aria-hidden="true" />
      ) : (
        <Eye className="h-4 w-4" aria-hidden="true" />
      )}
    </button>
  );
}

export default function RegistrationForm() {
  const {
    values,
    errors,
    touched,
    isSubmitting,
    apiError,
    successMessage,
    handleChange,
    handleBlur,
    handleSubmit,
    isFieldValid,
  } = useRegistrationForm();

  // Show / hide password toggles (independent per field)
  const [showPassword,        setShowPassword]        = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      aria-label="Create account form"
      className="flex flex-col gap-5"
    >
      {/* API-level status alerts */}
      {apiError && <AlertBanner message={apiError} variant="error" />}
      {successMessage && <AlertBanner message={successMessage} variant="info" />}

      {/* Full Name */}
      <InputField
        id="fullName"
        name="fullName"
        label="Full Name"
        type="text"
        value={values.fullName}
        placeholder="Jane Doe"
        error={touched.fullName ? errors.fullName : ''}
        valid={isFieldValid('fullName')}
        required
        autoComplete="name"
        onChange={handleChange}
        onBlur={handleBlur}
      />

      {/* Email */}
      <InputField
        id="email"
        name="email"
        label="Email Address"
        type="email"
        value={values.email}
        placeholder="jane@example.com"
        error={touched.email ? errors.email : ''}
        valid={isFieldValid('email')}
        required
        autoComplete="email"
        onChange={handleChange}
        onBlur={handleBlur}
      />

      {/* Password */}
      <div>
        <InputField
          id="password"
          name="password"
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={values.password}
          placeholder="Min. 8 characters"
          error={touched.password ? errors.password : ''}
          valid={isFieldValid('password')}
          required
          autoComplete="new-password"
          onChange={handleChange}
          onBlur={handleBlur}
          rightSlot={
            <ToggleBtn
              visible={showPassword}
              onToggle={() => setShowPassword((v) => !v)}
              label="password"
            />
          }
        />
        <PasswordStrengthBar password={values.password} />
      </div>

      {/* Confirm Password */}
      <InputField
        id="confirmPassword"
        name="confirmPassword"
        label="Confirm Password"
        type={showConfirmPassword ? 'text' : 'password'}
        value={values.confirmPassword}
        placeholder="Re-enter your password"
        error={touched.confirmPassword ? errors.confirmPassword : ''}
        valid={isFieldValid('confirmPassword')}
        required
        autoComplete="new-password"
        onChange={handleChange}
        onBlur={handleBlur}
        rightSlot={
          <ToggleBtn
            visible={showConfirmPassword}
            onToggle={() => setShowConfirmPassword((v) => !v)}
            label="confirm password"
          />
        }
      />

      {/* Submit */}
      <button
        type="submit"
        disabled={isSubmitting}
        aria-busy={isSubmitting}
        className="btn-primary mt-2 py-3"
      >
        {isSubmitting ? (
          <>
            <Spinner className="h-4 w-4" />
            <span>Creating account…</span>
          </>
        ) : (
          <>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            <span>Create Account</span>
          </>
        )}
      </button>

      {/* Legal note */}
      <p className="text-center text-xs text-zinc-400 leading-relaxed">
        By creating an account you agree to our{' '}
        <span className="cursor-pointer text-rose-400 underline-offset-2 hover:underline hover:text-rose-300 transition-colors">
          Terms of Service
        </span>{' '}
        and{' '}
        <span className="cursor-pointer text-rose-400 underline-offset-2 hover:underline hover:text-rose-300 transition-colors">
          Privacy Policy
        </span>
        .
      </p>
    </form>
  );
}
