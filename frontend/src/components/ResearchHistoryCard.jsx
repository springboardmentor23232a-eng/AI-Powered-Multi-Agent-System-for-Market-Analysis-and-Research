import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { useApiErrorHandler } from '../auth/useApiErrorHandler'
import { Alert, Card } from './ui'

const STATUS_STYLES = {
  pending: 'bg-slate-100 text-slate-700',
  running: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  partial: 'bg-amber-100 text-amber-800',
  failed: 'bg-red-100 text-red-700',
}

export default function ResearchHistoryCard() {
  const { token } = useAuth()
  const handleError = useApiErrorHandler()
  const [history, setHistory] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.getResearchHistory(token).then(setHistory).catch((err) => setError(handleError(err)))
  }, [token, handleError])

  return (
    <Card title="Research history" description="Your previous research requests.">
      <Alert>{error}</Alert>
      {!history && !error && <p className="text-sm text-slate-500">Loading…</p>}
      {history && history.total === 0 && (
        <p className="text-sm text-slate-500">
          No research yet. Running stock research becomes available once the analysis agents
          are added in later modules.
        </p>
      )}
      {history && history.total > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="text-slate-500">
            <tr><th className="py-1">Ticker</th><th>Market</th><th>Period</th><th>Status</th><th>Requested</th></tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {history.items.map((task) => (
              <tr key={task.task_id}>
                <td className="py-2 font-medium">{task.ticker}</td>
                <td>{task.market}</td>
                <td>{task.requested_period}</td>
                <td><span className={`rounded px-2 py-0.5 text-xs ${STATUS_STYLES[task.status]}`}>{task.status}</span></td>
                <td>{new Date(task.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  )
}
