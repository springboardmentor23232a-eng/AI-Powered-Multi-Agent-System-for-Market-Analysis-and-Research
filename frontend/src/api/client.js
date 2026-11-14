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
    const isAuthEndpoint = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh')
    if (error.response?.status === 401 && !original._retried && !isAuthEndpoint) {
      original._retried = true
      try {
        if (!refreshPromise) {
          refreshPromise = api.post('/auth/refresh').finally(() => {
            refreshPromise = null
          })
        }
        const { data } = await refreshPromise
        window.dispatchEvent(new CustomEvent('netshield:token', { detail: data.access_token }))
        original.headers.Authorization = `Bearer ${data.access_token}`
        return api(original)
      } catch {
        onSessionExpired()
      }
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
