import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { api } from './api.js'

const DataContext = createContext(null)
export const useData = () => useContext(DataContext)

export function DataProvider({ children }) {
  const [prefs, setPrefs] = useState(null)
  const [saved, setSaved] = useState([])
  const [tasks, setTasks] = useState([])
  const [ready, setReady] = useState(false)
  const [toast, setToast] = useState(null)
  const timer = useRef()

  const notify = useCallback((text, kind = 'ok', action = null) => {
    clearTimeout(timer.current)
    setToast({ text, kind, action, id: Date.now() })
    timer.current = setTimeout(() => setToast(null), 5000)
  }, [])

  useEffect(() => {
    Promise.all([api.preferences(), api.watchlist(), api.history()])
      .then(([p, w, h]) => { setPrefs(p); setSaved(w); setTasks(h) })
      .catch((e) => e.status !== 401 && notify(e.message, 'error'))
      .finally(() => setReady(true))
  }, [notify])

  const run = (fn) => async (...args) => {
    try { return await fn(...args) } catch (e) {
      if (e.status !== 401) notify(e.message, 'error')
      return null
    }
  }

  const value = {
    prefs, saved, tasks, ready, toast,
    savePrefs: run(async (p) => {
      setPrefs(await api.savePreferences(p))
      notify('Preferences saved')
      return true
    }),
    addStock: run(async (s) => {
      const r = await api.addStock(s)
      setSaved((l) => [r, ...l])
      notify(`${r.ticker} saved to your watchlist`)
      return true
    }),
    removeStock: run(async (s) => {
      await api.removeStock(s.saved_stock_id)
      setSaved((l) => l.filter((x) => x.saved_stock_id !== s.saved_stock_id))
      notify(`${s.ticker} removed from your watchlist`)
      return true
    }),
    research: run(async (s) => {
      const t = await api.startResearch({ ticker: s.ticker, company_name: s.company_name, market: s.market })
      setTasks((l) => [t, ...l])
      notify(`Research started for ${t.ticker}`, 'ok', { to: '/dashboard/research', label: 'View history' })
      return true
    }),
  }
  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}
