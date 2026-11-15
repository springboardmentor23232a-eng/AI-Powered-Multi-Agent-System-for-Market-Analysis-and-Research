import { Navigate } from 'react-router-dom'

import { useAuth } from './AuthContext'

// Shows its children only to logged-in users; everyone else is sent to /login.
export function ProtectedRoute({ children }) {
  const { status } = useAuth()
  if (status === 'loading') {
    return <p className="p-8 text-center text-slate-500">Checking your session…</p>
  }
  if (status !== 'authenticated') return <Navigate to="/login" replace />
  return children
}

// The opposite: logged-in users who open /login or /register go to the workspace.
export function GuestRoute({ children }) {
  const { status } = useAuth()
  if (status === 'authenticated') return <Navigate to="/" replace />
  return children
}
