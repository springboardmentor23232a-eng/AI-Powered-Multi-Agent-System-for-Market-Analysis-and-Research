import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AlertCircle } from 'lucide-react'
import { MARKETS, api, periodLabel } from '../api.js'
import { useData } from '../data.jsx'
import { fmtDateTime } from '../format.js'
import Page from '../components/Page.jsx'
import Status from '../components/Status.jsx'

export default function MarketDataPage() {
  const { prefs, saved } = useData()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [source, setSource] = useState(null)
  const [list, setList] = useState(null)
  const [ticker, setTicker] = useState(params.get('ticker') || '')
  const [market, setMarket] = useState(params.get('market') || prefs.market)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.marketSource().then(setSource).catch(() => {})
    api.collections().then(setList).catch((e) => setError(e.message))
  }, [])

  async function submit(e) {
    e.preventDefault()
    setError('')
    if (!ticker.trim()) return setError('Enter a ticker symbol to collect.')
    setBusy(true)
    try {
      const c = await api.collect({ ticker: ticker.trim(), market })
      navigate(`/dashboard/market-data/${c.collection_id}`)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  const pick = (symbol, m) => { setTicker(symbol); setMarket(m) }
  const sampleHere = source?.symbols?.filter((s) => s.market === market) ?? []
  const savedHere = saved.filter((s) => s.market === market)

  return (
    <Page title="Market data" aside={list?.length ? `${list.length} collected` : null}>
      {source && (
        <p className="mb-8 max-w-prose border-l-4 border-cobalt bg-cobalt/5 px-4 py-3 font-serif text-lg text-ink">
          {source.kind === 'sample'
            ? 'Data is currently collected from the bundled sample dataset. It is synthetic and meant for testing, so the prices are not real quotes.'
            : 'Data is collected live from Yahoo Finance through yfinance.'}
        </p>
      )}

      <section>
        <h2 className="mb-3 border-b border-ink pb-2 text-xl font-semibold tracking-tight">Collect data</h2>
        <form onSubmit={submit} className="grid gap-4 sm:grid-cols-[1fr_180px_auto] sm:items-end">
          <div>
            <label htmlFor="md-ticker" className="label">Ticker symbol</label>
            <input id="md-ticker" className="field" value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="For example TCS.BO or AAPL" autoComplete="off" />
          </div>
          <div>
            <label htmlFor="md-market" className="label">Market</label>
            <select id="md-market" className="field" value={market} onChange={(e) => setMarket(e.target.value)}>
              {MARKETS.map((m) => <option key={m.id} value={m.id}>{m.id}</option>)}
            </select>
          </div>
          <button className="btn-cobalt !py-3" disabled={busy}>{busy ? 'Collecting…' : 'Collect'}</button>
        </form>
        <p className="mt-2 text-sm text-mute">Covers {periodLabel(prefs.analysis_period).toLowerCase()} of daily prices, plus the company profile and financial statements when the source has them. Change the period under Preferences.</p>

        {error && (
          <p role="alert" className="mt-4 flex items-start gap-2.5 border-l-4 border-loss bg-loss/10 px-4 py-3 text-sm font-medium text-loss">
            <AlertCircle size={18} className="mt-px shrink-0" /> {error}
          </p>
        )}

        {savedHere.length > 0 && (
          <div className="mt-5">
            <p className="mb-2 text-sm font-medium">From your watchlist</p>
            <div className="flex flex-wrap gap-2">
              {savedHere.map((s) => <button key={s.saved_stock_id} onClick={() => pick(s.ticker, s.market)} className="btn-line btn-sm num">{s.ticker}</button>)}
            </div>
          </div>
        )}
        {sampleHere.length > 0 && (
          <div className="mt-5">
            <p className="mb-2 text-sm font-medium">Available in the sample dataset for {market}</p>
            <div className="flex flex-wrap gap-2">
              {sampleHere.map((s) => <button key={s.symbol} onClick={() => pick(s.symbol, s.market)} title={s.name} className="btn-line btn-sm num">{s.symbol}</button>)}
            </div>
          </div>
        )}
      </section>

      <section className="mt-14">
        <h2 className="mb-3 border-b border-ink pb-2 text-xl font-semibold tracking-tight">Collected data</h2>
        {list === null ? <p className="py-4 text-mute">Loading…</p> : list.length === 0 ? (
          <p className="py-4 text-mute">Nothing collected yet. Choose a ticker above and select Collect.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left">
              <thead className="text-sm text-mute">
                <tr>
                  <th className="py-2.5 pr-4 font-medium">Company</th><th className="py-2.5 pr-4 font-medium">Period</th>
                  <th className="py-2.5 pr-4 font-medium">Source</th><th className="py-2.5 pr-4 font-medium">Retrieved</th>
                  <th className="py-2.5 pr-4 font-medium">Rows kept</th><th className="py-2.5 pr-4 font-medium">Quality</th><th />
                </tr>
              </thead>
              <tbody className="divide-y divide-line border-y border-line">
                {list.map((c) => (
                  <tr key={c.collection_id}>
                    <td className="py-4 pr-4"><p className="font-medium">{c.company_name}</p><p className="num text-sm text-mute">{c.ticker}, {c.market}</p></td>
                    <td className="whitespace-nowrap py-4 pr-4">{periodLabel(c.analysis_period)}</td>
                    <td className="py-4 pr-4 text-sm">{c.source}</td>
                    <td className="num py-4 pr-4 text-sm">{fmtDateTime(c.retrieved_at)}</td>
                    <td className="num whitespace-nowrap py-4 pr-4">{c.rows_clean.toLocaleString()} <span className="text-mute">of {c.rows_raw.toLocaleString()}</span></td>
                    <td className="py-4 pr-4"><Status value={c.status} /></td>
                    <td className="py-4 text-right"><Link to={`/dashboard/market-data/${c.collection_id}`} className="btn-cobalt btn-sm">Open</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </Page>
  )
}
