import axios from 'axios';
const API_BASE_URL = 'http://127.0.0.1:8000';
const api = axios.create({
  baseURL: API_BASE_URL,
});
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
export const registerUser = (userData) => api.post('/users/', userData);
export const loginUser = (credentials) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);
  return api.post('/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
};
export const getMyProfile = () => api.get('/users/me');
export const getPreferences = () => api.get('/users/preferences');
export const updatePreferences = (prefs) => api.put('/users/preferences', prefs);
export const getWatchlist = () => api.get('/stocks/');
export const saveStock = (ticker) => api.post('/stocks/save/', { ticker });
export const deleteStock = (id) => api.delete(`/stocks/${id}`);
export const runResearch = (data) => api.post('/research/', data);
export const getResearchHistory = () => api.get('/research/');
export default api;