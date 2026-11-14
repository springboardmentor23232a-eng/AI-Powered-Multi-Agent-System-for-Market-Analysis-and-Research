import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Activity,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  Menu,
  ScrollText,
  Shield,
  ShieldCheck,
  User,
  Users,
  UsersRound,
  X,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, permission: 'dashboard.view', end: true },
  { to: '/users', label: 'User Management', icon: Users, permission: 'users.view' },
  { to: '/roles', label: 'Roles & Permissions', icon: ShieldCheck, permission: 'roles.view' },
  { to: '/teams', label: 'Team Management', icon: UsersRound, permission: 'teams.view' },
  { to: '/audit-logs', label: 'Audit Logs', icon: ScrollText, permission: 'audit.view' },
]

export default function Layout() {
  const { user, logout, hasPermission } = useAuth()
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const visibleItems = NAV_ITEMS.filter((item) => hasPermission(item.permission))

  const sidebar = (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-5 h-16 border-b border-soc-border">
        <div className="w-9 h-9 rounded-lg bg-soc-accent/15 border border-soc-accent/40 flex items-center justify-center">
          <Shield size={20} className="text-soc-accentBright" />
        </div>
        <div>
          <div className="font-bold tracking-wide text-soc-text">NetShield AI</div>
          <div className="text-[10px] uppercase tracking-[0.18em] text-soc-muted">Security Operations</div>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${
                isActive
                  ? 'bg-soc-accent/10 text-soc-accentBright border border-soc-accent/30 shadow-glow'
                  : 'text-soc-muted hover:text-soc-text hover:bg-soc-panel2 border border-transparent'
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="px-3 py-4 border-t border-soc-border space-y-1">
        <NavLink
          to="/profile"
          onClick={() => setMobileOpen(false)}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
              isActive ? 'bg-soc-panel2 text-soc-text' : 'text-soc-muted hover:text-soc-text hover:bg-soc-panel2'
            }`
          }
        >
          <User size={18} />
          Profile
        </NavLink>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-soc-danger hover:bg-soc-danger/10 transition-colors"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-soc-bg flex">
      {/* Desktop sidebar */}
      <aside className="hidden lg:block w-64 shrink-0 bg-soc-panel border-r border-soc-border fixed inset-y-0 z-30">
        {sidebar}
      </aside>

      {/* Mobile sidebar */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="relative w-72 bg-soc-panel border-r border-soc-border z-50 shadow-2xl">
            <button
              className="absolute top-4 right-3 text-soc-muted hover:text-soc-text z-10"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
            >
              <X size={20} />
            </button>
            {sidebar}
          </aside>
        </div>
      )}

      <div className="flex-1 lg:ml-64 flex flex-col min-w-0">
        <header className="h-16 bg-soc-panel/80 backdrop-blur border-b border-soc-border flex items-center justify-between px-4 lg:px-8 sticky top-0 z-20">
          <div className="flex items-center gap-3">
            <button className="lg:hidden text-soc-muted hover:text-soc-text" onClick={() => setMobileOpen(true)} aria-label="Open menu">
              <Menu size={22} />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-sm">
              <Activity size={15} className="text-soc-green" />
              <span className="text-soc-muted">Security Console</span>
              <span className="text-soc-borderLight">/</span>
              <span className="text-soc-text font-medium capitalize">{user?.roles?.[0]?.replace(/_/g, ' ') ?? 'Workspace'}</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-xs font-mono text-soc-green bg-soc-green/10 border border-soc-green/30 rounded-full px-3 py-1">
              <span className="w-1.5 h-1.5 rounded-full bg-soc-green animate-pulse" />
              ALL SYSTEMS NOMINAL
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-soc-text">{user?.full_name}</div>
              <div className="text-[11px] text-soc-muted capitalize">
                {(user?.roles ?? []).map((r) => r.replace(/_/g, ' ')).join(' · ')}
              </div>
            </div>
            <div className="w-9 h-9 rounded-full bg-soc-accent/15 border border-soc-accent/40 flex items-center justify-center text-soc-accentBright font-bold text-sm">
              {user?.username?.[0]?.toUpperCase()}
            </div>
          </div>
        </header>
        <main className="flex-1 p-4 lg:p-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
