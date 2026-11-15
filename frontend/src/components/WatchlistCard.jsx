import { useEffect, useState } from 'react'

import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { useApiErrorHandler } from '../auth/useApiErrorHandler'
import { MARKETS, TICKER_PATTERN } from '../constants'
import { Alert, Button, Card, fieldBaseClass } from './ui'

export default function WatchlistCard() {
  const { token } = useAuth()
  const handleError = useApiErrorHandler()

  const [stocks, setStocks] = useState(null)
  const [ticker, setTicker] = useState('')
  const [market, setMarket] = useState('NSE')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    // Load the list, and pre-select the user's preferred market in the form.
    Promise.all([api.getWatchlist(token), api.getPreferences(token)])
      .then(([savedStocks, preferences]) => {
        setStocks(savedStocks)
        setMarket(preferences.default_market)
      })
      .catch((err) => setError(handleError(err)))
  }, [token, handleError])

  async function handleAdd(event) {
    event.preventDefault()
    setError('')
    const cleaned = ticker.trim().toUpperCase()
    if (!TICKER_PATTERN.test(cleaned)) {
      return setError("Ticker may contain only letters, digits, '.', '-' or '&' (max 20 characters)")
    }
    setBusy(true)
    try {
      const added = await api.addToWatchlist(token, cleaned, market)
      setStocks((current) => [added, ...(current ?? [])])
      setTicker('')
    } catch (err) {
      setError(handleError(err))
    } finally {
      setBusy(false)
    }
  }

  async function handleRemove(stock) {
    setError('')
    try {
      await api.removeFromWatchlist(token, stock.saved_stock_id)
      setStocks((current) => current.filter((s) => s.saved_stock_id !== stock.saved_stock_id))
    } catch (err) {
      setError(handleError(err))
    }
  }

  return (
    <Card
      title="Watchlist"
      description="Stocks you want to follow. The ticker format is checked now; checking that the company exists comes with market data in Module 2."
    >
      <form onSubmit={handleAdd} className="flex gap-2">
        <input aria-label="Ticker symbol" placeholder="e.g. RELIANCE" className={`${fieldBaseClass} min-w-0 flex-1 uppercase`}
          value={ticker} onChange={(e) => setTicker(e.target.value)} maxLength={20} />
        <select aria-label="Market" className={fieldBaseClass} value={market}
          onChange={(e) => setMarket(e.target.value)}>
          {MARKETS.map((m) => <option key={m.value} value={m.value}>{m.value}</option>)}
        </select>
        <Button type="submit" disabled={busy || !ticker.trim()}>Add</Button>
      </form>

      <div className="mt-3"><Alert>{error}</Alert></div>

      {stocks === null ? (
        <p className="mt-3 text-sm text-slate-500">Loading…</p>
      ) : stocks.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">Your watchlist is empty.</p>
      ) : (
        <ul className="mt-3 divide-y divide-slate-100" aria-label="Saved stocks">
          {stocks.map((stock) => (
            <li key={stock.saved_stock_id} className="flex items-center justify-between py-2">
              <span>
                <span className="font-medium">{stock.ticker}</span>
                <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{stock.market}</span>
              </span>
              <Button variant="danger" onClick={() => handleRemove(stock)}
                aria-label={`Remove ${stock.ticker} (${stock.market})`}>
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  )
}
