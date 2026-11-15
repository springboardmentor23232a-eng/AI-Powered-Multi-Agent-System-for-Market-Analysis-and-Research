import { useCallback, useEffect, useMemo, useState } from 'react'

import { api } from '../api/client'
import { AuthContext } from './AuthContext'

const STORAGE_KEY = 'sra.session'

// The session (token + expiry time) is kept in localStorage so a page refresh
// does not log the user out. It is removed on logout or when it expires.
function loadStoredSession() {
  try {
    const session = JSON.parse(localStorage.getItem(STORAGE_KEY))
    if (session?.token && session.expiresAt > Date.now()) return session
  } catch {
    // corrupted value: ignore it
  }
  localStorage.removeItem(STORAGE_KEY)
  return null
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(loadStoredSession)
  const [user, setUser] = useState(null)
  // "loading" while we confirm a stored token with the backend.
  const [status, setStatus] = useState(session ? 'loading' : 'anonymous')

  const logout = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY)
    setSession(null)
    setUser(null)
    setStatus('anonymous')
  }, [])

  // Confirm the token is still accepted by the server and load the user.
  useEffect(() => {
    if (!session) return
    let cancelled = false
    api
      .me(session.token)
      .then((currentUser) => {
        if (cancelled) return
        setUser(currentUser)
        setStatus('authenticated')
      })
      .catch(() => {
        if (!cancelled) logout()
      })
    return () => {
      cancelled = true
    }
  }, [session, logout])

  // Log out automatically the moment the token expires.
  useEffect(() => {
    if (!session) return
    // Browsers cap timers at about 24.8 days; longer values would fire immediately.
    const delay = Math.min(session.expiresAt - Date.now(), 2_147_483_647)
    const timer = setTimeout(logout, delay)
    return () => clearTimeout(timer)
  }, [session, logout])

  const login = useCallback(async (email, password) => {
    const { access_token: token, expires_in: expiresIn } = await api.login(email, password)
    const newSession = { token, expiresAt: Date.now() + expiresIn * 1000 }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newSession))
    setStatus('loading')
    setSession(newSession)
  }, [])

  const register = useCallback(
    async (email, password) => {
      await api.register(email, password)
      await login(email, password)
    },
    [login],
  )

  const value = useMemo(
    () => ({ user, token: session?.token ?? null, status, login, register, logout }),
    [user, session, status, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
