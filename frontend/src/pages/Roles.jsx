import { useCallback, useEffect, useState } from 'react'
import { ShieldCheck } from 'lucide-react'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import DataTable from '../components/DataTable.jsx'
import { Modal, ModalActions } from './Users.jsx'

export default function Roles() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('roles.manage')
  const [roles, setRoles] = useState([])
  const [permissions, setPermissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [editRole, setEditRole] = useState(null)
  const [editPerms, setEditPerms] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [r, p] = await Promise.all([api.get('/roles'), api.get('/roles/permissions')])
      setRoles(r.data)
      setPermissions(p.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load roles')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const openEdit = async (role) => {
    try {
      const { data } = await api.get(`/roles/${role.id}/permissions`)
      setEditRole(data)
      setEditPerms(data.permissions.map((p) => p.id))
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load role permissions')
    }
  }

  const savePerms = async () => {
    try {
      await api.put(`/roles/${editRole.id}/permissions`, { permission_ids: editPerms })
      setEditRole(null)
      setNotice('Role permissions updated.')
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to update permissions')
    }
  }

  const columns = [
    { key: 'role_name', label: 'Role', render: (r) => <span className="font-semibold text-slate-100">{r.role_name.replace(/_/g, ' ')}</span> },
    { key: 'description', label: 'Description' },
    {
      key: 'permissions',
      label: 'Permissions',
      render: (r) => (
        <span className="text-soc-muted">{(r.permissions ?? []).length} granted</span>
      ),
    },
    {
      key: 'actions',
      label: '',
      render: (r) =>
        canManage && r.role_name !== 'administrator' ? (
          <button
            onClick={() => openEdit(r)}
            className="flex items-center gap-1 text-xs text-soc-accent hover:underline"
          >
            <ShieldCheck size={14} /> Manage
          </button>
        ) : r.role_name === 'administrator' ? (
          <span className="text-xs text-soc-muted">All permissions (fixed)</span>
        ) : null,
    },
  ]

  const grouped = permissions.reduce((acc, p) => {
    ;(acc[p.module] ||= []).push(p)
    return acc
  }, {})

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Roles & Permissions</h1>
        <p className="text-sm text-soc-muted">Role-based access control configuration</p>
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}
      {notice && <div className="bg-soc-green/10 border border-soc-green/30 text-soc-green rounded-lg px-4 py-3 text-sm">{notice}</div>}

      <DataTable columns={columns} rows={roles} loading={loading} />

      {editRole && (
        <Modal title={`Permissions — ${editRole.role_name.replace(/_/g, ' ')}`} onClose={() => setEditRole(null)}>
          <div className="space-y-4 max-h-[55vh] overflow-y-auto pr-1">
            {Object.entries(grouped).map(([module, perms]) => (
              <div key={module}>
                <div className="text-xs uppercase tracking-wider text-soc-accent mb-1.5">{module}</div>
                <div className="space-y-1">
                  {perms.map((p) => (
                    <label key={p.id} className="flex items-start gap-2 text-sm text-slate-300">
                      <input
                        type="checkbox"
                        className="accent-cyan-400 mt-0.5"
                        checked={editPerms.includes(p.id)}
                        onChange={(e) =>
                          setEditPerms(
                            e.target.checked ? [...editPerms, p.id] : editPerms.filter((id) => id !== p.id),
                          )
                        }
                      />
                      <span>
                        <span className="font-mono text-xs text-soc-accent">{p.permission_code}</span>
                        {p.description && <span className="text-soc-muted"> — {p.description}</span>}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="pt-4">
            <ModalActions saving={false} onClose={() => setEditRole(null)} submitLabel="Save" />
            <button onClick={savePerms} className="hidden">save</button>
          </div>
          <div className="flex justify-end gap-2 pt-2 -mt-2">
            <button onClick={() => setEditRole(null)} className="px-4 py-2 text-sm rounded-lg border border-soc-border text-soc-muted hover:bg-soc-panel2">Cancel</button>
            <button onClick={savePerms} className="px-4 py-2 text-sm rounded-lg bg-soc-accent hover:bg-cyan-400 text-soc-bg font-semibold">Save Permissions</button>
          </div>
        </Modal>
      )}
    </div>
  )
}
