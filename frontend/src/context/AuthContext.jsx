import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token') || null);
  const [loading, setLoading] = useState(true);

  // Validate session on initial app load
  useEffect(() => {
    const initializeAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const profile = await authAPI.getProfile();
          setUser(profile);
          setToken(storedToken);
        } catch (error) {
          console.error("Session verification failed:", error);
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          setUser(null);
          setToken(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  // Register method
  const register = async (userData) => {
    const data = await authAPI.register(userData);
    return data;
  };

  // Login method (Module 1, Section 2 & 3: receives JWT token and user)
  const login = async (credentials) => {
    const data = await authAPI.login(credentials);
    const { access_token, user: loggedUser } = data;
    
    // Save token and user in localStorage
    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(loggedUser));
    
    setToken(access_token);
    setUser(loggedUser);
    return data;
  };

  // Google Sign-In / Sign-Up method
  const googleSignIn = async (googleData) => {
    const data = await authAPI.googleLogin(googleData);
    const { access_token, user: loggedUser } = data;

    localStorage.setItem('token', access_token);
    localStorage.setItem('user', JSON.stringify(loggedUser));

    setToken(access_token);
    setUser(loggedUser);
    return data;
  };

  // Logout method
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        loading,
        register,
        login,
        googleSignIn,
        logout,
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
