import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ permission, roles, children }) {
  const { user, loading, hasPermission } = useAuth()
  const location = useLocation()

  if (loading) return null
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />

  if (roles && !roles.some((r) => user.roles?.includes(r))) {
    return <Navigate to="/" replace />
  }
  if (permission && !hasPermission(permission)) {
    return (
      <div className="p-10 text-center">
        <h2 className="text-xl font-semibold text-soc-danger">Access Denied</h2>
        <p className="text-soc-muted mt-2">You do not have permission to view this page.</p>
      </div>
    )
  }

  return children ?? <Outlet />
}
