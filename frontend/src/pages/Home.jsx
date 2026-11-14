import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../auth.jsx'
import Mark from '../components/Mark.jsx'
import PriceLine from '../components/PriceLine.jsx'

const POINTS = [
  { title: 'Keep a watchlist', text: 'Search NSE, BSE, NASDAQ and NYSE listings by company name or ticker, save the ones you follow, and start research on any of them in one click.' },
  { title: 'Choose your market and time frame', text: 'Pick where you research and how far back to look, from one month to five years. Every new research uses what you chose.' },
  { title: 'Find your past research', text: 'Each research you start is saved with its date and status, so you can return to the report whenever you need it.' },
]

export default function Home() {
  const { user } = useAuth()
  const [fx, setFx] = useState(null)
  const track = (clientX, el) => {
    const r = el.getBoundingClientRect()
    setFx((clientX - r.left) / r.width)
  }

  return (
    <div>
      <section
        className="on-cobalt grid-paper relative flex min-h-[100svh] flex-col overflow-hidden bg-cobalt text-white"
        onMouseMove={(e) => track(e.clientX, e.currentTarget)}
        onTouchMove={(e) => track(e.touches[0].clientX, e.currentTarget)}
        onMouseLeave={() => setFx(null)}
      >
        <PriceLine fx={fx} />
        <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6 sm:px-10">
          <Mark light />
          <nav className="flex items-center gap-2">
            {user ? (
              <Link to="/dashboard" className="btn-white">Open dashboard</Link>
            ) : (
              <>
                <Link to="/login" className="btn-outline-white">Login</Link>
                <Link to="/register" className="btn-white">Register</Link>
              </>
            )}
          </nav>
        </header>

        <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 items-start px-6 pb-24 pt-10 sm:px-10 lg:pt-16">
          <div className="max-w-3xl">
            <h1 className="text-[clamp(2.75rem,7vw,5.75rem)] font-extrabold leading-[0.96] tracking-[-0.035em]">
              Look into any stock, and keep what you find.
            </h1>
            <p className="mt-7 max-w-xl font-serif text-xl leading-relaxed text-white/85">
              Build a watchlist, choose how far back to look, and run research on the companies you care about. Every report stays in your account.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              {user ? (
                <Link to="/dashboard" className="btn-white !px-6 !py-3">Open dashboard</Link>
              ) : (
                <>
                  <Link to="/register" className="btn-white !px-6 !py-3">Create an account</Link>
                  <Link to="/login" className="btn-outline-white !px-6 !py-3">Login</Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-20 sm:px-10">
        <h2 className="max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">What you can do here</h2>
        <div className="mt-10 border-b border-line">
          {POINTS.map((p) => (
            <div key={p.title} className="grid gap-3 border-t border-line py-8 md:grid-cols-[1fr_1.6fr] md:gap-10">
              <h3 className="text-2xl font-semibold tracking-tight">{p.title}</h3>
              <p className="max-w-prose font-serif text-lg leading-relaxed text-mute">{p.text}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-4 px-6 py-8 text-sm text-mute sm:px-10">
          <span>ORIONNEX, a multi-agent stock research analyst</span>
          {!user && (
            <span className="flex gap-5">
              <Link to="/login" className="hover:text-ink">Login</Link>
              <Link to="/register" className="hover:text-ink">Register</Link>
            </span>
          )}
        </div>
      </footer>
    </div>
  )
}
