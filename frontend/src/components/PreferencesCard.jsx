import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { useApiErrorHandler } from '../auth/useApiErrorHandler'
import { ANALYSIS_PERIODS, MARKETS } from '../constants'
import { Alert, Button, Card, Field, inputClass } from './ui'

export default function PreferencesCard() {
  const { token } = useAuth()
  const handleError = useApiErrorHandler()

  const [saved, setSaved] = useState(null) // what the server has
  const [form, setForm] = useState(null) // what the user is editing
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api
      .getPreferences(token)
      .then((prefs) => {
        setSaved(prefs)
        setForm({ default_market: prefs.default_market, analysis_period: prefs.analysis_period })
      })
      .catch((err) => setError(handleError(err)))
  }, [token, handleError])

  const changed =
    form && saved &&
    (form.default_market !== saved.default_market || form.analysis_period !== saved.analysis_period)

  async function handleSave(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    setMessage('')
    try {
      const updated = await api.updatePreferences(token, form)
      setSaved(updated)
      setMessage('Preferences saved')
    } catch (err) {
      setError(handleError(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card title="Preferences" description="Defaults used when you start new research.">
      {!form ? (
        error ? <Alert>{error}</Alert> : <p className="text-sm text-slate-500">Loading…</p>
      ) : (
        <form onSubmit={handleSave} className="space-y-4">
          <Field label="Default market" id="default-market">
            <select id="default-market" className={inputClass} value={form.default_market}
              onChange={(e) => { setForm({ ...form, default_market: e.target.value }); setMessage('') }}>
              {MARKETS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </Field>
          <Field label="Analysis period" id="analysis-period">
            <select id="analysis-period" className={inputClass} value={form.analysis_period}
              onChange={(e) => { setForm({ ...form, analysis_period: e.target.value }); setMessage('') }}>
              {ANALYSIS_PERIODS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </Field>
          <Alert>{error}</Alert>
          <Alert kind="success">{message}</Alert>
          <Button type="submit" disabled={!changed || saving}>
            {saving ? 'Saving…' : 'Save preferences'}
          </Button>
        </form>
      )}
    </Card>
  )
}
