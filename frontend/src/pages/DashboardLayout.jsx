import { NavLink, Outlet } from 'react-router-dom'
import { ClipboardList, LayoutGrid, LogOut, SlidersHorizontal, Star } from 'lucide-react'
import { useAuth } from '../auth.jsx'
import { DataProvider, useData } from '../data.jsx'
import Mark from '../components/Mark.jsx'
import Toast from '../components/Toast.jsx'

function Shell() {
  const { user, logout } = useAuth()
  const { saved, tasks, prefs, ready } = useData()
  const nav = [
    { to: '/dashboard', end: true, label: 'Overview', icon: LayoutGrid },
    { to: '/dashboard/watchlist', label: 'Watchlist', icon: Star, count: saved.length },
    { to: '/dashboard/research', label: 'Research', icon: ClipboardList, count: tasks.length },
    { to: '/dashboard/preferences', label: 'Preferences', icon: SlidersHorizontal },
  ]

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      <aside className="on-cobalt sticky top-0 hidden h-screen flex-col bg-ink px-5 py-7 text-white lg:flex">
        <div className="px-2"><Mark light /></div>
        <nav className="mt-10 space-y-1">
          {nav.map(({ to, end, label, icon: Icon, count }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) => 'flex items-center gap-3 rounded-md px-3 py-2.5 text-[15px] font-medium transition-colors ' + (isActive ? 'bg-cobalt text-white' : 'text-white/70 hover:bg-white/10 hover:text-white')}>
              <Icon size={18} /> <span className="flex-1">{label}</span>
              {count > 0 && <span className="num text-sm text-white/60">{count}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto border-t border-white/15 px-2 pt-5">
          <p className="truncate text-sm font-semibold">{user.full_name}</p>
          <p className="truncate text-sm text-white/60">{user.email}</p>
          <button onClick={logout} className="mt-3 inline-flex items-center gap-2 text-sm text-white/70 hover:text-white"><LogOut size={15} /> Log out</button>
        </div>
      </aside>

      <main className="min-w-0 pb-20 lg:pb-0">
        <div className="flex items-center justify-between border-b border-line px-6 py-4 lg:hidden">
          <Mark />
          <button onClick={logout} className="text-sm font-medium text-mute hover:text-ink">Log out</button>
        </div>
        {!prefs ? (
          <p className="px-6 py-16 text-mute sm:px-10">
            {ready ? 'We could not load your workspace. Check that the backend is running, then refresh the page.' : 'Loading your workspace…'}
          </p>
        ) : <Outlet />}
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-white/10 bg-ink lg:hidden">
        {nav.map(({ to, end, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={end}
            className={({ isActive }) => 'flex flex-col items-center gap-1 py-2.5 text-xs font-medium ' + (isActive ? 'text-mark' : 'text-white/70')}>
            <Icon size={19} /> {label}
          </NavLink>
        ))}
      </nav>
      <Toast />
    </div>
  )
}

export default function DashboardLayout() {
  return <DataProvider><Shell /></DataProvider>
}
