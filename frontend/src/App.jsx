import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import AuthPage from './pages/AuthPage.jsx'
import DashboardLayout from './pages/DashboardLayout.jsx'
import Home from './pages/Home.jsx'
import Overview from './pages/Overview.jsx'
import PreferencesPage from './pages/PreferencesPage.jsx'
import ResearchPage from './pages/ResearchPage.jsx'
import WatchlistPage from './pages/WatchlistPage.jsx'

export default function App() {
  const { user, loading } = useAuth()
  if (loading) {
    return <div className="grid min-h-screen place-items-center"><div className="h-7 w-7 animate-spin rounded-full border-2 border-cobalt border-t-transparent" /></div>
  }
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <AuthPage mode="login" />} />
      <Route path="/register" element={user ? <Navigate to="/dashboard" replace /> : <AuthPage mode="register" />} />
      <Route path="/dashboard" element={user ? <DashboardLayout /> : <Navigate to="/login" replace />}>
        <Route index element={<Overview />} />
        <Route path="watchlist" element={<WatchlistPage />} />
        <Route path="research" element={<ResearchPage />} />
        <Route path="preferences" element={<PreferencesPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
