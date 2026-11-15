import { Navigate, Route, Routes } from 'react-router-dom'

import { GuestRoute, ProtectedRoute } from './auth/ProtectedRoute'
import AuthPage from './pages/AuthPage'
import WorkspacePage from './pages/WorkspacePage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ProtectedRoute><WorkspacePage /></ProtectedRoute>} />
      <Route path="/login" element={<GuestRoute><AuthPage mode="login" /></GuestRoute>} />
      <Route path="/register" element={<GuestRoute><AuthPage mode="register" /></GuestRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
