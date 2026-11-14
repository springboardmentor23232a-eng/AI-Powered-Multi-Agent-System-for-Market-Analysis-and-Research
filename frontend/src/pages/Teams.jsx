import { useCallback, useEffect, useState } from 'react'
import { Pencil, Plus, Trash2, UserPlus, UsersRound, X } from 'lucide-react'
import api, { apiError } from '../api/client'
import { useAuth } from '../context/AuthContext'
import DataTable from '../components/DataTable.jsx'
import { Field, Modal, ModalActions } from './Users.jsx'

export default function Teams() {
  const { hasPermission, isAdmin } = useAuth()
  const canCreate = hasPermission('teams.create')
  const canUpdate = hasPermission('teams.update')
  const canDelete = hasPermission('teams.delete')
  const canMembers = hasPermission('teams.manage_members')

  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [selected, setSelected] = useState(null) // team detail
  const [showCreate, setShowCreate] = useState(false)
  const [editTeam, setEditTeam] = useState(null)
  const [addMemberFor, setAddMemberFor] = useState(null)
  const [allUsers, setAllUsers] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/teams')
      setTeams(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load teams')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const openDetail = async (team) => {
    try {
      const { data } = await api.get(`/teams/${team.id}`)
      setSelected(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to load team')
    }
  }

  const refreshDetail = async (teamId) => {
    const { data } = await api.get(`/teams/${teamId}`)
    setSelected(data)
    load()
  }

  const removeMember = async (teamId, userId) => {
    try {
      await api.delete(`/teams/${teamId}/members/${userId}`)
      setNotice('Member removed.')
      refreshDetail(teamId)
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to remove member')
    }
  }

  const deleteTeam = async (team) => {
    if (!window.confirm(`Delete team "${team.team_name}"? This cannot be undone.`)) return
    try {
      await api.delete(`/teams/${team.id}`)
      setSelected(null)
      setNotice('Team deleted.')
      load()
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to delete team')
    }
  }

  const openAddMember = async (team) => {
    try {
      const { data } = await api.get(`/teams/${team.id}/candidate-users`)
      setAllUsers(data)
      setAddMemberFor(team)
    } catch (e) {
      setError(apiError(e, 'Failed to load eligible users'))
    }
  }

  const columns = [
    { key: 'team_name', label: 'Team', render: (r) => <span className="font-semibold text-slate-100">{r.team_name}</span> },
    { key: 'description', label: 'Description', render: (r) => <span className="text-soc-muted">{r.description || '—'}</span> },
    { key: 'lead_full_name', label: 'Lead', render: (r) => r.lead_full_name || <span className="text-soc-muted">—</span> },
    { key: 'member_count', label: 'Members', render: (r) => <span className="font-mono">{r.member_count ?? '—'}</span> },
    {
      key: 'actions',
      label: '',
      render: (r) => (
        <div className="flex gap-1">
          {canUpdate && (
            <button title="Edit" onClick={(e) => { e.stopPropagation(); setEditTeam(r) }} className="p-1.5 rounded hover:bg-soc-panel2 text-soc-muted hover:text-soc-accent">
              <Pencil size={15} />
            </button>
          )}
          {canDelete && isAdmin && (
            <button title="Delete" onClick={(e) => { e.stopPropagation(); deleteTeam(r) }} className="p-1.5 rounded hover:bg-soc-panel2 text-soc-muted hover:text-soc-danger">
              <Trash2 size={15} />
            </button>
          )}
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Team Management</h1>
          <p className="text-sm text-soc-muted">{teams.length} team(s) visible to you</p>
        </div>
        {canCreate && (
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 bg-soc-accent hover:bg-cyan-400 text-soc-bg font-semibold text-sm rounded-lg px-4 py-2">
            <Plus size={16} /> New Team
          </button>
        )}
      </div>

      {error && <div className="bg-soc-danger/10 border border-soc-danger/30 text-soc-danger rounded-lg px-4 py-3 text-sm">{error}</div>}
      {notice && <div className="bg-soc-green/10 border border-soc-green/30 text-soc-green rounded-lg px-4 py-3 text-sm">{notice}</div>}

      <DataTable columns={columns} rows={teams} loading={loading} onRowClick={openDetail} />

      {/* Team detail drawer */}
      {selected && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div className="absolute inset-0 bg-black/60" onClick={() => setSelected(null)} />
          <div className="relative w-full max-w-lg bg-soc-panel border-l border-soc-border h-full overflow-y-auto p-6">
            <div className="flex items-start justify-between mb-5">
              <div>
                <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
                  <UsersRound size={20} className="text-soc-accent" /> {selected.team_name}
                </h2>
                <p className="text-sm text-soc-muted mt-1">{selected.description || 'No description'}</p>
                <p className="text-xs text-soc-muted mt-1">
                  Lead: {selected.lead_full_name || 'Unassigned'} • Created {selected.created_at ? new Date(selected.created_at).toLocaleDateString() : ''}
                </p>
              </div>
              <button onClick={() => setSelected(null)} className="text-soc-muted hover:text-slate-200"><X size={20} /></button>
            </div>

            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-soc-muted">
                Members ({selected.members?.length ?? 0})
              </h3>
              {canMembers && (
                <button onClick={() => openAddMember(selected)} className="flex items-center gap-1 text-xs text-soc-accent hover:underline">
                  <UserPlus size={14} /> Add member
                </button>
              )}
            </div>

            <ul className="space-y-2">
              {(selected.members ?? []).map((m) => (
                <li key={m.id} className="flex items-center justify-between bg-soc-bg border border-soc-border rounded-lg px-4 py-3">
                  <div>
                    <div className="text-sm font-medium text-slate-200">{m.full_name}</div>
                    <div className="text-xs text-soc-muted font-mono">{m.username} • {(m.roles ?? []).join(', ')}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full border ${m.status === 'active' ? 'bg-soc-green/15 text-soc-green border-soc-green/40' : 'bg-soc-muted/15 text-soc-muted border-soc-muted/40'}`}>
                      {m.status}
                    </span>
                    {canMembers && (
                      <button onClick={() => removeMember(selected.id, m.id)} className="p-1.5 rounded hover:bg-soc-danger/15 text-soc-muted hover:text-soc-danger" title="Remove">
                        <X size={15} />
                      </button>
                    )}
                  </div>
                </li>
              ))}
              {(!selected.members || selected.members.length === 0) && (
                <li className="text-sm text-soc-muted text-center py-6">No members assigned.</li>
              )}
            </ul>
          </div>
        </div>
      )}

      {showCreate && (
        <TeamFormModal
          title="Create Team"
          onClose={() => setShowCreate(false)}
          onSaved={() => { setShowCreate(false); setNotice('Team created.'); load() }}
          onError={setError}
        />
      )}
      {editTeam && (
        <TeamFormModal
          title="Edit Team"
          team={editTeam}
          onClose={() => setEditTeam(null)}
          onSaved={() => { setEditTeam(null); setNotice('Team updated.'); load(); if (selected?.id === editTeam.id) refreshDetail(editTeam.id) }}
          onError={setError}
        />
      )}
      {addMemberFor && (
        <AddMemberModal
          team={addMemberFor}
          users={allUsers}
          onClose={() => setAddMemberFor(null)}
          onAdded={async (userId) => {
            setAddMemberFor(null)
            setNotice('Member added.')
            await refreshDetail(addMemberFor.id)
          }}
          onError={setError}
        />
      )}
    </div>
  )
}

function TeamFormModal({ title, team, onClose, onSaved, onError }) {
  const [form, setForm] = useState({
    team_name: team?.team_name ?? '',
    description: team?.description ?? '',
    lead_user_id: team?.lead_user_id ?? '',
  })
  const [users, setUsers] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/users', { params: { status: 'active', page_size: 100 } })
      .then((r) => setUsers(r.data.items))
      .catch(() => {})
  }, [])

  const submit = async (e) => {
    e.preventDefault()
    setSaving(true)
    onError('')
    const payload = {
      team_name: form.team_name,
      description: form.description || null,
      lead_user_id: form.lead_user_id ? Number(form.lead_user_id) : null,
    }
    try {
      if (team) await api.put(`/teams/${team.id}`, payload)
      else await api.post('/teams', payload)
      onSaved()
    } catch (err) {
      onError(err.response?.data?.detail || 'Failed to save team')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <Field label="Team Name" value={form.team_name} onChange={(v) => setForm({ ...form, team_name: v })} required />
        <div>
          <label className="block text-xs uppercase tracking-wider text-soc-muted mb-1.5">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            rows={3}
            className="w-full bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-soc-accent"
          />
        </div>
        <div>
          <label className="block text-xs uppercase tracking-wider text-soc-muted mb-1.5">Team Lead (optional)</label>
          <select
            value={form.lead_user_id}
            onChange={(e) => setForm({ ...form, lead_user_id: e.target.value })}
            className="w-full bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">— None —</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.full_name} ({u.username})</option>
            ))}
          </select>
        </div>
        <ModalActions saving={saving} onClose={onClose} submitLabel={team ? 'Save' : 'Create'} />
      </form>
    </Modal>
  )
}

function AddMemberModal({ team, users, onClose, onAdded, onError }) {
  const [userId, setUserId] = useState('')
  const [saving, setSaving] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!userId) return
    setSaving(true)
    onError('')
    try {
      await api.post(`/teams/${team.id}/members`, { user_id: Number(userId) })
      onAdded(Number(userId))
    } catch (err) {
      onError(apiError(err, 'Failed to add member'))
      setSaving(false)
    }
  }

  return (
    <Modal title={`Add Member — ${team.team_name}`} onClose={onClose}>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="block text-xs uppercase tracking-wider text-soc-muted mb-1.5">User</label>
          <select
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            required
            className="w-full bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-sm"
          >
            <option value="">Select a user...</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>{u.full_name} ({u.username})</option>
            ))}
          </select>
        </div>
        <ModalActions saving={saving} onClose={onClose} submitLabel="Add" />
      </form>
    </Modal>
  )
}
