import axios from 'axios';
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api', withCredentials: true, headers: { 'Content-Type': 'application/json' } });
api.interceptors.request.use((config) => {
  const unsafe = ['post', 'put', 'patch', 'delete'].includes((config.method || '').toLowerCase());
  if (unsafe) {
    const csrf = document.cookie.split('; ').find(row => row.startsWith('csrf_token='))?.split('=').slice(1).join('=');
    if (csrf) config.headers['X-CSRF-Token'] = decodeURIComponent(csrf);
  }
  return config;
});
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const requestUrl = error.config?.url || '';
    const isAuthenticationBootstrap = ['/auth/me', '/auth/login', '/auth/register', '/auth/google'].some((path) => requestUrl.endsWith(path));
    if (error.response?.status === 401 && !isAuthenticationBootstrap) {
      window.dispatchEvent(new Event('equitylens:session-expired'));
    }
    return Promise.reject(error);
  },
);
export default api;
