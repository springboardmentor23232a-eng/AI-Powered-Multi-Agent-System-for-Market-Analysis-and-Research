import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Shield, ShieldAlert, UserPlus } from 'lucide-react'
import api, { apiError } from '../api/client'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const update = (field) => (event) =>
    setForm((current) => ({ ...current, [field]: event.target.value }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      await api.post('/auth/register', form)
      setSuccess('Registration successful. Your account is assigned the Security Analyst role.')
      window.setTimeout(() => navigate('/login', { replace: true }), 900)
    } catch (err) {
      setError(apiError(err, 'Registration failed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-soc-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-soc-accent/10 border border-soc-accent/40 mb-5">
            <Shield size={30} className="text-soc-accentBright" />
          </div>
          <h1 className="text-2xl font-bold text-soc-text">Create NetShield Account</h1>
          <p className="text-sm text-soc-muted mt-1.5">Public accounts receive Security Analyst access</p>
        </div>
        <form onSubmit={handleSubmit} className="card p-8 space-y-4">
          {[
            ['full_name', 'Full name', 'text'],
            ['username', 'Username', 'text'],
            ['email', 'Email', 'email'],
            ['password', 'Password', 'password'],
            ['confirm_password', 'Confirm password', 'password'],
          ].map(([field, label, type]) => (
            <div key={field}>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-soc-muted mb-1.5">
                {label}
              </label>
              <input
                type={type}
                value={form[field]}
                onChange={update(field)}
                required
                autoComplete={type === 'password' ? 'new-password' : field}
                className="input"
              />
            </div>
          ))}
          <div>
            <label className="block text-[11px] font-semibold uppercase tracking-wider text-soc-muted mb-1.5">
              Registration Role
            </label>
            <select className="input" value="security_analyst" disabled>
              <option value="security_analyst">Security Analyst</option>
            </select>
            <p className="text-[11px] text-soc-muted mt-1.5">
              Admin and Team Lead roles must be assigned by an authorized administrator.
            </p>
          </div>
          {error && (
            <div className="flex items-start gap-2 text-sm text-soc-danger bg-soc-danger/10 border border-soc-danger/30 rounded-lg px-3.5 py-3">
              <ShieldAlert size={16} className="shrink-0 mt-0.5" />
              {error}
            </div>
          )}
          {success && (
            <div className="text-sm text-soc-green bg-soc-green/10 border border-soc-green/30 rounded-lg px-3.5 py-3">
              {success}
            </div>
          )}
          <button type="submit" disabled={loading} className="btn-primary w-full">
            <UserPlus size={16} />
            {loading ? 'REGISTERING...' : 'REGISTER'}
          </button>
        </form>
        <p className="mt-6 text-center text-sm text-soc-muted">
          Already have an account? <Link to="/login" className="text-soc-accentBright hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
