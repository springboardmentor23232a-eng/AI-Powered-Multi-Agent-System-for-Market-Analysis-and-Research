import { useMemo } from 'react'

// A fixed, illustrative price path (not real data). The marker follows the pointer.
function series(n = 72) {
  let s = 11
  const rand = () => {
    s = (s + 0x6d2b79f5) | 0
    let t = Math.imul(s ^ (s >>> 15), 1 | s)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  let v = 0
  const out = []
  for (let i = 0; i < n; i++) { v += (rand() - 0.4) * 7; out.push(v) }
  const min = Math.min(...out), max = Math.max(...out)
  return out.map((x) => 90 - ((x - min) / (max - min)) * 38)
}

export default function PriceLine({ fx = null }) {
  const ys = useMemo(() => series(), [])
  const n = ys.length
  const line = 'M' + ys.map((y, i) => `${(i / (n - 1)) * 100},${y.toFixed(2)}`).join(' L')
  const idx = fx == null ? null : Math.round(Math.min(1, Math.max(0, fx)) * (n - 1))

  return (
    <div className="pointer-events-none absolute inset-0" aria-hidden="true">
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="reveal h-full w-full">
        <path d={`${line} L100,100 L0,100 Z`} fill="rgba(255,255,255,0.09)" />
        <path d={line} fill="none" stroke="#fff" strokeWidth="2.5" vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
      </svg>
      {idx != null && (
        <>
          <span className="absolute bottom-0 w-px bg-white/40" style={{ left: `${(idx / (n - 1)) * 100}%`, top: `${ys[idx]}%` }} />
          <span className="absolute h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-mark ring-4 ring-white/30" style={{ left: `${(idx / (n - 1)) * 100}%`, top: `${ys[idx]}%` }} />
        </>
      )}
    </div>
  )
}
