import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Fingerprint, Lock, Shield, ShieldAlert, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import api, { apiError } from '../api/client'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(identifier.trim(), password)
      navigate('/', { replace: true })
    } catch (err) {
      if (err.response?.status === 429) {
        setError('Too many sign-in attempts. Please wait a few minutes and try again.')
      } else {
        setError(apiError(err, 'Sign-in failed. Please check your credentials.'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4 relative overflow-hidden">
      {/* subtle grid backdrop */}
      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage:
            'linear-gradient(#3b82f6 1px, transparent 1px), linear-gradient(90deg, #3b82f6 1px, transparent 1px)',
          backgroundSize: '44px 44px',
        }}
      />
      {/* ambient glow */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-soc-accent/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-md relative">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-soc-accent/10 border border-soc-accent/40 mb-5 shadow-glow">
            <Shield size={30} className="text-soc-accentBright" />
          </div>
          <h1 className="text-2xl font-bold text-soc-text tracking-wide">NetShield AI</h1>
          <p className="text-sm text-soc-muted mt-1.5">
            AI-powered network anomaly detection &amp; intrusion monitoring
          </p>
        </div>

        <form onSubmit={handleSubmit} className="card p-8 shadow-2xl">
          <div className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-soc-muted mb-1.5">
                Username or Email
              </label>
              <div className="relative">
                <User size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-soc-muted" />
                <input
                  type="text"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                  autoComplete="username"
                  className="input pl-10"
                  placeholder="e.g. analyst01"
                />
              </div>
            </div>
            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-soc-muted mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-soc-muted" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoComplete="current-password"
                  className="input pl-10"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 flex items-start gap-2.5 text-sm text-soc-danger bg-soc-danger/10 border border-soc-danger/30 rounded-lg px-3.5 py-3">
              <ShieldAlert size={16} className="shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary w-full mt-6 py-3">
            {loading ? (
              <>
                <Fingerprint size={16} className="animate-pulse" />
                AUTHENTICATING…
              </>
            ) : (
              'SIGN IN SECURELY'
            )}
          </button>
        </form>

        <div className="mt-6 flex items-center justify-center gap-2 text-[11px] font-mono text-soc-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-soc-green" />
          ENCRYPTED SESSION • ALL ACTIVITY IS AUDITED
        </div>
      </div>
    </div>
  )
}
