export const fmtDate = (d) =>
  new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

export function greeting() {
  const h = new Date().getHours()
  return h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening'
}

export const fmtDateTime = (d) =>
  new Date(d).toLocaleString('en-IN', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' })

const SYMBOL = { NSE: '₹', BSE: '₹', NASDAQ: '$', NYSE: '$' }
export const money = (v, market) =>
  v == null ? '-' : (SYMBOL[market] || '') + Number(v).toLocaleString(SYMBOL[market] === '₹' ? 'en-IN' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const whole = (v) => (v == null ? '-' : Number(v).toLocaleString('en-US'))
export const compact = (v) =>
  v == null ? '-' : Math.abs(v) >= 1e5 ? new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 2 }).format(v) : Number(v).toLocaleString('en-US', { maximumFractionDigits: 2 })
