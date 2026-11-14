import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { api, periodLabel } from '../api.js'
import { fmtDate } from '../format.js'
import Status from './Status.jsx'

export default function ReportPanel({ task, onClose }) {
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api.report(task.task_id).then(setDetail).catch((e) => setError(e.message))
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [task.task_id, onClose])

  const body = error || (!detail ? 'Loading…'
    : detail.status === 'Failed' ? detail.error_message || 'This research did not finish.'
    : detail.report || 'This report has no content yet.')

  return (
    <div className="fixed inset-0 z-50 bg-ink/50" onClick={onClose}>
      <aside role="dialog" aria-label={`${task.company_name} report`} onClick={(e) => e.stopPropagation()}
        className="slide-in ml-auto flex h-full w-full max-w-xl flex-col bg-paper shadow-2xl">
        <div className="flex items-start justify-between gap-4 border-b border-line px-7 py-6">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">{task.company_name}</h2>
            <p className="num mt-1 text-mute">{task.ticker}, {task.market}, {periodLabel(task.analysis_period)} of data, started {fmtDate(task.created_at)}</p>
            <div className="mt-3"><Status value={task.status} /></div>
          </div>
          <button onClick={onClose} aria-label="Close report" className="rounded-md p-1.5 text-mute hover:bg-line/60 hover:text-ink"><X size={20} /></button>
        </div>
        <div className="flex-1 overflow-y-auto px-7 py-6">
          <p className="max-w-prose whitespace-pre-wrap font-serif text-[17px] leading-[1.7]">{body}</p>
        </div>
      </aside>
    </div>
  )
}
