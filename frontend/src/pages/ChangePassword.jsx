import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { KeyRound } from 'lucide-react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Field, ModalActions } from './Users.jsx'

export default function ChangePassword() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setNotice('')
    if (form.new_password.length < 8) {
      setError('New password must be at least 8 characters.')
      return
    }
    if (form.new_password !== form.confirm) {
      setError('New passwords do not match.')
      return
    }
    setSaving(true)
    try {
      const { data } = await api.post('/auth/me/password', {
        current_password: form.current_password,
        new_password: form.new_password,
      })
      setNotice(`${data.message} Redirecting to login...`)
      setTimeout(async () => {
        await logout()
        navigate('/login')
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Password change failed')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold text-slate-100 mb-1">Change Password</h1>
      <p className="text-sm text-soc-muted mb-6">All active sessions will be signed out after the change.</p>

      <form onSubmit={submit} className="bg-soc-panel border border-soc-border rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-soc-warning text-sm mb-2">
          <KeyRound size={16} /> Password must be at least 8 characters
        </div>
        <Field label="Current Password" type="password" value={form.current_password} onChange={(v) => setForm({ ...form, current_password: v })} required />
        <Field label="New Password" type="password" value={form.new_password} onChange={(v) => setForm({ ...form, new_password: v })} required />
        <Field label="Confirm New Password" type="password" value={form.confirm} onChange={(v) => setForm({ ...form, confirm: v })} required />

        {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-3 py-2.5 text-sm">{error}</div>}
        {notice && <div className="bg-soc-green/10 border border-soc-green/30 text-soc-green rounded-lg px-3 py-2.5 text-sm">{notice}</div>}

        <ModalActions saving={saving} onClose={() => navigate('/profile')} submitLabel="Change Password" />
      </form>
    </div>
  )
}
