
import { useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ChartNoAxesCombined,
  Eye,
  EyeOff,
  ShieldCheck,
  Activity,
  Check,
  X,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

import { useAuth } from '../context/AuthContext';
import GoogleSignIn from '../components/GoogleSignIn';

// ==================== AUTH FRAME ====================

function AuthFrame({ children, mode }) {
  return (
    <div className="auth-screen">
      <div className="auth-decoration decor-one" />
      <div className="auth-decoration decor-two" />

      <section className="auth-panel">
        <div className="auth-brand">
          <div className="brand-mark">
            <ChartNoAxesCombined size={22} />
          </div>

          <div>
            <b>EquityLens</b>
            <span>INTELLIGENCE FOR EVERY INVESTOR</span>
          </div>
        </div>

        <div className="auth-content">
          {children}
        </div>

        <div className="auth-foot">
          <ShieldCheck size={14} />
          Your account is protected with secure authentication
        </div>
      </section>

      <aside className="auth-aside">
        <div className="aside-orb orb-a" />
        <div className="aside-orb orb-b" />

        <div className="aside-content">
          <div className="eyebrow">
            <span />
            MARKET INTELLIGENCE PLATFORM
          </div>

          <h1>
            Research the market.
            <br />
            <em>Understand the signal.</em>
          </h1>

          <p>
            A focused workspace to organize stock research,
            track companies, and keep your market preferences close.
          </p>

          <div className="aside-stat-row">
            <div>
              <b>01</b>
              <span>One research space</span>
            </div>

            <div>
              <b>04</b>
              <span>Supported markets</span>
            </div>

            <div>
              <b>∞</b>
              <span>Ideas to investigate</span>
            </div>
          </div>

          <div className="floating-card">
            <div className="float-icon">
              <Activity size={17} />
            </div>

            <div>
              <b>Clarity over noise</b>
              <span>Keep every research task organized.</span>
            </div>

            <span className="float-check">✓</span>
          </div>
        </div>

        <div className="aside-bottom">
          MULTI-AGENT STOCK RESEARCH ANALYST
          <span>·</span>
          TASKS 01—06
        </div>
      </aside>
    </div>
  );
}

// ==================== LOGIN PAGE ====================

export function Login() {
  const { login, googleLogin } = useAuth();
  const nav = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);

    try {
      await login({ email, password });
      nav('/');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to sign in. Please try again.'
      );
    } finally {
      setBusy(false);
    }
  };

  const google = async (credential) => {
    setError('');

    try {
      await googleLogin(credential);
      nav('/');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Google sign-in failed.'
      );
    }
  };

  return (
    <AuthFrame mode="login">
      <div className="auth-heading">
        <div className="eyebrow">WELCOME BACK</div>

        <h2>
          Sign in to your
          <br />
          <span>research space.</span>
        </h2>

        <p>Pick up where your market research left off.</p>
      </div>

      {error && (
        <div className="alert error">
          {error}
        </div>
      )}

      <form onSubmit={submit} className="auth-form" method="post" action="#">
        <label htmlFor="login-email">
          Email address

          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="username"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>

        <label htmlFor="login-password">
          Password

          <div className="password-wrap">
            <input
              id="login-password"
              name="password"
              type={show ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button
              type="button"
              onClick={() => setShow(!show)}
              aria-label="Toggle password visibility"
            >
              {show ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </label>

        <button className="primary-btn" disabled={busy}>
          {busy ? 'Signing in…' : 'Sign in'}
          <ArrowRight size={17} />
        </button>
      </form>

      <div className="divider">
        <span />
        OR CONTINUE WITH
        <span />
      </div>

      <GoogleSignIn
        onCredential={google}
        onError={setError}
      />

      <div className="auth-switch">
        New to EquityLens?{' '}
        <Link to="/register">Create an account</Link>
      </div>
    </AuthFrame>
  );
}

// ==================== REGISTER PAGE ====================

export function Register() {
  const { register } = useAuth();
  const nav = useNavigate();

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: ''
  });

  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [showRequirements, setShowRequirements] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  // Six explicit password requirements
  const passwordCriteria = useMemo(() => [
    {
      id: 'min_length',
      label: 'Minimum 8 characters (15 recommended)',
      passed: form.password.length >= 8
    },
    {
      id: 'max_length',
      label: 'At most 128 characters',
      passed: form.password.length > 0 && form.password.length <= 128
    },
    {
      id: 'uppercase',
      label: 'At least one uppercase letter (A–Z)',
      passed: /[A-Z]/.test(form.password)
    },
    {
      id: 'lowercase',
      label: 'At least one lowercase letter (a–z)',
      passed: /[a-z]/.test(form.password)
    },
    {
      id: 'number',
      label: 'At least one number (0–9)',
      passed: /[0-9]/.test(form.password)
    },
    {
      id: 'special',
      label: 'At least one special character (@#$!%&*)',
      passed: /[@#$!%&*]/.test(form.password)
    }
  ], [form.password]);

  const passedCount = useMemo(
    () => passwordCriteria.filter((c) => c.passed).length,
    [passwordCriteria]
  );

  const passwordsMatch = form.password && form.confirm_password && form.password === form.confirm_password;
  const isPasswordValid = passedCount === 6;
  const isFormReady = isPasswordValid && passwordsMatch && form.full_name.trim().length >= 2 && form.email.includes('@');

  // Strength status formatting
  let strengthLabel = 'Enter password';
  let strengthColorClass = 'empty';
  let progressPct = (passedCount / 6) * 100;

  if (form.password.length > 0) {
    if (passedCount <= 2) {
      strengthLabel = 'Weak password';
      strengthColorClass = 'weak';
    } else if (passedCount <= 4) {
      strengthLabel = 'Improving password';
      strengthColorClass = 'improving';
    } else if (passedCount === 5) {
      strengthLabel = 'Almost valid';
      strengthColorClass = 'improving';
    } else {
      strengthLabel = form.password.length >= 15 ? 'Excellent & Secure' : 'Valid password';
      strengthColorClass = 'valid';
    }
  }

  const change = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');

    if (!isPasswordValid) {
      setError('Please fulfill all 6 password requirements before proceeding.');
      setShowRequirements(true);
      return;
    }

    if (!passwordsMatch) {
      setError('Your passwords do not match.');
      return;
    }

    setBusy(true);

    try {
      await register(form);
      nav('/');
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to create your account.'
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthFrame mode="register">
      <div className="auth-heading">
        <div className="eyebrow">GET STARTED</div>

        <h2>
          Create your
          <br />
          <span>research account.</span>
        </h2>

        <p>Your market workspace starts with a few details.</p>
      </div>

      {error && (
        <div className="alert error">
          {error}
        </div>
      )}

      <form onSubmit={submit} className="auth-form" method="post" action="#">
        <label htmlFor="register-name">
          Full name

          <input
            id="register-name"
            name="full_name"
            type="text"
            autoComplete="name"
            placeholder="Your full name"
            value={form.full_name}
            onChange={change}
            minLength="2"
            maxLength="120"
            required
          />
        </label>

        <label htmlFor="register-email">
          Email address

          <input
            id="register-email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={change}
            required
          />
        </label>

        <label htmlFor="register-password">
          Password

          <div className="password-wrap">
            <input
              id="register-password"
              name="password"
              type={showPass ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Enter secure password"
              value={form.password}
              onChange={change}
              onFocus={() => setShowRequirements(true)}
              maxLength="128"
              required
            />

            <button
              type="button"
              onClick={() => setShowPass(!showPass)}
              aria-label="Toggle password visibility"
            >
              {showPass ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </label>

        {/* Live Password Strength Bar */}
        <div
          className="password-strength-container cursor-pointer"
          onClick={() => setShowRequirements(!showRequirements)}
          title="Click to view password requirements"
        >
          <div className="strength-header">
            <span className="strength-caption">Password strength:</span>
            <span className={`strength-badge ${strengthColorClass}`}>{strengthLabel}</span>
            <span className="strength-toggle-icon">
              {showRequirements ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </span>
          </div>

          <div className="strength-bar-track">
            <div
              className={`strength-bar-fill ${strengthColorClass}`}
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* Expandable Password Requirements Panel */}
        {showRequirements && (
          <div className="password-requirements-panel">
            <div className="requirements-title">
              <Info size={14} /> Requirements checklist ({passedCount}/6):
            </div>
            <ul className="requirements-list">
              {passwordCriteria.map((crit) => (
                <li
                  key={crit.id}
                  className={`requirement-item ${crit.passed ? 'passed' : 'missing'}`}
                >
                  {crit.passed ? (
                    <Check size={14} className="check-icon" />
                  ) : (
                    <span className="missing-bullet">○</span>
                  )}
                  <span>{crit.label}</span>
                </li>
              ))}
            </ul>

            {isPasswordValid && (
              <div className="requirement-success-banner">
                <Check size={14} /> All password criteria met!
              </div>
            )}
          </div>
        )}

        <label htmlFor="register-confirm-password">
          Confirm password

          <div className="password-wrap">
            <input
              id="register-confirm-password"
              name="confirm_password"
              type={showConfirm ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="Enter password again"
              value={form.confirm_password}
              onChange={change}
              maxLength="128"
              required
            />

            <button
              type="button"
              onClick={() => setShowConfirm(!showConfirm)}
              aria-label="Toggle confirm password visibility"
            >
              {showConfirm ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
          {form.confirm_password && (
            <div className={`match-hint ${passwordsMatch ? 'match' : 'mismatch'}`}>
              {passwordsMatch ? '✓ Passwords match' : '✕ Passwords do not match'}
            </div>
          )}
        </label>

        <button className="primary-btn" disabled={busy || !isFormReady}>
          {busy ? 'Creating account…' : 'Create account'}
          <ArrowRight size={17} />
        </button>
      </form>

      <div className="auth-switch">
        Already have an account?{' '}
        <Link to="/login">Sign in</Link>
      </div>
    </AuthFrame>
  );
}
