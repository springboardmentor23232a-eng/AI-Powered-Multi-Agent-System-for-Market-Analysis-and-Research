async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch('/api' + path, {
    method,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const d = data?.detail
    const message = Array.isArray(d)
      ? d.map((e) => e.msg.replace(/^Value error, /, '')).join('. ')
      : d || 'Something went wrong'
    if (res.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event('auth:expired'))
    const err = new Error(message)
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  register: (b) => request('/auth/register', { method: 'POST', body: b }),
  login: (b) => request('/auth/login', { method: 'POST', body: b }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  preferences: () => request('/preferences'),
  savePreferences: (b) => request('/preferences', { method: 'PUT', body: b }),
  search: (q, market) => request(`/stocks/search?q=${encodeURIComponent(q)}&market=${market}`),
  watchlist: () => request('/watchlist'),
  addStock: (b) => request('/watchlist', { method: 'POST', body: b }),
  removeStock: (id) => request(`/watchlist/${id}`, { method: 'DELETE' }),
  history: () => request('/research'),
  report: (id) => request(`/research/${id}`),
  startResearch: (b) => request('/research', { method: 'POST', body: b }),
}

export const MARKETS = [
  { id: 'NSE', name: 'National Stock Exchange of India', region: 'India' },
  { id: 'BSE', name: 'BSE Ltd.', region: 'India' },
  { id: 'NASDAQ', name: 'NASDAQ', region: 'United States' },
  { id: 'NYSE', name: 'New York Stock Exchange', region: 'United States' },
]
export const PERIODS = [
  { id: '1M', label: '1 Month', phrase: '1 month' },
  { id: '3M', label: '3 Months', phrase: '3 months' },
  { id: '6M', label: '6 Months', phrase: '6 months' },
  { id: '1Y', label: '1 Year', phrase: '1 year' },
  { id: '5Y', label: '5 Years', phrase: '5 years' },
]
export const periodLabel = (id) => PERIODS.find((p) => p.id === id)?.label ?? id
