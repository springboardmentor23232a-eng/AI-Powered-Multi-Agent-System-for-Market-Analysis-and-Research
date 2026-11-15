import { vi } from 'vitest'

// A tiny in-memory imitation of the backend, used by the frontend tests.
// It answers fetch() calls the same way the real FastAPI endpoints do.
export function installFakeBackend() {
  const state = {
    users: {}, // email -> password
    preferences: { default_market: 'NSE', analysis_period: '1Y', updated_at: '2026-01-01T00:00:00Z' },
    watchlist: [],
    nextId: 1,
  }
  const json = (status, body) =>
    Promise.resolve(new Response(body === null ? null : JSON.stringify(body), { status }))

  const fetchMock = vi.fn((url, { method = 'GET', headers = {}, body } = {}) => {
    const path = new URL(url).pathname.replace('/api/v1', '')
    const authed = headers.Authorization === 'Bearer valid-token'

    if (path === '/auth/register' && method === 'POST') {
      const { email, password } = JSON.parse(body)
      if (state.users[email]) return json(409, { detail: 'Email is already registered' })
      state.users[email] = password
      return json(201, { user_id: 1, email, created_at: '2026-01-01T00:00:00Z' })
    }
    if (path === '/auth/login' && method === 'POST') {
      const form = new URLSearchParams(body)
      if (state.users[form.get('username')] !== form.get('password'))
        return json(401, { detail: 'Incorrect email or password' })
      return json(200, { access_token: 'valid-token', token_type: 'bearer', expires_in: 3600 })
    }
    if (!authed) return json(401, { detail: 'Could not validate credentials' })

    if (path === '/auth/me') return json(200, { user_id: 1, email: 'alice@example.com', created_at: '2026-01-01T00:00:00Z' })
    if (path === '/users/me/preferences') {
      if (method === 'PUT') Object.assign(state.preferences, JSON.parse(body))
      return json(200, state.preferences)
    }
    if (path === '/watchlist' && method === 'GET') return json(200, state.watchlist)
    if (path === '/watchlist' && method === 'POST') {
      const { ticker, market } = JSON.parse(body)
      if (state.watchlist.some((s) => s.ticker === ticker && s.market === market))
        return json(409, { detail: `${ticker} (${market}) is already saved` })
      const stock = { saved_stock_id: state.nextId++, ticker, market, created_at: '2026-01-01T00:00:00Z' }
      state.watchlist.unshift(stock)
      return json(201, stock)
    }
    if (path.startsWith('/watchlist/') && method === 'DELETE') {
      const id = Number(path.split('/')[2])
      state.watchlist = state.watchlist.filter((s) => s.saved_stock_id !== id)
      return json(204, null)
    }
    if (path === '/research/history') return json(200, { items: [], total: 0, limit: 20, offset: 0 })
    return json(404, { detail: 'Not Found' })
  })

  vi.spyOn(globalThis, 'fetch').mockImplementation(fetchMock)
  return { state, fetchMock }
}

export function storeValidSession() {
  localStorage.setItem('sra.session', JSON.stringify({ token: 'valid-token', expiresAt: Date.now() + 3_600_000 }))
}
