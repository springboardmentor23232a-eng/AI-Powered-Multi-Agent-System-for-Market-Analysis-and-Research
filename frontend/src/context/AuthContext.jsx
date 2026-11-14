import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  const checkAuth = useCallback(async () => {
    try {
      setLoading(true);
      const userData = await authService.getMe();
      setUser(userData);
      setAuthError(null);
    } catch (err) {
      // Session expired or unauthenticated
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = async (email, password) => {
    setAuthError(null);
    try {
      const data = await authService.login({ email, password });
      setUser(data.user);
      return data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Invalid email or password. Please try again.';
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  const register = async (formData) => {
    setAuthError(null);
    try {
      const data = await authService.register(formData);
      return data;
    } catch (err) {
      let msg = 'Failed to create account. Please check your details.';
      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          msg = detail;
        } else if (Array.isArray(detail)) {
          msg = detail.map(d => d.msg || d.message || JSON.stringify(d)).join('. ');
        }
      } else if (err.message === 'Network Error') {
        msg = 'Cannot connect to server. Please ensure the backend is running on port 8000.';
      }
      setAuthError(msg);
      throw new Error(msg);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        authError,
        setAuthError,
        login,
        register,
        logout,
        checkAuth,
      }}
    >
      {children}
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

