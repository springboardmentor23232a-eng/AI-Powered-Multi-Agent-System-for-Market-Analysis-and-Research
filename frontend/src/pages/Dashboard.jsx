import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  ScrollText,
  Shield,
  ShieldCheck,
  Users,
  UsersRound,
  Zap,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import api, { apiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import StatCard from '../components/StatCard.jsx'

const PIE_COLORS = ['#3b82f6', '#22d3ee', '#34d399', '#fbbf24', '#f87171', '#818cf8', '#94a3b8']

const ACTION_LABELS = {
  'auth.login': 'Sign-ins',
  'auth.logout': 'Sign-outs',
  'auth.password_change': 'Password changes',
  'user.create': 'User creation',
  'user.update': 'Profile updates',
  'user.activate': 'Activations',
  'user.deactivate': 'Deactivations',
  'user.roles_change': 'Role changes',
  'role.permissions_change': 'Permission changes',
  'team.create': 'Team creation',
  'team.update': 'Team updates',
  'team.delete': 'Team deletions',
  'team.member_add': 'Member additions',
  'team.member_remove': 'Member removals',
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/dashboard/stats')
      .then((r) => setStats(r.data))
      .catch((e) => setError(apiError(e, 'Failed to load dashboard data')))
  }, [])

  const scopeLabel =
    stats?.scope === 'all' ? 'Platform-wide overview' : stats?.scope === 'team' ? 'Your teams' : 'Your activity'

  const actionChart = (stats?.events_by_action ?? []).map((e) => ({
    name: ACTION_LABELS[e.action] ?? e.action,
    events: e.count,
  }))

  const roleChart = (stats?.role_distribution ?? [])
    .filter((r) => r.count > 0)
    .map((r) => ({ name: r.role.replace(/_/g, ' '), value: r.count }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-soc-text">Security Dashboard</h1>
          <p className="text-sm text-soc-muted mt-1">
            Welcome back, <span className="text-soc-text font-medium">{user?.full_name}</span> — {scopeLabel}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-soc-green bg-soc-green/10 border border-soc-green/30 rounded-full px-3.5 py-1.5">
          <span className="w-2 h-2 rounded-full bg-soc-green animate-pulse" />
          ALL SYSTEMS OPERATIONAL
        </div>
      </div>

      {error && (
        <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={stats?.total_users} icon={Users} tone="accent" sub="Registered accounts" />
        <StatCard label="Active Users" value={stats?.active_users} icon={ShieldCheck} tone="success" sub="Currently enabled" />
        <StatCard label="Security Teams" value={stats?.total_teams} icon={UsersRound} tone="muted" sub="Organized units" />
        <StatCard
          label="Events · 24h"
          value={stats?.events_24h}
          icon={Activity}
          tone="warning"
          sub={`${stats?.failures_24h ?? 0} failed`}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-soc-text">Security Events — Last 7 Days</h2>
            <span className="text-[11px] font-mono text-soc-muted">BY ACTION TYPE</span>
          </div>
          <div className="h-64">
            {actionChart.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={actionChart} layout="vertical" margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1c2942" horizontal={false} />
                  <XAxis type="number" stroke="#8b9bb8" fontSize={11} allowDecimals={false} />
                  <YAxis
                    type="category"
                    dataKey="name"
                    stroke="#8b9bb8"
                    fontSize={11}
                    width={130}
                    tick={{ fill: '#8b9bb8' }}
                  />
                  <Tooltip
                    contentStyle={{ background: '#0d1424', border: '1px solid #1c2942', borderRadius: 10, fontSize: 12 }}
                    labelStyle={{ color: '#e6edf7' }}
                  />
                  <Bar dataKey="events" fill="#3b82f6" radius={[0, 6, 6, 0]} barSize={18} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart text="No security events recorded in the last 7 days" />
            )}
          </div>
        </div>

        <div className="card p-5">
          <h2 className="text-sm font-semibold text-soc-text mb-4">Role Distribution</h2>
          <div className="h-64">
            {roleChart.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={roleChart}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={85}
                    paddingAngle={3}
                    strokeWidth={0}
                  >
                    {roleChart.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#0d1424', border: '1px solid #1c2942', borderRadius: 10, fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyChart text="No role data available" />
            )}
          </div>
          <div className="mt-2 space-y-1.5">
            {roleChart.map((r, i) => (
              <div key={r.name} className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-soc-muted">
                  <span className="w-2.5 h-2.5 rounded-sm" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }} />
                  {r.name}
                </span>
                <span className="font-mono text-soc-text">{r.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent activity */}
        <div className="xl:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-soc-text">Recent Security Activity</h2>
            <Link to="/audit-logs" className="text-xs text-soc-accentBright hover:underline inline-flex items-center gap-1">
              View all <ArrowRight size={12} />
            </Link>
          </div>
          {stats?.recent_activity?.length ? (
            <ul className="divide-y divide-soc-border">
              {stats.recent_activity.map((a) => (
                <li key={a.id} className="flex items-center gap-3 py-3 first:pt-0 last:pb-0">
                  <span
                    className={`w-2 h-2 rounded-full shrink-0 ${a.status === 'success' ? 'bg-soc-green' : 'bg-soc-danger'}`}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-soc-text truncate">
                      <span className="font-mono text-xs text-soc-accentBright">{a.action}</span>
                      {a.actor_username && <span className="text-soc-muted"> · {a.actor_username}</span>}
                    </div>
                    <div className="text-[11px] text-soc-muted">
                      {a.timestamp ? new Date(a.timestamp).toLocaleString() : ''}
                    </div>
                  </div>
                  <span
                    className={`badge ${a.status === 'success' ? 'bg-soc-green/10 text-soc-green border-soc-green/30' : 'bg-soc-danger/10 text-soc-danger border-soc-danger/30'}`}
                  >
                    {a.status}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-soc-muted py-6 text-center">No recent activity recorded.</p>
          )}
        </div>

        {/* Security posture */}
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-soc-text mb-4 flex items-center gap-2">
            <Shield size={16} className="text-soc-accentBright" /> Security Posture
          </h2>
          <div className="space-y-3">
            <PostureRow
              icon={ShieldCheck}
              label="Active sessions enforced"
              value="JWT + refresh rotation"
              tone="green"
            />
            <PostureRow
              icon={ScrollText}
              label="Audit coverage"
              value="All security events logged"
              tone="green"
            />
            <PostureRow
              icon={AlertTriangle}
              label="Failed events (24h)"
              value={stats?.failures_24h ?? 0}
              tone={(stats?.failures_24h ?? 0) > 0 ? 'warning' : 'green'}
            />
            <PostureRow
              icon={Zap}
              label="Access control"
              value="Role-based permissions"
              tone="green"
            />
          </div>
          {(stats?.failures_24h ?? 0) > 0 && (
            <div className="mt-4 flex items-start gap-2.5 text-xs text-soc-warning bg-soc-warning/10 border border-soc-warning/30 rounded-lg px-3 py-2.5">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              Failed events detected — review the audit log for details.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function PostureRow({ icon: Icon, label, value, tone }) {
  const tones = {
    green: 'text-soc-green',
    warning: 'text-soc-warning',
    danger: 'text-soc-danger',
  }
  return (
    <div className="flex items-center gap-3 bg-soc-bg border border-soc-border rounded-lg px-3.5 py-3">
      <Icon size={16} className={tones[tone] ?? tones.green} />
      <div className="min-w-0 flex-1">
        <div className="text-xs text-soc-muted">{label}</div>
        <div className="text-sm font-medium text-soc-text truncate">{value}</div>
      </div>
    </div>
  )
}

function EmptyChart({ text }) {
  return (
    <div className="h-full flex flex-col items-center justify-center text-soc-muted gap-2">
      <Activity size={28} className="opacity-40" />
      <p className="text-sm">{text}</p>
    </div>
  )
}
