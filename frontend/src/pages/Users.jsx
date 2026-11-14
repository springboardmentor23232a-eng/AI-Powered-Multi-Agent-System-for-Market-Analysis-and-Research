import { useCallback, useEffect, useState } from 'react'
import { KeyRound, Pencil, Plus, Search, ShieldCheck, UserCheck, UserX } from 'lucide-react'
import api, { apiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import DataTable from '../components/DataTable.jsx'

const STATUS_BADGE = {
  active: 'bg-soc-green/15 text-soc-green border-soc-green/40',
  inactive: 'bg-soc-muted/15 text-soc-muted border-soc-muted/40',
  locked: 'bg-soc-danger/15 text-soc-danger border-soc-danger/40',
}

export default function Users() {
  const { hasPermission, user: me } = useAuth()
  const canCreate = hasPermission('users.create')
  const canUpdate = hasPermission('users.update')
  const canStatus = hasPermission('users.activate')
  const canRoles = hasPermission('users.assign_roles')

  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const [showCreate, setShowCreate] = useState(false)
  const [editUser, setEditUser] = useState(null)
  const [rolesUser, setRolesUser] = useState(null)
  const [rolesOptions, setRolesOptions] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = { page, page_size: 15 }
      if (search) params.search = search
      if (statusFilter) params.status = statusFilter
      const { data } = await api.get('/users', { params })
      setRows(data.items)
      setTotal(data.total)
    } catch (e) {
      setError(apiError(e, 'Failed to load users'))
    } finally {
      setLoading(false)
    }
  }, [page, search, statusFilter])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (canRoles || canCreate) {
      api.get('/roles').then((r) => setRolesOptions(r.data)).catch(() => {})
    }
  }, [canRoles, canCreate])

  const toggleStatus = async (u) => {
    const next = u.status === 'active' ? 'inactive' : 'active'
    try {
      await api.post(`/users/${u.id}/status`, { status: next })
      setNotice(`User ${u.username} ${next === 'active' ? 'activated' : 'deactivated'}.`)
      load()
    } catch (e) {
      setError(apiError(e, 'Status change failed'))
    }
  }

  const columns = [
    { key: 'username', label: 'Username', render: (r) => <span className="font-mono text-soc-accent">{r.username}</span> },
    { key: 'full_name', label: 'Full Name' },
    { key: 'email', label: 'Email' },
    {
      key: 'roles',
      label: 'Roles',
      render: (r) => (
        <div className="flex flex-wrap gap-1">
          {(r.roles ?? []).map((role) => (
            <span key={role} className="text-[11px] px-2 py-0.5 rounded-full bg-soc-accentBright/15 text-soc-accentBright border border-soc-accentBright/30">
              {role.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => (
        <span className={`text-xs px-2 py-0.5 rounded-full border ${STATUS_BADGE[r.status]}`}>
          {r.status}
        </span>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (r) => (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {canUpdate && (
            <button title="Edit" onClick={() => setEditUser(r)} className="p-1.5 rounded hover:bg-soc-panel2 text-soc-muted hover:text-soc-accent">
              <Pencil size={15} />
            </button>
          )}
          {canRoles && (
            <button title="Assign roles" onClick={() => setRolesUser(r)} className="p-1.5 rounded hover:bg-soc-panel2 text-soc-muted hover:text-soc-accentBright">
              <ShieldCheck size={15} />
            </button>
          )}
          {canStatus && r.id !== me?.id && (
            <button
              title={r.status === 'active' ? 'Deactivate' : 'Activate'}
              onClick={() => toggleStatus(r)}
              className={`p-1.5 rounded hover:bg-soc-panel2 ${r.status === 'active' ? 'text-soc-muted hover:text-soc-danger' : 'text-soc-muted hover:text-soc-green'}`}
            >
              {r.status === 'active' ? <UserX size={15} /> : <UserCheck size={15} />}
            </button>
          )}
        </div>
      ),
    },
  ]

  const totalPages = Math.max(1, Math.ceil(total / 15))

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">User Management</h1>
          <p className="text-sm text-soc-muted">{total} account(s)</p>
        </div>
        {canCreate && (
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 bg-soc-accent hover:bg-cyan-400 text-soc-bg font-semibold text-sm rounded-lg px-4 py-2"
          >
            <Plus size={16} /> New User
          </button>
        )}
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}
      {notice && <div className="bg-soc-green/10 border border-soc-green/30 text-soc-green rounded-lg px-4 py-3 text-sm">{notice}</div>}

      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-soc-muted" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search username, email, name..."
            className="w-full bg-soc-panel border border-soc-border rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:border-soc-accent"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          className="bg-soc-panel border border-soc-border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
          <option value="locked">Locked</option>
        </select>
      </div>

      <DataTable columns={columns} rows={rows} loading={loading} />

      <div className="flex items-center justify-between text-sm text-soc-muted">
        <span>Page {page} of {totalPages}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40 hover:bg-soc-panel2">Prev</button>
          <button disabled={page >= totalPages} onClick={() => setPage(page + 1)} className="px-3 py-1.5 rounded border border-soc-border disabled:opacity-40 hover:bg-soc-panel2">Next</button>
        </div>
      </div>

      {showCreate && (
        <UserFormModal
          rolesOptions={rolesOptions}
          onClose={() => setShowCreate(false)}
          onSaved={() => { setShowCreate(false); setNotice('User created.'); load() }}
          onError={setError}
        />
      )}
      {editUser && (
        <EditUserModal
          user={editUser}
          onClose={() => setEditUser(null)}
          onSaved={() => { setEditUser(null); setNotice('User updated.'); load() }}
          onError={setError}
        />
      )}
      {rolesUser && (
        <RolesModal
          user={rolesUser}
          rolesOptions={rolesOptions}
          onClose={() => setRolesUser(null)}
          onSaved={() => { setRolesUser(null); setNotice('Roles updated.'); load() }}
          onError={setError}
        />
      )}
    </div>
  )
}

function UserFormModal({ rolesOptions, onClose, onSaved, onError }) {
  const [form, setForm] = useState({ username: '', email: '', full_name: '', password: '', role_ids: [] })
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    onError('')
    try {
      await api.post('/users', form)
      onSaved()
    } catch (err) {
      onError(apiError(err, 'Failed to create user'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="Create User" onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Field label="Username" value={form.username} onChange={(v) => setForm({ ...form, username: v })} required />
        <Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required />
        <Field label="Full Name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} required />
        <Field label="Password (min 8 chars)" type="password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} required />
        <div>
          <label className="block text-xs uppercase tracking-wider text-soc-muted mb-1.5">Roles</label>
          <div className="space-y-1.5">
            {rolesOptions.map((r) => (
              <label key={r.id} className="flex items-center gap-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={form.role_ids.includes(r.id)}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      role_ids: e.target.checked
                        ? [...form.role_ids, r.id]
                        : form.role_ids.filter((id) => id !== r.id),
                    })
                  }
                  className="accent-cyan-400"
                />
                {r.role_name.replace(/_/g, ' ')}
              </label>
            ))}
          </div>
        </div>
        <ModalActions saving={saving} onClose={onClose} submitLabel="Create" />
      </form>
    </Modal>
  )
}

function EditUserModal({ user, onClose, onSaved, onError }) {
  const [form, setForm] = useState({ username: user.username, email: user.email, full_name: user.full_name })
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    onError('')
    try {
      await api.put(`/users/${user.id}`, form)
      onSaved()
    } catch (err) {
      onError(apiError(err, 'Failed to update user'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={`Edit User — ${user.username}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Field label="Username" value={form.username} onChange={(v) => setForm({ ...form, username: v })} required />
        <Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} required />
        <Field label="Full Name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} required />
        <ModalActions saving={saving} onClose={onClose} submitLabel="Save" />
      </form>
    </Modal>
  )
}

function RolesModal({ user, rolesOptions, onClose, onSaved, onError }) {
  const [selected, setSelected] = useState(user.role_ids ?? [])
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    onError('')
    try {
      await api.put(`/users/${user.id}/roles`, { role_ids: selected })
      onSaved()
    } catch (err) {
      onError(apiError(err, 'Failed to update roles'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={`Assign Roles — ${user.username}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <div className="space-y-1.5">
          {rolesOptions.map((r) => (
            <label key={r.id} className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={selected.includes(r.id)}
                onChange={(e) =>
                  setSelected(e.target.checked ? [...selected, r.id] : selected.filter((id) => id !== r.id))
                }
                className="accent-cyan-400"
              />
              {r.role_name.replace(/_/g, ' ')}
            </label>
          ))}
        </div>
        <ModalActions saving={saving} onClose={onClose} submitLabel="Save Roles" />
      </form>
    </Modal>
  )
}

export function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative bg-soc-panel border border-soc-border rounded-xl w-full max-w-md p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-100">{title}</h3>
          <button onClick={onClose} className="text-soc-muted hover:text-slate-200 text-xl leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function Field({ label, value, onChange, type = 'text', required = false }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-wider text-soc-muted mb-1.5">{label}</label>
      <input
        type={type}
        value={value}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-soc-accent"
      />
    </div>
  )
}

export function ModalActions({ saving, onClose, submitLabel = 'Save' }) {
  return (
    <div className="flex justify-end gap-2 pt-2">
      <button type="button" onClick={onClose} className="px-4 py-2 text-sm rounded-lg border border-soc-border text-soc-muted hover:bg-soc-panel2">
        Cancel
      </button>
      <button type="submit" disabled={saving} className="px-4 py-2 text-sm rounded-lg bg-soc-accent hover:bg-cyan-400 text-soc-bg font-semibold disabled:opacity-50">
        {saving ? 'Saving...' : submitLabel}
      </button>
    </div>
  )
}
