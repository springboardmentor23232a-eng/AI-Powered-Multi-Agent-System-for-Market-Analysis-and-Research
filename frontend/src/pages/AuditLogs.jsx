import { useCallback, useEffect, useState } from 'react'
import { Search, ScrollText } from 'lucide-react'
import api from '../api/client'
import DataTable from '../components/DataTable.jsx'

const STATUS_BADGE = {
  success: 'bg-soc-green/15 text-soc-green border-soc-green/40',
  failure: 'bg-soc-danger/15 text-soc-danger border-soc-danger/40',
}

export default function AuditLogs() {
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [filters, setFilters] = useState({
    action: '',
    status: '',
    target_type: '',
    date_from: '',
    date_to: '',
  })
  const [applied, setApplied] = useState(filters)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: 25 }
      Object.entries(applied).forEach(([k, v]) => {
        if (v) params[k] = k.startsWith('date') ? new Date(v).toISOString() : v
      })
      const { data } = await api.get('/audit-logs', { params })
      setRows(data.items)
      setTotal(data.total)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load audit logs')
    } finally {
      setLoading(false)
    }
  }, [page, applied])

  useEffect(() => {
    load()
  }, [load])

  const applyFilters = () => {
    setPage(1)
    setApplied({ ...filters })
  }

  const columns = [
    {
      key: 'timestamp',
      label: 'Timestamp',
      render: (r) => (
        <span className="font-mono text-xs text-soc-muted whitespace-nowrap">
          {r.timestamp ? new Date(r.timestamp).toLocaleString() : '—'}
        </span>
      ),
    },
    {
      key: 'actor',
      label: 'Actor',
      render: (r) =>
        r.actor_username ? (
          <div>
            <div className="text-slate-200">{r.actor_full_name}</div>
            <div className="text-xs text-soc-muted font-mono">{r.actor_username}</div>
          </div>
        ) : (
          <span className="text-soc-muted italic">anonymous / unknown</span>
        ),
    },
    { key: 'action', label: 'Action', render: (r) => <span className="font-mono text-xs text-soc-accent">{r.action}</span> },
    {
      key: 'target',
      label: 'Target',
      render: (r) =>
        r.target_type ? (
          <span className="text-xs text-soc-muted">
            {r.target_type}
            {r.target_id ? ` #${r.target_id}` : ''}
          </span>
        ) : (
          '—'
        ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_BADGE[r.status] ?? ''}`}>
          {r.status}
        </span>
      ),
    },
    {
      key: 'ip_address',
      label: 'IP',
      render: (r) => <span className="font-mono text-xs text-soc-muted">{r.ip_address || '—'}</span>,
    },
  ]

  const totalPages = Math.max(1, Math.ceil(total / 25))

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
          <ScrollText className="text-soc-accent" size={24} /> Audit Logs
        </h1>
        <p className="text-sm text-soc-muted">{total} event(s) — read-only record of security-relevant activity</p>
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}

      <div className="bg-soc-panel border border-soc-border rounded-xl p-4 grid grid-cols-2 md:grid-cols-5 gap-3">
        <input
          placeholder="Action (e.g. auth.login)"
          value={filters.action}
          onChange={(e) => setFilters({ ...filters, action: e.target.value })}
          className="bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm col-span-2"
        />
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })} className="bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm">
          <option value="">All statuses</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
        </select>
        <select value={filters.target_type} onChange={(e) => setFilters({ ...filters, target_type: e.target.value })} className="bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm">
          <option value="">All targets</option>
          <option value="user">User</option>
          <option value="team">Team</option>
          <option value="role">Role</option>
        </select>
        <button onClick={applyFilters} className="flex items-center justify-center gap-2 bg-soc-accent hover:bg-cyan-400 text-soc-bg font-semibold text-sm rounded-lg px-3 py-2">
          <Search size={15} /> Filter
        </button>
        <input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} className="bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm" title="From date" />
        <input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} className="bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm" title="To date" />
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} empty="No audit events match the filters" />

      <div className="flex items-center justify-between text-sm text-soc-muted">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40 hover:bg-soc-panel2">Prev</button>
          <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40 hover:bg-soc-panel2">Next</button>
        </div>
      </div>
    </div>
  )
}
