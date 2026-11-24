import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true, // sends HttpOnly refresh cookie
})

// Access token lives in memory only (set by AuthContext via setAccessTokenGetter)
let getAccessToken = () => null
let onSessionExpired = () => {}
let refreshPromise = null

export function configureAuth({ getToken, onExpired }) {
  getAccessToken = getToken
  onSessionExpired = onExpired
}

export function refreshSession() {
  if (!refreshPromise) {
    refreshPromise = api
      .post('/auth/refresh')
      .then(({ data }) => {
        window.dispatchEvent(new CustomEvent('netshield:token', { detail: data.access_token }))
        return data
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

api.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    const isAuthEndpoint =
      original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh')
    if (error.response?.status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true
      let data
      try {
        data = await refreshSession()
      } catch (refreshError) {
        const status = refreshError.response?.status
        if (status === 401 || status === 403) onSessionExpired()
        return Promise.reject(refreshError)
      }
      original.headers.Authorization = `Bearer ${data.access_token}`
      return api(original)
    }
    return Promise.reject(error)
  },
)

export function apiError(err, fallback = 'Request failed') {
  const detail = err?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
  }
  if (typeof detail === 'string') return detail
  return fallback
}

export default api
