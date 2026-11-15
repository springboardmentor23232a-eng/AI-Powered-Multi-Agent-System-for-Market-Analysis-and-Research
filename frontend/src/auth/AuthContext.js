import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

// Use inside any component: const { user, token, login, logout } = useAuth()
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
