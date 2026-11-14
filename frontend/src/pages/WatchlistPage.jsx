import { useData } from '../data.jsx'
import { fmtDate } from '../format.js'
import Page from '../components/Page.jsx'
import StockSearch from '../components/StockSearch.jsx'

export default function WatchlistPage() {
  const { saved, removeStock, research } = useData()
  return (
    <Page title="Watchlist" aside={saved.length ? `${saved.length} saved` : null}>
      <StockSearch placeholder="Find a company to save" />
      <div className="mt-10">
        {saved.length === 0 ? (
          <p className="border-t border-ink py-6 text-mute">Your watchlist is empty. Search for a company above and choose Save.</p>
        ) : (
          <ul className="divide-y divide-line border-y border-ink">
            {saved.map((s) => (
              <li key={s.saved_stock_id} className="grid items-center gap-x-6 gap-y-3 py-4 sm:grid-cols-[1fr_auto]">
                <div className="min-w-0">
                  <p className="flex flex-wrap items-baseline gap-x-3">
                    <span className="num text-xl font-semibold">{s.ticker}</span>
                    <span className="text-sm font-medium text-mute">{s.market}</span>
                  </p>
                  <p className="truncate text-mute">{s.company_name}, saved {fmtDate(s.created_at)}</p>
                </div>
                <div className="flex items-center gap-3">
                  <button className="btn-cobalt btn-sm" onClick={() => research(s)}>Research</button>
                  <button className="text-sm font-medium text-mute underline underline-offset-4 hover:text-loss" onClick={() => removeStock(s)}>Remove</button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Page>
  )
}
