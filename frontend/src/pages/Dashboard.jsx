import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  HardDrive,
  Network,
  Radio,
  RefreshCw,
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
const SEVERITY_BADGE = {
  informational: 'border-soc-cyan/30 bg-soc-cyan/10 text-soc-cyan',
  low: 'border-soc-green/30 bg-soc-green/10 text-soc-green',
  medium: 'border-soc-warning/30 bg-soc-warning/10 text-soc-warning',
  high: 'border-soc-danger/30 bg-soc-danger/10 text-soc-danger',
}

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
  const [networkSummary, setNetworkSummary] = useState(null)
  const [networkLoading, setNetworkLoading] = useState(true)
  const [networkError, setNetworkError] = useState('')
  const [alertSummary, setAlertSummary] = useState(null)

  useEffect(() => {
    api
      .get('/dashboard/stats')
      .then((r) => setStats(r.data))
      .catch((e) => setError(apiError(e, 'Failed to load dashboard data')))
  }, [])

  const loadNetworkSummary = useCallback(async (signal) => {
    setNetworkLoading(true)
    setNetworkError('')
    try {
      const { data } = await api.get('/network/summary', { signal })
      setNetworkSummary(data)
    } catch (e) {
      if (e.code !== 'ERR_CANCELED') {
        setNetworkError(apiError(e, 'Failed to load network traffic data'))
      }
    } finally {
      if (!signal?.aborted) setNetworkLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    loadNetworkSummary(controller.signal)
    return () => controller.abort()
  }, [loadNetworkSummary])

  useEffect(() => {
    api
      .get('/network/alerts/summary')
      .then((r) => setAlertSummary(r.data))
      .catch(() => setAlertSummary(null))
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
          SECURITY SESSION ACTIVE
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
      {alertSummary && (
        <div className="card p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <h2 className="text-sm font-semibold text-soc-text flex items-center gap-2">
              <AlertTriangle size={16} className="text-soc-warning" /> Network Alerts
            </h2>
            <Link to="/alerts" className="text-xs text-soc-accentBright hover:underline inline-flex items-center gap-1">
              View alerts <ArrowRight size={12} />
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard label="Total Alerts" value={alertSummary.total} icon={AlertTriangle} tone="warning" sub="Stored database alerts" />
            <StatCard label="Open" value={alertSummary.by_status?.open ?? 0} icon={AlertTriangle} tone="danger" sub="Awaiting response" />
            <StatCard label="Medium" value={alertSummary.by_severity?.medium ?? 0} icon={Zap} tone="warning" sub="Heuristic severity" />
            <StatCard label="Resolved" value={alertSummary.by_status?.resolved ?? 0} icon={ShieldCheck} tone="success" sub="Closed alerts" />
          </div>
          {alertSummary.recent?.length ? (
            <ul className="mt-4 divide-y divide-soc-border">
              {alertSummary.recent.map((alert) => (
                <li key={alert.id} className="flex flex-wrap items-center gap-3 py-3 first:pt-0 last:pb-0">
                  <span className={`badge border ${SEVERITY_BADGE[alert.severity]}`}>{alert.severity}</span>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm text-soc-text">{alert.rule_name}</div>
                    <div className="text-xs text-soc-muted">
                      {alert.source_ip || 'Source unavailable'} · {alert.capture_source === 'live_capture' ? 'Live capture' : 'Historical import'}
                    </div>
                  </div>
                  <span className="text-xs text-soc-muted">
                    {alert.detected_at ? new Date(alert.detected_at).toLocaleString() : 'Unavailable'}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-4 text-sm text-soc-muted text-center">No network alerts recorded.</p>
          )}
        </div>
      )}
      <NetworkTrafficSection
        summary={networkSummary}
        loading={networkLoading}
        error={networkError}
        onRetry={() => loadNetworkSummary()}
      />
    </div>
  )
}

function NetworkTrafficSection({ summary, loading, error, onRetry }) {
  const protocols = (summary?.protocols ?? []).map((item) => ({
    name: item.protocol || 'Unknown',
    packets: Number(item.packet_count) || 0,
  }))
  const recentPackets = summary?.recent_packets ?? []

  return (
    <section className="space-y-4" aria-labelledby="network-traffic-heading">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Network size={18} className="text-soc-cyan" />
            <h2 id="network-traffic-heading" className="text-lg font-semibold text-soc-text">
              Network Traffic Monitoring
            </h2>
          </div>
          <p className="mt-1 text-sm text-soc-muted">
            Summary of imported historical packet data
          </p>
        </div>
        {!loading && (
          <button type="button" onClick={onRetry} className="btn-ghost px-3 py-2 text-xs">
            <RefreshCw size={13} />
            Refresh
          </button>
        )}
      </div>

      {error ? (
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-soc-danger/30 bg-soc-danger/10 px-4 py-3 text-sm text-soc-danger"
        >
          <span>{error}</span>
          <button type="button" onClick={onRetry} className="btn-ghost border-soc-danger/30 px-3 py-2 text-xs text-soc-danger">
            <RefreshCw size={13} />
            Try again
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <StatCard
              label="Total Packets"
              value={loading ? '…' : formatCount(summary?.total_packets)}
              icon={Radio}
              tone="accent"
              sub="Imported historical packets"
            />
            <StatCard
              label="Data Transferred"
              value={loading ? '…' : formatBytes(summary?.total_bytes)}
              icon={HardDrive}
              tone="success"
              sub="Combined packet size"
            />
          </div>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="card p-5 xl:col-span-3">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-soc-text">Packets by Protocol</h3>
                <span className="text-[11px] font-mono text-soc-muted">PACKET COUNTS</span>
              </div>
              <div className="h-64">
                {loading ? (
                  <LoadingMessage text="Loading protocol data…" />
                ) : protocols.length ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={protocols} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1c2942" horizontal={false} />
                      <XAxis type="number" stroke="#8b9bb8" fontSize={11} allowDecimals={false} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        stroke="#8b9bb8"
                        fontSize={11}
                        width={90}
                        tick={{ fill: '#8b9bb8' }}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#0d1424',
                          border: '1px solid #1c2942',
                          borderRadius: 10,
                          fontSize: 12,
                        }}
                        labelStyle={{ color: '#e6edf7' }}
                      />
                      <Bar dataKey="packets" name="Packets" fill="#22d3ee" radius={[0, 6, 6, 0]} barSize={18} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyChart text="No protocol data available" />
                )}
              </div>
            </div>

          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="card p-5">
              <h3 className="mb-4 text-sm font-semibold text-soc-text">Top Source IPs</h3>
              {loading ? (
                <LoadingMessage text="Loading source IPs…" />
              ) : (
                <TrafficEndpointList data={summary?.top_sources ?? []} addressKey="source_ip" />
              )}
            </div>
            <div className="card p-5">
              <h3 className="mb-4 text-sm font-semibold text-soc-text">Top Destination IPs</h3>
              {loading ? (
                <LoadingMessage text="Loading destination IPs…" />
              ) : (
                <TrafficEndpointList data={summary?.top_destinations ?? []} addressKey="destination_ip" />
              )}
            </div>
          </div>

          <div className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-soc-border px-5 py-4">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-soc-cyan" />
                <h3 className="text-sm font-semibold text-soc-text">Recent Packet Activity</h3>
              </div>
              <span className="text-[11px] font-mono text-soc-muted">LATEST IMPORTED</span>
            </div>
            {loading ? (
              <div className="p-5">
                <LoadingMessage text="Loading recent packets…" />
              </div>
            ) : recentPackets.length ? (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[760px]">
                  <thead className="border-b border-soc-border bg-soc-bg/50">
                    <tr>
                      <th className="th">Time</th>
                      <th className="th">Source</th>
                      <th className="th">Destination</th>
                      <th className="th">Protocol</th>
                      <th className="th text-right">Size</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-soc-border">
                    {recentPackets.map((packet) => (
                      <tr key={packet.id} className="hover:bg-soc-panel2/50">
                        <td className="td whitespace-nowrap text-xs text-soc-muted">
                          {formatTimestamp(packet.packet_timestamp)}
                        </td>
                        <td className="td font-mono text-xs">
                          {formatEndpoint(packet.source_ip, packet.source_port)}
                        </td>
                        <td className="td font-mono text-xs">
                          {formatEndpoint(packet.destination_ip, packet.destination_port)}
                        </td>
                        <td className="td">
                          <span className="badge border-soc-cyan/30 bg-soc-cyan/10 text-soc-cyan">
                            {packet.protocol || 'Unknown'}
                          </span>
                        </td>
                        <td className="td text-right font-mono text-xs">{formatBytes(packet.packet_size)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-soc-muted">No packet activity recorded.</p>
            )}
          </div>
        </>
      )}
    </section>
  )
}

function TrafficEndpointList({ data, addressKey }) {
  if (!data.length) {
    return <p className="py-6 text-center text-sm text-soc-muted">No IP activity available.</p>
  }

  const maxCount = Math.max(...data.map((item) => Number(item.packet_count) || 0), 1)

  return (
    <ul className="space-y-4">
      {data.map((item) => {
        const count = Number(item.packet_count) || 0
        return (
          <li key={item[addressKey]} className="space-y-1.5">
            <div className="flex items-center justify-between gap-3 text-xs">
              <span className="truncate font-mono text-soc-text">{item[addressKey] || 'Unknown'}</span>
              <span className="shrink-0 font-mono text-soc-muted">{formatCount(count)}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-soc-bg">
              <div
                className="h-full rounded-full bg-soc-cyan"
                style={{ width: `${Math.min((count / maxCount) * 100, 100)}%` }}
              />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function LoadingMessage({ text }) {
  return (
    <div className="flex h-full min-h-24 items-center justify-center gap-2 text-sm text-soc-muted" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-soc-border border-t-soc-cyan" />
      {text}
    </div>
  )
}

function formatCount(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—'
  return new Intl.NumberFormat().format(Number(value))
}

function formatBytes(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return '—'
  const bytes = Number(value)
  if (bytes < 1024) return `${formatCount(bytes)} B`
  const units = ['KB', 'MB', 'GB', 'TB']
  const unitIndex = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)) - 1, units.length - 1)
  return `${(bytes / 1024 ** (unitIndex + 1)).toFixed(1)} ${units[unitIndex]}`
}

function formatEndpoint(address, port) {
  if (!address) return '—'
  return port === null || port === undefined ? address : `${address}:${port}`
}

function formatTimestamp(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString()
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
