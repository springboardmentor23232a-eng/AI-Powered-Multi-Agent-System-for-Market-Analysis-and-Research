import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Users from './pages/Users.jsx'
import Roles from './pages/Roles.jsx'
import Teams from './pages/Teams.jsx'
import AuditLogs from './pages/AuditLogs.jsx'
import Profile from './pages/Profile.jsx'
import ChangePassword from './pages/ChangePassword.jsx'
import TrafficMonitor from './pages/TrafficMonitor.jsx'
import Alerts from './pages/Alerts.jsx'

function App() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-soc-bg">
        <div className="text-soc-accent font-mono text-sm animate-pulse">
          NETSHIELD AI // INITIALIZING SECURE SESSION...
        </div>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to="/" replace /> : <Register />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/users" element={<ProtectedRoute permission="users.view"><Users /></ProtectedRoute>} />
        <Route path="/roles" element={<ProtectedRoute permission="roles.view"><Roles /></ProtectedRoute>} />
        <Route path="/teams" element={<ProtectedRoute permission="teams.view"><Teams /></ProtectedRoute>} />
        <Route path="/audit-logs" element={<ProtectedRoute permission="audit.view"><AuditLogs /></ProtectedRoute>} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/change-password" element={<ChangePassword />} />
        <Route path="/traffic" element={<ProtectedRoute permission="network.view"><TrafficMonitor /></ProtectedRoute>} />
        <Route path="/alerts" element={<ProtectedRoute permission="alerts.view"><Alerts /></ProtectedRoute>} />
      </Route>
      <Route path="*" element={<Navigate to={user ? '/' : '/login'} replace />} />
    </Routes>
  )
}

export default App
