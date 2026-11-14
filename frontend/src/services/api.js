import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Crucial for sending/receiving HTTP-only JWT cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authService = {
  register: async (payload) => {
    const response = await api.post('/api/auth/register', payload);
    return response.data;
  },

  login: async (credentials) => {
    const response = await api.post('/api/auth/login', credentials);
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/api/auth/logout');
    return response.data;
  },

  getMe: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },

  getGoogleAuthUrl: () => `${API_BASE_URL || 'http://localhost:8000'}/api/auth/google/login`,
  getAppleAuthUrl: () => `${API_BASE_URL || 'http://localhost:8000'}/api/auth/apple/login`,
};

export const stockService = {
  search: async (query) => {
    const response = await api.get(`/api/stocks/search`, {
      params: { q: query },
    });
    return response.data;
  },
};

export const dashboardService = {
  getWatchlist: async () => {
    const response = await api.get('/api/dashboard/watchlist');
    return response.data;
  },

  addToWatchlist: async (ticker) => {
    const response = await api.post('/api/dashboard/watchlist', { ticker });
    return response.data;
  },

  removeFromWatchlist: async (savedStockId) => {
    const response = await api.delete(`/api/dashboard/watchlist/${savedStockId}`);
    return response.data;
  },

  getRecentResearch: async () => {
    const response = await api.get('/api/dashboard/recent-research');
    return response.data;
  },

  createResearchTask: async (taskData) => {
    const response = await api.post('/api/dashboard/research', taskData);
    return response.data;
  },

  getResearchReport: async (taskId) => {
    const response = await api.get(`/api/dashboard/research/${taskId}/report`);
    return response.data;
  },

  getPreferences: async () => {
    const response = await api.get('/api/dashboard/preferences');
    return response.data;
  },

  updatePreferences: async (preferences) => {
    const response = await api.put('/api/dashboard/preferences', preferences);
    return response.data;
  },
};

export default api;
