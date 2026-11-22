import { useMemo, useState } from 'react'
import { fmtDate, money, whole } from '../format.js'

const W = 1000, PH = 300, GAP = 14, VH = 56, H = PH + GAP + VH

export default function PriceChart({ bars, market }) {
  const [hover, setHover] = useState(null)
  const n = bars.length

  const g = useMemo(() => {
    const closes = bars.map((b) => b.close)
    const lo = Math.min(...closes), hi = Math.max(...closes)
    const span = hi - lo || 1
    const x = (i) => (n === 1 ? W / 2 : (i / (n - 1)) * W)
    const y = (v) => PH - 14 - ((v - lo) / span) * (PH - 28)
    const line = bars.map((b, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(b.close).toFixed(1)}`).join(' ')
    const vmax = Math.max(...bars.map((b) => b.volume)) || 1
    const bw = Math.max((W / n) * 0.7, 0.6)
    const vols = bars.map((b, i) => {
      const h = (b.volume / vmax) * VH
      const up = i === 0 || b.close >= bars[i - 1].close
      return { x: x(i) - bw / 2, y: PH + GAP + VH - h, w: bw, h, up }
    })
    return { lo, hi, x, y, line, area: `${line} L${x(n - 1)},${PH} L${x(0)},${PH} Z`, vols }
  }, [bars, n])

  const move = (clientX, el) => {
    const r = el.getBoundingClientRect()
    setHover(Math.round(Math.min(1, Math.max(0, (clientX - r.left) / r.width)) * (n - 1)))
  }
  const b = hover != null ? bars[hover] : bars[n - 1]
  const hx = hover != null ? (g.x(hover) / W) * 100 : null

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-baseline gap-x-5 gap-y-1 text-sm">
        <span className="font-semibold">{fmtDate(b.date)}</span>
        <span className="num text-mute">Open {money(b.open, market)}</span>
        <span className="num text-mute">High {money(b.high, market)}</span>
        <span className="num text-mute">Low {money(b.low, market)}</span>
        <span className="num font-semibold">Close {money(b.close, market)}</span>
        <span className="num text-mute">Volume {whole(b.volume)}</span>
      </div>
      <div className="relative cursor-crosshair select-none"
        onMouseMove={(e) => move(e.clientX, e.currentTarget)} onTouchMove={(e) => move(e.touches[0].clientX, e.currentTarget)}
        onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-[340px] w-full" role="img" aria-label="Closing price and volume">
          {[0.25, 0.5, 0.75].map((f) => <line key={f} x1="0" x2={W} y1={PH * f} y2={PH * f} stroke="#D9DCE3" strokeWidth="1" vectorEffect="non-scaling-stroke" />)}
          <path d={g.area} fill="#2430D6" fillOpacity="0.08" />
          <path d={g.line} fill="none" stroke="#2430D6" strokeWidth="2" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
          {g.vols.map((v, i) => <rect key={i} x={v.x} y={v.y} width={v.w} height={v.h} fill={v.up ? '#0B8A57' : '#D4302B'} fillOpacity="0.4" />)}
        </svg>
        <span className="num pointer-events-none absolute left-0 top-0 bg-paper/80 pr-2 text-xs text-mute">{money(g.hi, market)}</span>
        <span className="num pointer-events-none absolute left-0 text-xs text-mute" style={{ top: `${(PH / H) * 100 - 6}%` }}>{money(g.lo, market)}</span>
        {hover != null && (
          <>
            <span className="pointer-events-none absolute top-0 w-px bg-ink/40" style={{ left: `${hx}%`, height: `${(PH / H) * 100}%` }} />
            <span className="pointer-events-none absolute h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-cobalt shadow"
              style={{ left: `${hx}%`, top: `${(g.y(b.close) / H) * 100}%` }} />
          </>
        )}
      </div>
      <div className="mt-1 flex justify-between text-xs text-mute"><span>{fmtDate(bars[0].date)}</span><span>{fmtDate(bars[n - 1].date)}</span></div>
    </div>
  )
}
