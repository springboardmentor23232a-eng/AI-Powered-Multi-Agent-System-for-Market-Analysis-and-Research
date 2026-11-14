
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ChartNoAxesCombined,
  Eye,
  EyeOff,
  ShieldCheck,
  Activity
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

      <form onSubmit={submit} className="auth-form">
        <label>
          Email address

          <input
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>

        <label>
          Password

          <div className="password-wrap">
            <input
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

  const [show, setShow] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const change = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirm_password) {
      setError('Your passwords do not match.');
      return;
    }

    if (!/(?=.*[A-Za-z])(?=.*\d).{8,}/.test(form.password)) {
      setError(
        'Use at least 8 characters, including a letter and a number.'
      );
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

      <form onSubmit={submit} className="auth-form">
        <label>
          Full name

          <input
            name="full_name"
            placeholder="Your full name"
            value={form.full_name}
            onChange={change}
            minLength="2"
            required
          />
        </label>

        <label>
          Email address

          <input
            name="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={change}
            required
          />
        </label>

        <label>
          Password

          <div className="password-wrap">
            <input
              name="password"
              type={show ? 'text' : 'password'}
              autoComplete="new-password"
              placeholder="At least 8 characters"
              value={form.password}
              onChange={change}
              required
            />

            <button
              type="button"
              onClick={() => setShow(!show)}
            >
              {show ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </label>

        <label>
          Confirm password

          <input
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            placeholder="Enter password again"
            value={form.confirm_password}
            onChange={change}
            required
          />
        </label>

        <button className="primary-btn" disabled={busy}>
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
