// Small wrapper around fetch() that talks to the FastAPI backend.
// Every function returns parsed JSON or throws an ApiError with a readable message.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// FastAPI returns errors as {detail: "text"} or, for validation errors,
// {detail: [{loc: [...], msg: "..."}]}. Turn either shape into one sentence.
function errorMessageFrom(body, status) {
  const detail = body?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((item) => {
        const field = item.loc?.filter((part) => part !== 'body').join('.')
        const msg = (item.msg ?? 'Invalid value').replace(/^Value error, /, '')
        return field ? `${field}: ${msg}` : msg
      })
      .join('; ')
  }
  return `Request failed (HTTP ${status})`
}

async function request(path, { method = 'GET', token, json, form } = {}) {
  const headers = {}
  let body
  if (token) headers.Authorization = `Bearer ${token}`
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(json)
  } else if (form !== undefined) {
    body = new URLSearchParams(form)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { method, headers, body })
  } catch {
    throw new ApiError('Cannot reach the server. Is the backend running?', 0)
  }

  if (response.status === 204) return null
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new ApiError(errorMessageFrom(data, response.status), response.status)
  return data
}

export const api = {
  register: (email, password) =>
    request('/auth/register', { method: 'POST', json: { email, password } }),
  // OAuth2 password flow: the email goes in the "username" form field.
  login: (email, password) =>
    request('/auth/login', { method: 'POST', form: { username: email, password } }),
  me: (token) => request('/auth/me', { token }),

  getPreferences: (token) => request('/users/me/preferences', { token }),
  updatePreferences: (token, changes) =>
    request('/users/me/preferences', { method: 'PUT', token, json: changes }),

  getWatchlist: (token) => request('/watchlist', { token }),
  addToWatchlist: (token, ticker, market) =>
    request('/watchlist', { method: 'POST', token, json: { ticker, market } }),
  removeFromWatchlist: (token, savedStockId) =>
    request(`/watchlist/${savedStockId}`, { method: 'DELETE', token }),

  getResearchHistory: (token, { limit = 20, offset = 0 } = {}) =>
    request(`/research/history?limit=${limit}&offset=${offset}`, { token }),
}
