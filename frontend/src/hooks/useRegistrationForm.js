/**
 * useRegistrationForm.js
 * Custom hook that owns all form state, validation logic, and
 * the (future) FastAPI submit integration for user registration.
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

// ── Validation helpers ──────────────────────────────────────────────────────

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_MIN = 8;

/**
 * Validate a single field and return an error string (or empty string).
 * @param {string} name  – field name
 * @param {string} value – current value
 * @param {object} allValues – sibling field values (needed for confirmPassword)
 */
function validateField(name, value, allValues = {}) {
  switch (name) {
    case 'fullName':
      if (!value.trim()) return 'Full name is required.';
      if (value.trim().length < 2) return 'Name must be at least 2 characters.';
      return '';

    case 'email':
      if (!value.trim()) return 'Email address is required.';
      if (!EMAIL_REGEX.test(value.trim())) return 'Please enter a valid email address.';
      return '';

    case 'password':
      if (!value) return 'Password is required.';
      if (value.length < PASSWORD_MIN)
        return `Password must be at least ${PASSWORD_MIN} characters.`;
      if (!/[A-Z]/.test(value)) return 'Include at least one uppercase letter.';
      if (!/[0-9]/.test(value)) return 'Include at least one number.';
      return '';

    case 'confirmPassword':
      if (!value) return 'Please confirm your password.';
      if (value !== allValues.password) return 'Passwords do not match.';
      return '';

    default:
      return '';
  }
}

/**
 * Validate every field and return a map of { fieldName: errorString }.
 */
function validateAll(values) {
  return {
    fullName:        validateField('fullName',        values.fullName,        values),
    email:           validateField('email',           values.email,           values),
    password:        validateField('password',        values.password,        values),
    confirmPassword: validateField('confirmPassword', values.confirmPassword, values),
  };
}

// ── Hook ────────────────────────────────────────────────────────────────────

const INITIAL_VALUES = {
  fullName:        '',
  email:           '',
  password:        '',
  confirmPassword: '',
};

const INITIAL_ERRORS = {
  fullName:        '',
  email:           '',
  password:        '',
  confirmPassword: '',
};

/**
 * @typedef {Object} UseRegistrationFormReturn
 * @property {object}   values        – controlled field values
 * @property {object}   errors        – per-field validation errors
 * @property {object}   touched       – tracks which fields have been blurred
 * @property {boolean}  isSubmitting  – true while the API call is in-flight
 * @property {string|null} apiError   – server-side error message
 * @property {function} handleChange  – onChange handler
 * @property {function} handleBlur    – onBlur handler
 * @property {function} handleSubmit  – form onSubmit handler
 * @property {function} isFieldValid  – returns true if a field has no error and was touched
 */
export function useRegistrationForm() {
  const navigate = useNavigate();
  const [values, setValues]       = useState(INITIAL_VALUES);
  const [errors, setErrors]       = useState(INITIAL_ERRORS);
  const [touched, setTouched]     = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError]   = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  /** Update a single field value and clear its error on change */
  const handleChange = useCallback((e) => {
    const { name, value } = e.target;
    setValues((prev) => {
      const updated = { ...prev, [name]: value };
      // Re-validate both password fields together so the confirmPassword
      // hint updates live when the user types in the password field.
      if (name === 'password' || name === 'confirmPassword') {
        setErrors((prevErr) => ({
          ...prevErr,
          [name]: touched[name]
            ? validateField(name, value, updated)
            : prevErr[name],
          // Keep confirmPassword in sync when password changes
          ...(name === 'password' && touched.confirmPassword
            ? { confirmPassword: validateField('confirmPassword', updated.confirmPassword, updated) }
            : {}),
        }));
      } else {
        setErrors((prevErr) => ({
          ...prevErr,
          [name]: touched[name] ? validateField(name, value, updated) : prevErr[name],
        }));
      }
      return updated;
    });
    setApiError(null);
    setSuccessMessage(null);
  }, [touched]);

  /** Mark field as touched and run validation on blur */
  const handleBlur = useCallback((e) => {
    const { name, value } = e.target;
    setTouched((prev) => ({ ...prev, [name]: true }));
    setErrors((prev) => ({
      ...prev,
      [name]: validateField(name, value, values),
    }));
  }, [values]);

  /**
   * Submit handler.
   * Currently prepares a clean payload ready for a FastAPI endpoint.
   * Replace the TODO block with your real `fetch`/`axios` call.
   */
  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();

    // Prevent duplicate in-flight submissions
    if (isSubmitting) return;

    // Touch all fields to show every error
    setTouched({ fullName: true, email: true, password: true, confirmPassword: true });

    const allErrors = validateAll(values);
    setErrors(allErrors);

    const hasErrors = Object.values(allErrors).some(Boolean);
    if (hasErrors) return;

    setIsSubmitting(true);
    setApiError(null);
    setSuccessMessage(null);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fullName: values.fullName.trim(),
          email: values.email.trim().toLowerCase(),
          password: values.password,
          confirmPassword: values.confirmPassword,
        }),
      });

      let data = {};
      try {
        data = await response.json();
      } catch {
        // Fallback if response body is not JSON
      }

      if (!response.ok) {
        const errorMsg = data.detail || (data.errors && data.errors[0]?.message) || 'Registration failed. Please check your details.';
        throw new Error(errorMsg);
      }

      const registeredEmail = data.data?.email || values.email.trim().toLowerCase();
      const userName = data.data?.full_name || 'you';
      
      setSuccessMessage(`Account created successfully for ${userName}! Redirecting to login…`);
      setValues(INITIAL_VALUES);
      setTouched({});
      setErrors(INITIAL_ERRORS);

      // Smooth transition to login page after 1.2s feedback
      setTimeout(() => {
        navigate('/login', {
          state: {
            registeredEmail: registeredEmail,
            message: `Account created successfully! Welcome aboard, ${userName}. Please sign in.`,
          },
        });
      }, 1200);
    } catch (err) {
      if (err.name === 'TypeError' && err.message.toLowerCase().includes('fetch')) {
        setApiError('Unable to connect to the backend server. Please verify the API is running.');
      } else {
        setApiError(err.message || 'Something went wrong. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [values, isSubmitting, navigate]);

  const isFieldValid = useCallback(
    (name) => touched[name] && !errors[name],
    [touched, errors],
  );

  return {
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
  };
}
