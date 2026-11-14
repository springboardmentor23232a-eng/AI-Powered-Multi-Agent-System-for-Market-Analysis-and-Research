import { Link } from 'react-router-dom'
import { MARKETS, PERIODS, periodLabel } from '../api.js'
import { useAuth } from '../auth.jsx'
import { useData } from '../data.jsx'
import { fmtDate, greeting } from '../format.js'
import Page from '../components/Page.jsx'
import Status from '../components/Status.jsx'
import StockSearch from '../components/StockSearch.jsx'

function Section({ title, to, linkText, children }) {
  return (
    <section>
      <div className="mb-3 flex items-baseline justify-between border-b border-ink pb-2">
        <h2 className="text-xl font-semibold tracking-tight">{title}</h2>
        {to && <Link to={to} className="text-sm font-medium text-cobalt underline underline-offset-4">{linkText}</Link>}
      </div>
      {children}
    </section>
  )
}

export default function Overview() {
  const { user } = useAuth()
  const { prefs, saved, tasks, research } = useData()
  const market = MARKETS.find((m) => m.id === prefs.market)
  const period = PERIODS.find((p) => p.id === prefs.analysis_period)

  return (
    <Page>
      <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">{greeting()}, {user.full_name.split(' ')[0]}.</h1>
      <p className="mt-3 max-w-prose font-serif text-lg text-mute">
        You are searching {market.id} listings and looking back {period.phrase}.{' '}
        <Link to="/dashboard/preferences" className="text-cobalt underline underline-offset-4">Change this</Link>
      </p>

      <div className="mt-10"><StockSearch /></div>

      <div className="mt-14 grid gap-12 lg:grid-cols-2">
        <Section title="Recent research" to="/dashboard/research" linkText="See all">
          {tasks.length === 0 ? (
            <p className="py-4 text-mute">Nothing yet. Search for a company above and choose Research to run your first.</p>
          ) : (
            <ul className="divide-y divide-line">
              {tasks.slice(0, 5).map((t) => (
                <li key={t.task_id} className="flex items-center justify-between gap-4 py-3.5">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{t.company_name}</p>
                    <p className="num text-sm text-mute">{t.ticker}, {periodLabel(t.analysis_period)}, {fmtDate(t.created_at)}</p>
                  </div>
                  <Status value={t.status} />
                </li>
              ))}
            </ul>
          )}
        </Section>

        <Section title="Your watchlist" to="/dashboard/watchlist" linkText="Manage">
          {saved.length === 0 ? (
            <p className="py-4 text-mute">No saved stocks. Search above and choose Save to keep a company here.</p>
          ) : (
            <ul className="divide-y divide-line">
              {saved.slice(0, 6).map((s) => (
                <li key={s.saved_stock_id} className="flex items-center justify-between gap-4 py-3">
                  <div className="min-w-0">
                    <p className="num font-semibold">{s.ticker}</p>
                    <p className="truncate text-sm text-mute">{s.company_name}</p>
                  </div>
                  <button className="btn-line btn-sm" onClick={() => research(s)}>Research</button>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>
    </Page>
  )
}
