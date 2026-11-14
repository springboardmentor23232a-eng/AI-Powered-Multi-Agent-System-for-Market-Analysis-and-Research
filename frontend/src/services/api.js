import axios from 'axios';

// Base Axios instance pointing to the FastAPI backend
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Automatically inject JWT Bearer Token into headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle expired/invalid tokens cleanly
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    return Promise.reject(error);
  }
);

// Authentication API methods (Module 1 Guide, Sections 1, 2, 3)
export const authAPI = {
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },
  googleLogin: async (googleData) => {
    const response = await api.post('/auth/google', googleData);
    return response.data;
  },
  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Real-Time Market Data via Yahoo Finance (yfinance)
export const marketAPI = {
  getTickerTape: async () => {
    const response = await api.get('/market/ticker-tape');
    return response.data;
  },
  getQuote: async (ticker, market = 'NSE') => {
    const response = await api.get(`/market/quote/${ticker}`, {
      params: { market },
    });
    return response.data;
  },
  getAnalysis: async (ticker, market = 'NSE', period = '1y') => {
    const response = await api.get(`/market/analysis/${ticker}`, {
      params: { market, period },
    });
    return response.data;
  },
  getHistory: async (ticker, market = 'NSE', period = '1y') => {
    const response = await api.get(`/market/history/${ticker}`, {
      params: { market, period },
    });
    return response.data;
  },
  getPopular: async (market = 'NSE') => {
    const response = await api.get('/market/popular', {
      params: { market },
    });
    return response.data;
  },
};

// Watchlist API (Module 1 Guide, Section 5)
export const watchlistAPI = {
  getWatchlist: async () => {
    const response = await api.get('/watchlist');
    return response.data;
  },
  addToWatchlist: async (stockData) => {
    const response = await api.post('/watchlist', stockData);
    return response.data;
  },
  removeFromWatchlist: async (ticker) => {
    const response = await api.delete(`/watchlist/${ticker}`);
    return response.data;
  },
};

// User Preferences API (Module 1 Guide, Section 6)
export const preferencesAPI = {
  getPreferences: async () => {
    const response = await api.get('/preferences');
    return response.data;
  },
  updatePreferences: async (preferences) => {
    const response = await api.put('/preferences', preferences);
    return response.data;
  },
};

// Research Tasks API (Module 1 Guide, Section 4)
export const researchAPI = {
  getHistory: async () => {
    const response = await api.get('/research/history');
    return response.data;
  },
  startTask: async (taskData) => {
    const response = await api.post('/research/start', taskData);
    return response.data;
  },
};

export default api;
