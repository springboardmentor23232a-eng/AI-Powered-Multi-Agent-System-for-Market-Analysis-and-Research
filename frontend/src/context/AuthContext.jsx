import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import api, { configureAuth } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [accessToken, setAccessToken] = useState(null) // memory only
  const [loading, setLoading] = useState(true)
  const tokenRef = useRef(null)
  tokenRef.current = accessToken

  const applySession = useCallback((data) => {
    setAccessToken(data.access_token)
    setUser(data.user)
  }, [])

  const clearSession = useCallback(() => {
    setAccessToken(null)
    setUser(null)
  }, [])

  useEffect(() => {
    configureAuth({
      getToken: () => tokenRef.current,
      onExpired: clearSession,
    })
    const handler = (e) => setAccessToken(e.detail)
    window.addEventListener('netshield:token', handler)
    return () => window.removeEventListener('netshield:token', handler)
  }, [clearSession])

  // On mount: try silent refresh via HttpOnly cookie
  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data } = await api.post('/auth/refresh')
        if (!cancelled) applySession(data)
      } catch {
        // no valid session
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [applySession])

  const login = useCallback(
    async (identifier, password) => {
      const { data } = await api.post('/auth/login', { identifier, password })
      applySession(data)
      return data.user
    },
    [applySession],
  )

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout')
    } finally {
      clearSession()
    }
  }, [clearSession])

  const refreshMe = useCallback(async () => {
    const { data } = await api.get('/auth/me')
    setUser((prev) => (prev ? { ...prev, ...data } : prev))
    return data
  }, [])

  const hasPermission = useCallback(
    (code) => {
      if (!user) return false
      if (user.roles?.includes('administrator')) return true
      return user.permissions?.includes(code)
    },
    [user],
  )

  const value = useMemo(
    () => ({
      user,
      accessToken,
      loading,
      login,
      logout,
      refreshMe,
      hasPermission,
      isAdmin: user?.roles?.includes('administrator') ?? false,
      isTeamLead: user?.roles?.includes('team_lead') ?? false,
    }),
    [user, accessToken, loading, login, logout, refreshMe, hasPermission],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
