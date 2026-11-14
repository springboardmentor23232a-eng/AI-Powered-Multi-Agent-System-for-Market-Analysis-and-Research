import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, Check, Circle, Eye, EyeOff } from 'lucide-react'
import { api } from '../api.js'
import { useAuth } from '../auth.jsx'
import Mark from '../components/Mark.jsx'
import PriceLine from '../components/PriceLine.jsx'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function Field({ id, label, type = 'text', value, onChange, placeholder, autoComplete }) {
  const [show, setShow] = useState(false)
  const isPw = type === 'password'
  return (
    <div>
      <label htmlFor={id} className="label">{label}</label>
      <div className="relative">
        <input id={id} className={'field ' + (isPw ? 'pr-11' : '')} type={isPw && show ? 'text' : type}
          value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} autoComplete={autoComplete} />
        {isPw && (
          <button type="button" onClick={() => setShow(!show)} aria-label={show ? 'Hide password' : 'Show password'}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-mute hover:text-ink">
            {show ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        )}
      </div>
    </div>
  )
}

function Rule({ ok, children }) {
  return (
    <li className={'flex items-center gap-2 text-sm ' + (ok ? 'text-gain' : 'text-mute')}>
      {ok ? <Check size={15} /> : <Circle size={15} />} {children}
    </li>
  )
}

export default function AuthPage({ mode }) {
  const isLogin = mode === 'login'
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }))

  const lenOk = form.password.length >= 8
  const mixOk = /[A-Za-z]/.test(form.password) && /\d/.test(form.password)
  const matchOk = form.confirm_password !== '' && form.password === form.confirm_password

  async function submit(e) {
    e.preventDefault()
    setError('')
    if (!EMAIL_RE.test(form.email)) return setError('Enter a valid email address.')
    if (isLogin) {
      if (!form.password) return setError('Enter your password.')
    } else {
      if (form.full_name.trim().length < 2) return setError('Enter your full name.')
      if (!lenOk || !mixOk) return setError('Your password needs at least 8 characters, including a letter and a number.')
      if (!matchOk) return setError('The two passwords do not match.')
    }
    setBusy(true)
    try {
      if (isLogin) await login({ email: form.email, password: form.password })
      else {
        await api.register(form)
        navigate('/login', { state: { registered: true } })
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[5fr_6fr]">
      <aside className="on-cobalt grid-paper relative hidden flex-col gap-20 overflow-hidden bg-cobalt p-10 text-white lg:flex">
        <PriceLine />
        <div className="relative z-10"><Mark light /></div>
        <h2 className="relative z-10 max-w-md text-5xl font-extrabold leading-[1.02] tracking-[-0.03em]">
          {isLogin ? 'Pick up where you left off.' : 'Save the stocks you follow and every research you run.'}
        </h2>
      </aside>

      <main className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden"><Mark /></div>
          <h1 className="text-4xl font-semibold tracking-tight">{isLogin ? 'Login' : 'Create your account'}</h1>
          <p className="mt-2 text-mute">
            {isLogin ? 'Enter your email and password to open your workspace.' : 'It takes under a minute.'}
          </p>

          {location.state?.registered && isLogin && (
            <p role="status" className="mt-6 border-l-4 border-gain bg-gain/10 px-4 py-3 text-sm font-medium text-gain">
              Account created successfully. You can now log in.
            </p>
          )}

          <form onSubmit={submit} className="mt-8 space-y-5" noValidate>
            {!isLogin && <Field id="name" label="Full name" value={form.full_name} onChange={set('full_name')} autoComplete="name" />}
            <Field id="email" label="Email address" type="email" value={form.email} onChange={set('email')} autoComplete="email" />
            <Field id="password" label="Password" type="password" value={form.password} onChange={set('password')} autoComplete={isLogin ? 'current-password' : 'new-password'} />
            {!isLogin && (
              <>
                <Field id="confirm" label="Confirm password" type="password" value={form.confirm_password} onChange={set('confirm_password')} autoComplete="new-password" />
                <ul className="space-y-1.5" aria-label="Password requirements">
                  <Rule ok={lenOk}>At least 8 characters</Rule>
                  <Rule ok={mixOk}>Contains a letter and a number</Rule>
                  <Rule ok={matchOk}>Both passwords match</Rule>
                </ul>
              </>
            )}

            {error && (
              <p role="alert" className="flex items-start gap-2.5 border-l-4 border-loss bg-loss/10 px-4 py-3 text-sm font-medium text-loss">
                <AlertCircle size={18} className="mt-px shrink-0" /> {error}
              </p>
            )}

            <button className="btn-cobalt w-full !py-3" disabled={busy}>
              {busy ? 'Please wait…' : isLogin ? 'Login' : 'Create account'}
            </button>
          </form>

          <p className="mt-7 text-sm text-mute">
            {isLogin ? 'New here? ' : 'Already have an account? '}
            <Link to={isLogin ? '/register' : '/login'} className="font-semibold text-cobalt underline underline-offset-4">
              {isLogin ? 'Create an account' : 'Login'}
            </Link>
          </p>
        </div>
      </main>
    </div>
  )
}
