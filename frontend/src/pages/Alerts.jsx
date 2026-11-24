import { useCallback, useEffect, useState } from 'react'
import { CheckCircle2, Siren, XCircle } from 'lucide-react'
import api, { apiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import DataTable from '../components/DataTable.jsx'

const SEVERITY_BADGE = {
  informational: 'bg-soc-cyan/10 text-soc-cyan border-soc-cyan/30',
  low: 'bg-soc-green/10 text-soc-green border-soc-green/30',
  medium: 'bg-soc-warning/10 text-soc-warning border-soc-warning/30',
  high: 'bg-soc-danger/10 text-soc-danger border-soc-danger/30',
}

const STATUS_BADGE = {
  open: 'bg-soc-warning/10 text-soc-warning border-soc-warning/30',
  acknowledged: 'bg-soc-cyan/10 text-soc-cyan border-soc-cyan/30',
  resolved: 'bg-soc-green/10 text-soc-green border-soc-green/30',
}

export default function Alerts() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('alerts.manage')
  const [summary, setSummary] = useState(null)
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [filters, setFilters] = useState({
    severity: '',
    status: '',
    rule_name: '',
    capture_source: '',
  })

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: 25 }
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params[key] = value
      })
      const [summaryRes, alertsRes] = await Promise.all([
        api.get('/network/alerts/summary'),
        api.get('/network/alerts', { params }),
      ])
      setSummary(summaryRes.data)
      setRows(alertsRes.data.items)
      setTotal(alertsRes.data.total)
    } catch (err) {
      setError(apiError(err, 'Failed to load network alerts'))
    } finally {
      setLoading(false)
    }
  }, [page, filters])

  useEffect(() => {
    load()
  }, [load])

  const updateAlert = async (alert, action) => {
    setError('')
    setNotice('')
    try {
      await api.post(`/network/alerts/${alert.id}/${action}`)
      setNotice(`Alert ${action === 'acknowledge' ? 'acknowledged' : 'resolved'}.`)
      load()
    } catch (err) {
      setError(apiError(err, `Failed to ${action} alert`))
    }
  }

  const evaluate = async (captureSource) => {
    setError('')
    setNotice('')
    try {
      const { data } = await api.post('/network/alerts/evaluate', null, {
        params: { capture_source: captureSource },
      })
      setNotice(`${data.created_count} new alert(s) created by deterministic rules.`)
      load()
    } catch (err) {
      setError(apiError(err, 'Failed to evaluate packet data'))
    }
  }

  const columns = [
    {
      key: 'rule_name',
      label: 'Rule',
      render: (row) => (
        <div>
          <div className="font-semibold text-soc-text">{row.rule_name}</div>
          <div className="text-[11px] text-soc-muted">
            {row.capture_source === 'live_capture' ? 'Live capture' : 'Historical import'}
          </div>
        </div>
      ),
    },
    {
      key: 'severity',
      label: 'Severity',
      render: (row) => (
        <span className={`text-xs px-2 py-0.5 rounded-full border ${SEVERITY_BADGE[row.severity]}`}>
          {row.severity}
        </span>
      ),
    },
    {
      key: 'source_ip',
      label: 'Source',
      render: (row) => <span className="font-mono text-xs">{row.source_ip || 'Unavailable'}</span>,
    },
    {
      key: 'destination_ip',
      label: 'Destination',
      render: (row) => <span className="font-mono text-xs">{row.destination_ip || 'Unavailable'}</span>,
    },
    {
      key: 'detected_at',
      label: 'Detected',
      render: (row) => (
        <span className="text-xs text-soc-muted">
          {row.detected_at ? new Date(row.detected_at).toLocaleString() : 'Unavailable'}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (row) => (
        <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_BADGE[row.status]}`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (row) =>
        canManage ? (
          <div className="flex gap-1">
            {row.status === 'open' && (
              <button
                title="Acknowledge"
                onClick={(event) => {
                  event.stopPropagation()
                  updateAlert(row, 'acknowledge')
                }}
                className="p-1.5 rounded hover:bg-soc-panel2 text-soc-cyan"
              >
                <CheckCircle2 size={15} />
              </button>
            )}
            {row.status !== 'resolved' && (
              <button
                title="Resolve"
                onClick={(event) => {
                  event.stopPropagation()
                  updateAlert(row, 'resolve')
                }}
                className="p-1.5 rounded hover:bg-soc-panel2 text-soc-green"
              >
                <XCircle size={15} />
              </button>
            )}
          </div>
        ) : null,
    },
    {
      key: 'explanation',
      label: 'Explanation',
      render: (row) => (
        <div className="max-w-md text-xs text-soc-muted">
          {row.explanation}
          <div className="mt-1 font-mono">
            Observed {row.observed_count} · Threshold {row.threshold_value} · Window {row.window_seconds}s
          </div>
        </div>
      ),
    },
  ]

  const totalPages = Math.max(1, Math.ceil(total / 25))

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Siren className="text-soc-warning" size={24} /> Network Alerts
          </h1>
          <p className="text-sm text-soc-muted">
            Deterministic heuristic alerts — these signals are not confirmed attacks
          </p>
        </div>
        {canManage && (
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={() => evaluate('live_capture')}>
              Evaluate Live
            </button>
            <button className="btn-ghost" onClick={() => evaluate('historical_import')}>
              Evaluate Historical
            </button>
          </div>
        )}
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}
      {notice && <div className="bg-soc-green/10 border border-soc-green/30 text-soc-green rounded-lg px-4 py-3 text-sm">{notice}</div>}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <div className="text-xs text-soc-muted uppercase">Total</div>
          <div className="mt-1 text-2xl font-bold text-soc-text">{summary?.total ?? 0}</div>
        </div>
        {['medium', 'high', 'low'].map((severity) => (
          <div className="card p-4" key={severity}>
            <div className="text-xs text-soc-muted uppercase">{severity}</div>
            <div className="mt-1 text-2xl font-bold text-soc-text">{summary?.by_severity?.[severity] ?? 0}</div>
          </div>
        ))}
      </div>

      <div className="bg-soc-panel border border-soc-border rounded-xl p-4 grid grid-cols-2 md:grid-cols-5 gap-3">
        <select className="input" value={filters.severity} onChange={(event) => setFilters({ ...filters, severity: event.target.value })}>
          <option value="">All severities</option>
          <option value="informational">Informational</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <select className="input" value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
        <select className="input" value={filters.rule_name} onChange={(event) => setFilters({ ...filters, rule_name: event.target.value })}>
          <option value="">All rules</option>
          <option value="High Packet Volume">High Packet Volume</option>
          <option value="Port Concentration">Port Concentration</option>
        </select>
        <select className="input" value={filters.capture_source} onChange={(event) => setFilters({ ...filters, capture_source: event.target.value })}>
          <option value="">All sources</option>
          <option value="live_capture">Live capture</option>
          <option value="historical_import">Historical import</option>
        </select>
        <button className="btn-primary" onClick={() => { setPage(1); load() }}>Apply</button>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} empty="No network alerts match the filters" />

      <div className="flex items-center justify-between text-sm text-soc-muted">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40">Prev</button>
          <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40">Next</button>
        </div>
      </div>
    </div>
  )
}
