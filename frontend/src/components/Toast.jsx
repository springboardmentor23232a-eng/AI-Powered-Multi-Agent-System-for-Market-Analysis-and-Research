import { Link } from 'react-router-dom'
import { useData } from '../data.jsx'

export default function Toast() {
  const { toast } = useData()
  if (!toast) return null
  return (
    <div role="status" key={toast.id}
      className={'slide-in fixed bottom-20 left-4 right-4 z-50 flex items-center justify-between gap-4 rounded-md px-4 py-3 text-sm font-medium text-white shadow-lg sm:right-auto sm:max-w-md lg:bottom-6 lg:left-[288px] ' + (toast.kind === 'error' ? 'bg-loss' : 'bg-ink')}>
      <span>{toast.text}</span>
      {toast.action && <Link to={toast.action.to} className="shrink-0 underline underline-offset-4 hover:text-mark">{toast.action.label}</Link>}
    </div>
  )
}
