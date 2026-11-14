import { useEffect, useState } from 'react'
import { KeyRound, User } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, refreshMe } = useAuth()
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/auth/me')
      .then((r) => setProfile(r.data))
      .catch((e) => setError(e.response?.data?.detail || 'Failed to load profile'))
  }, [])

  const p = profile ?? user

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">My Profile</h1>
        <p className="text-sm text-soc-muted">Account information and security</p>
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}

      <div className="bg-soc-panel border border-soc-border rounded-xl p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-full bg-soc-accent/15 border border-soc-accent/40 flex items-center justify-center text-soc-accent text-xl font-bold">
            {p?.username?.[0]?.toUpperCase()}
          </div>
          <div>
            <div className="text-lg font-semibold text-slate-100">{p?.full_name}</div>
            <div className="text-sm text-soc-muted font-mono">@{p?.username}</div>
          </div>
        </div>

        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div className="bg-soc-bg border border-soc-border rounded-lg p-4">
            <dt className="text-xs uppercase tracking-wider text-soc-muted mb-1">Email</dt>
            <dd className="text-slate-200">{p?.email}</dd>
          </div>
          <div className="bg-soc-bg border border-soc-border rounded-lg p-4">
            <dt className="text-xs uppercase tracking-wider text-soc-muted mb-1">Status</dt>
            <dd className="text-soc-green capitalize">{p?.status}</dd>
          </div>
          <div className="bg-soc-bg border border-soc-border rounded-lg p-4 sm:col-span-2">
            <dt className="text-xs uppercase tracking-wider text-soc-muted mb-1">Roles</dt>
            <dd className="flex flex-wrap gap-2">
              {(p?.roles ?? []).map((r) => (
                <span key={r} className="text-xs px-2.5 py-1 rounded-full bg-soc-accentBright/15 text-soc-accentBright border border-soc-accentBright/30">
                  {r.replace(/_/g, ' ')}
                </span>
              ))}
            </dd>
          </div>
          <div className="bg-soc-bg border border-soc-border rounded-lg p-4 sm:col-span-2">
            <dt className="text-xs uppercase tracking-wider text-soc-muted mb-1">Permissions</dt>
            <dd className="flex flex-wrap gap-1.5">
              {(p?.permissions ?? []).map((perm) => (
                <span key={perm} className="text-[11px] font-mono px-2 py-0.5 rounded bg-soc-panel2 border border-soc-border text-soc-muted">
                  {perm}
                </span>
              ))}
              {(p?.roles ?? []).includes('administrator') && (
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-soc-accent/15 border border-soc-accent/40 text-soc-accent">
                  * administrator — all permissions
                </span>
              )}
            </dd>
          </div>
        </dl>
      </div>

      <Link
        to="/change-password"
        className="flex items-center gap-3 bg-soc-panel border border-soc-border rounded-xl p-5 hover:border-soc-accent/50 transition-colors"
      >
        <KeyRound className="text-soc-warning" size={22} />
        <div>
          <div className="font-semibold text-slate-100">Change Password</div>
          <div className="text-xs text-soc-muted">Update your password — all existing sessions will be revoked</div>
        </div>
      </Link>
    </div>
  )
}
