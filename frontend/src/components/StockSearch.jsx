import { useEffect, useState } from 'react'
import { Check, Loader2, Search } from 'lucide-react'
import { api } from '../api.js'
import { useData } from '../data.jsx'

export default function StockSearch({ placeholder }) {
  const { prefs, saved, addStock, research } = useData()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')
  const market = prefs.market

  useEffect(() => {
    const q = query.trim()
    setError('')
    if (!q) { setResults([]); setLoading(false); return }
    setLoading(true)
    let cancelled = false
    const t = setTimeout(() => {
      api.search(q, market)
        .then((r) => {
          if (cancelled) return
          setResults(r)
          if (!r.length) setError(`No ${market} listings match “${q}”. Try the company name or its ticker.`)
        })
        .catch((e) => { if (!cancelled) { setResults([]); setError(e.message) } })
        .finally(() => { if (!cancelled) setLoading(false) })
    }, 400)
    return () => { cancelled = true; clearTimeout(t) }
  }, [query, market])

  const savedTickers = new Set(saved.map((s) => s.ticker))
  const act = (key, fn) => async () => { setBusy(key); await fn(); setBusy('') }

  return (
    <div>
      <label htmlFor="stock-search" className="sr-only">Search stocks</label>
      <div className="relative">
        <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-mute" />
        <input id="stock-search" className="field !py-3.5 !pl-11 text-base" placeholder={placeholder || `Search ${market} by company or ticker`} value={query} onChange={(e) => setQuery(e.target.value)} autoComplete="off" />
        {loading && <Loader2 size={18} className="absolute right-4 top-1/2 -translate-y-1/2 animate-spin text-mute" />}
      </div>
      {error && <p className="mt-3 text-sm text-mute">{error}</p>}
      {results.length > 0 && (
        <ul className="mt-3 divide-y divide-line border-y border-line bg-white">
          {results.map((r) => (
            <li key={r.ticker} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
              <div className="min-w-0">
                <p className="truncate font-medium">{r.company_name}</p>
                <p className="num text-sm text-mute">{r.ticker}</p>
              </div>
              <div className="flex shrink-0 gap-2">
                {savedTickers.has(r.ticker)
                  ? <span className="inline-flex items-center gap-1.5 px-2 text-sm text-gain"><Check size={15} /> Saved</span>
                  : <button className="btn-line btn-sm" disabled={!!busy} onClick={act(r.ticker + 'a', () => addStock(r))}>{busy === r.ticker + 'a' ? 'Saving…' : 'Save'}</button>}
                <button className="btn-cobalt btn-sm" disabled={!!busy} onClick={act(r.ticker + 'r', () => research(r))}>{busy === r.ticker + 'r' ? 'Starting…' : 'Research'}</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
