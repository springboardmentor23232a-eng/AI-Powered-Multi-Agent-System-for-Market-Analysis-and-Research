import { useEffect, useState } from 'react'
import { MARKETS, PERIODS } from '../api.js'
import { useData } from '../data.jsx'
import Page from '../components/Page.jsx'

export default function PreferencesPage() {
  const { prefs, savePrefs } = useData()
  const [draft, setDraft] = useState(prefs)
  const [saving, setSaving] = useState(false)
  useEffect(() => setDraft(prefs), [prefs])
  const dirty = draft.market !== prefs.market || draft.analysis_period !== prefs.analysis_period
  const period = PERIODS.find((p) => p.id === draft.analysis_period)

  async function save() {
    setSaving(true)
    await savePrefs(draft)
    setSaving(false)
  }

  return (
    <Page title="Preferences">
      <div className="grid gap-14 lg:grid-cols-[1.2fr_1fr]">
        <section>
          <h2 id="market-label" className="mb-3 border-b border-ink pb-2 text-xl font-semibold tracking-tight">Market</h2>
          <div role="radiogroup" aria-labelledby="market-label" className="divide-y divide-line">
            {MARKETS.map((m) => {
              const on = draft.market === m.id
              return (
                <button key={m.id} role="radio" aria-checked={on} onClick={() => setDraft({ ...draft, market: m.id })}
                  className="flex w-full items-center gap-5 py-4 text-left">
                  <span className={'grid h-5 w-5 shrink-0 place-items-center rounded-full border-2 ' + (on ? 'border-cobalt' : 'border-line')}>
                    {on && <span className="h-2.5 w-2.5 rounded-full bg-cobalt" />}
                  </span>
                  <span className={'w-20 text-2xl font-semibold tracking-tight ' + (on ? 'text-cobalt' : '')}>{m.id}</span>
                  <span className="text-mute">{m.name}, {m.region}</span>
                </button>
              )
            })}
          </div>
        </section>

        <section>
          <h2 id="period-label" className="mb-3 border-b border-ink pb-2 text-xl font-semibold tracking-tight">Analysis period</h2>
          <div role="radiogroup" aria-labelledby="period-label" className="flex flex-wrap gap-2 pt-2">
            {PERIODS.map((p) => (
              <button key={p.id} role="radio" aria-checked={draft.analysis_period === p.id} onClick={() => setDraft({ ...draft, analysis_period: p.id })}
                className={'rounded-md border px-4 py-2.5 text-sm font-semibold transition-colors ' + (draft.analysis_period === p.id ? 'border-ink bg-ink text-white' : 'border-line bg-white hover:border-ink')}>
                {p.label}
              </button>
            ))}
          </div>

          <p className="mt-8 max-w-sm font-serif text-lg leading-relaxed text-mute">
            New research will use {draft.market} listings and about {period.phrase} of price history. Stocks already on your watchlist are not affected.
          </p>
          <button className="btn-cobalt mt-6" disabled={!dirty || saving} onClick={save}>
            {saving ? 'Saving…' : 'Save preferences'}
          </button>
        </section>
      </div>
    </Page>
  )
}
