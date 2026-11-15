import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { Alert, Button, Field, inputClass } from '../components/ui'

const MIN_PASSWORD_LENGTH = 8

// Mirrors the backend rules so users get instant feedback; the backend still checks everything.
function validateRegistration(password, confirmPassword) {
  if (password.length < MIN_PASSWORD_LENGTH) return `Password must be at least ${MIN_PASSWORD_LENGTH} characters`
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password))
    return 'Password must contain at least one letter and one number'
  if (password !== confirmPassword) return 'Passwords do not match'
  return null
}

// One component for both screens: mode is "login" or "register".
export default function AuthPage({ mode }) {
  const isRegister = mode === 'register'
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    if (isRegister) {
      const problem = validateRegistration(password, confirmPassword)
      if (problem) return setError(problem)
    }
    setSubmitting(true)
    try {
      await (isRegister ? register(email, password) : login(email, password))
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-semibold">{isRegister ? 'Create your account' : 'Sign in'}</h1>
        <p className="mt-1 text-sm text-slate-500">Multi-Agent Stock Research Analyst</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          <Field label="Email" id="email">
            <input id="email" type="email" autoComplete="email" required className={inputClass}
              value={email} onChange={(e) => setEmail(e.target.value)} />
          </Field>
          <Field label="Password" id="password">
            <input id="password" type="password" required className={inputClass}
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              value={password} onChange={(e) => setPassword(e.target.value)} />
          </Field>
          {isRegister && (
            <Field label="Confirm password" id="confirm-password">
              <input id="confirm-password" type="password" autoComplete="new-password" required
                className={inputClass} value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)} />
            </Field>
          )}
          {isRegister && (
            <p className="text-xs text-slate-500">
              At least {MIN_PASSWORD_LENGTH} characters, with at least one letter and one number.
            </p>
          )}

          <Alert>{error}</Alert>

          <Button type="submit" className="w-full" disabled={submitting || !email || !password}>
            {submitting ? 'Please wait…' : isRegister ? 'Create account' : 'Sign in'}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          {isRegister ? 'Already have an account? ' : 'New here? '}
          <Link to={isRegister ? '/login' : '/register'} className="font-medium text-indigo-600 hover:underline">
            {isRegister ? 'Sign in' : 'Create an account'}
          </Link>
        </p>
      </div>
    </main>
  )
}
