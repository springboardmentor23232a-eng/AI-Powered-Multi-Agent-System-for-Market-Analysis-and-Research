import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, periodLabel } from '../api.js'
import { compact, fmtDate, fmtDateTime, money, whole } from '../format.js'
import Page from '../components/Page.jsx'
import PriceChart from '../components/PriceChart.jsx'
import Status from '../components/Status.jsx'

const TABS = ['Prices', 'Profile', 'Financials', 'Data quality']
const STATEMENTS = { income_statement: 'Income statement', balance_sheet: 'Balance sheet', cash_flow: 'Cash flow' }
const PROFILE_LABELS = { name: 'Name', exchange: 'Exchange', currency: 'Currency', country: 'Country', sector: 'Sector', industry: 'Industry', website: 'Website', employees: 'Employees', market_cap: 'Market cap' }

function Stat({ label, value }) {
  return (
    <div className="border-t border-ink pt-2">
      <p className="text-sm text-mute">{label}</p>
      <p className="num mt-0.5 text-xl font-semibold">{value}</p>
    </div>
  )
}

function Financials({ data }) {
  const keys = Object.keys(STATEMENTS).filter((k) => data?.[k] && Object.keys(data[k]).length)
  const [which, setWhich] = useState(keys[0])
  if (!keys.length) return <p className="py-4 text-mute">This source has no financial statements for the company.</p>
  const byYear = data[which]
  const years = Object.keys(byYear).sort().reverse()
  const items = [...new Set(years.flatMap((y) => Object.keys(byYear[y])))]
  return (
    <div>
      <div className="mb-4 flex flex-wrap gap-2">
        {keys.map((k) => (
          <button key={k} onClick={() => setWhich(k)}
            className={'rounded-md border px-3.5 py-2 text-sm font-semibold ' + (which === k ? 'border-ink bg-ink text-white' : 'border-line bg-white hover:border-ink')}>
            {STATEMENTS[k]}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-left">
          <thead className="border-b border-ink text-sm text-mute">
            <tr><th className="py-2.5 pr-4 font-medium">Fiscal year ending</th>{years.map((y) => <th key={y} className="num py-2.5 pl-4 text-right font-medium">{fmtDate(y)}</th>)}</tr>
          </thead>
          <tbody className="divide-y divide-line border-b border-line">
            {items.map((it) => (
              <tr key={it}>
                <td className="py-3 pr-4">{it}</td>
                {years.map((y) => <td key={y} className="num py-3 pl-4 text-right">{compact(byYear[y][it])}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function CollectionDetail() {
  const { id } = useParams()
  const [col, setCol] = useState(null)
  const [bars, setBars] = useState(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('Prices')

  useEffect(() => {
    Promise.all([api.collection(id), api.prices(id)])
      .then(([c, p]) => { setCol(c); setBars(p) })
      .catch((e) => setError(e.message))
  }, [id])

  if (error) return <Page><p className="text-loss">{error}</p><Link to="/dashboard/market-data" className="mt-4 inline-block text-cobalt underline underline-offset-4">Back to market data</Link></Page>
  if (!col || !bars) return <Page><p className="text-mute">Loading…</p></Page>

  const m = col.market
  const last = bars[bars.length - 1]
  const hi = Math.max(...bars.map((b) => b.high)), lo = Math.min(...bars.map((b) => b.low))
  const profile = col.profile
  const issues = col.report.issues

  return (
    <Page>
      <Link to="/dashboard/market-data" className="text-sm font-medium text-cobalt underline underline-offset-4">All market data</Link>
      <div className="mt-4 flex flex-wrap items-end justify-between gap-x-8 gap-y-3">
        <div>
          <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{col.company_name}</h1>
          <p className="num mt-2 text-mute">{col.ticker}, {m}, {periodLabel(col.analysis_period)} of data</p>
        </div>
        <div className="text-sm">
          <p className="font-medium">{col.source}</p>
          <p className="num text-mute">Retrieved {fmtDateTime(col.retrieved_at)}</p>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
        <Stat label="Latest close" value={money(last.close, m)} />
        <Stat label="Period high" value={money(hi, m)} />
        <Stat label="Period low" value={money(lo, m)} />
        <Stat label="Trading days" value={whole(bars.length)} />
      </div>

      <div className="mt-10"><PriceChart bars={bars} market={m} /></div>

      <div className="mt-12 flex flex-wrap gap-1 border-b border-line" role="tablist">
        {TABS.map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
            className={'-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold ' + (tab === t ? 'border-cobalt text-cobalt' : 'border-transparent text-mute hover:text-ink')}>
            {t}
          </button>
        ))}
      </div>

      <div className="pt-6">
        {tab === 'Prices' && (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-left">
              <thead className="border-b border-ink text-sm text-mute">
                <tr><th className="py-2.5 pr-4 font-medium">Date</th>{['Open', 'High', 'Low', 'Close', 'Volume'].map((h) => <th key={h} className="py-2.5 pl-4 text-right font-medium">{h}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-line border-b border-line">
                {bars.slice(-25).reverse().map((b) => (
                  <tr key={b.date} className="num">
                    <td className="py-2.5 pr-4">{fmtDate(b.date)}</td>
                    <td className="py-2.5 pl-4 text-right">{money(b.open, m)}</td><td className="py-2.5 pl-4 text-right">{money(b.high, m)}</td>
                    <td className="py-2.5 pl-4 text-right">{money(b.low, m)}</td><td className="py-2.5 pl-4 text-right font-semibold">{money(b.close, m)}</td>
                    <td className="py-2.5 pl-4 text-right">{whole(b.volume)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-3 text-sm text-mute">Showing the latest 25 of {bars.length} trading days.</p>
          </div>
        )}

        {tab === 'Profile' && (!profile ? <p className="py-4 text-mute">This source has no profile for the company.</p> : (
          <div>
            <dl className="grid max-w-2xl grid-cols-[160px_1fr] gap-y-3">
              {Object.keys(PROFILE_LABELS).filter((k) => profile[k] != null).map((k) => (
                <div key={k} className="contents">
                  <dt className="text-mute">{PROFILE_LABELS[k]}</dt>
                  <dd className="num">{k === 'market_cap' ? compact(profile[k]) : k === 'employees' ? whole(profile[k]) : String(profile[k])}</dd>
                </div>
              ))}
            </dl>
            {profile.summary && <p className="mt-6 max-w-prose font-serif text-[17px] leading-relaxed">{profile.summary}</p>}
          </div>
        ))}

        {tab === 'Financials' && <Financials data={col.financials} />}

        {tab === 'Data quality' && (
          <div>
            <p className="flex items-center gap-3 text-lg"><Status value={col.status} />
              <span className="num text-mute">{col.rows_raw.toLocaleString()} rows received, {col.rows_clean.toLocaleString()} kept</span></p>
            {issues.length === 0 ? (
              <p className="mt-4 max-w-prose font-serif text-lg text-mute">No missing values, duplicate dates or inconsistent prices were found.</p>
            ) : (
              <table className="mt-5 w-full min-w-[560px] text-left">
                <thead className="border-b border-ink text-sm text-mute">
                  <tr><th className="py-2.5 pr-4 font-medium">Check</th><th className="py-2.5 pr-4 font-medium">Rows</th><th className="py-2.5 pr-4 font-medium">Action</th><th className="py-2.5 font-medium">Example dates</th></tr>
                </thead>
                <tbody className="divide-y divide-line border-b border-line">
                  {issues.map((i) => (
                    <tr key={i.check}>
                      <td className="py-3 pr-4 font-medium">{i.label}</td><td className="num py-3 pr-4">{i.count}</td>
                      <td className="py-3 pr-4">{i.action}</td><td className="num py-3 text-sm text-mute">{i.examples.map(fmtDate).join(', ') || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </Page>
  )
}
