import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [preferences, setPreferences] = useState({
    preferred_market: 'NASDAQ',
    analysis_period: '1 Year',
  });
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const fetchUserProfileAndPreferences = async () => {
    try {
      const [userRes, prefRes] = await Promise.all([
        api.get('/auth/me'),
        api.get('/preferences'),
      ]);
      setUser(userRes.data);
      setPreferences(prefRes.data);
      localStorage.setItem('user_info', JSON.stringify(userRes.data));
    } catch (err) {
      console.error('Failed to restore authentication session:', err);
      setUser(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUserProfileAndPreferences();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.data.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
      await fetchUserProfileAndPreferences();
      addToast('Welcome back! Successfully logged in.', 'success');
      return true;
    }
    return false;
  };

  const register = async (fullName, email, password, confirmPassword) => {
    const res = await api.post('/auth/register', {
      full_name: fullName,
      email,
      password,
      confirm_password: confirmPassword,
    });
    addToast(res.data.message || 'Registration successful! Please log in.', 'success');
    return res.data;
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // ignore
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      setUser(null);
      addToast('You have been logged out.', 'info');
    }
  };

  const updateProfileName = async (fullName) => {
    const res = await api.put('/users/profile', { full_name: fullName });
    setUser(res.data);
    localStorage.setItem('user_info', JSON.stringify(res.data));
    addToast('Profile name updated successfully.', 'success');
    return res.data;
  };

  const savePreferences = async (preferredMarket, analysisPeriod) => {
    const res = await api.put('/preferences', {
      preferred_market: preferredMarket,
      analysis_period: analysisPeriod,
    });
    setPreferences(res.data);
    addToast('Preferences saved successfully.', 'success');
    return res.data;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        preferences,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        updateProfileName,
        savePreferences,
        addToast,
      }}
    >
      {children}
      {/* Toast Notification Container */}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm pointer-events-none">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-center justify-between p-4 rounded-xl shadow-lg border text-sm font-medium transition-all transform duration-200 animate-slide-in ${
              toast.type === 'success'
                ? 'bg-emerald-900/95 text-emerald-100 border-emerald-700/50'
                : toast.type === 'error'
                ? 'bg-rose-900/95 text-rose-100 border-rose-700/50'
                : 'bg-slate-900/95 text-slate-100 border-slate-700/50'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-base">
                {toast.type === 'success' ? '✓' : toast.type === 'error' ? '⚠' : 'ℹ'}
              </span>
              <span>{toast.message}</span>
            </div>
            <button
              onClick={() => removeToast(toast.id)}
              className="ml-4 text-xs opacity-70 hover:opacity-100 transition-opacity"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

