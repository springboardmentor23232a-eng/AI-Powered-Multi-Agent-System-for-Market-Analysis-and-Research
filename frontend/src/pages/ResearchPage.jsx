import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import { periodLabel } from '../api.js'
import { useData } from '../data.jsx'
import { fmtDate } from '../format.js'
import Page from '../components/Page.jsx'
import ReportPanel from '../components/ReportPanel.jsx'
import Status from '../components/Status.jsx'

export default function ResearchPage() {
  const { tasks } = useData()
  const [open, setOpen] = useState(null)
  const close = useCallback(() => setOpen(null), [])

  return (
    <Page title="Research history" aside={tasks.length ? `${tasks.length} total` : null}>
      {tasks.length === 0 ? (
        <p className="border-t border-ink py-6 text-mute">
          You have not run any research yet. Start from the <Link to="/dashboard" className="text-cobalt underline underline-offset-4">overview</Link> or your <Link to="/dashboard/watchlist" className="text-cobalt underline underline-offset-4">watchlist</Link>.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[680px] text-left">
            <thead className="border-b border-ink text-sm text-mute">
              <tr>
                <th className="py-2.5 pr-4 font-medium">Company</th>
                <th className="py-2.5 pr-4 font-medium">Market</th>
                <th className="py-2.5 pr-4 font-medium">Period</th>
                <th className="py-2.5 pr-4 font-medium">Started</th>
                <th className="py-2.5 pr-4 font-medium">Status</th>
                <th className="py-2.5 text-right font-medium">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line border-b border-line">
              {tasks.map((t) => (
                <tr key={t.task_id}>
                  <td className="py-4 pr-4">
                    <p className="font-medium">{t.company_name}</p>
                    <p className="num text-sm text-mute">{t.ticker}</p>
                  </td>
                  <td className="py-4 pr-4">{t.market}</td>
                  <td className="py-4 pr-4">{periodLabel(t.analysis_period)}</td>
                  <td className="num py-4 pr-4">{fmtDate(t.created_at)}</td>
                  <td className="py-4 pr-4"><Status value={t.status} /></td>
                  <td className="py-4 text-right">
                    {t.status === 'Completed' && <button className="btn-cobalt btn-sm" onClick={() => setOpen(t)}>Open report</button>}
                    {t.status === 'Failed' && <button className="btn-line btn-sm" onClick={() => setOpen(t)}>See why</button>}
                    {(t.status === 'Pending' || t.status === 'Processing') && <span className="text-sm text-mute">In progress</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {open && <ReportPanel task={open} onClose={close} />}
    </Page>
  )
}
