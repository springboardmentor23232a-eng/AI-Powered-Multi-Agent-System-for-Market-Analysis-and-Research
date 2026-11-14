import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import api from '../services/api';
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); const [loading, setLoading] = useState(true);
  const authActionRef = useRef(0);
  const location = useLocation();
  useEffect(() => {
    const handleExpired = () => setUser(null);
    window.addEventListener('equitylens:session-expired', handleExpired);
    return () => window.removeEventListener('equitylens:session-expired', handleExpired);
  }, []);
  const refresh = async () => {
    const requestVersion = authActionRef.current;
    try {
      const { data } = await api.get('/auth/me');
      if (requestVersion === authActionRef.current) setUser(data);
      return data;
    } catch (error) {
      if (requestVersion === authActionRef.current) setUser(null);
      return null;
    } finally {
      if (requestVersion === authActionRef.current) setLoading(false);
    }
  };
  useEffect(() => {
    if (location.pathname === '/login' || location.pathname === '/register') {
      setLoading(false);
      return;
    }
    refresh();
  }, [location.pathname]);
  const login = async (credentials) => { authActionRef.current += 1; const { data } = await api.post('/auth/login', credentials); setUser(data); setLoading(false); return data; };
  const register = async (details) => { authActionRef.current += 1; const { data } = await api.post('/auth/register', details); setUser(data); setLoading(false); return data; };
  const googleLogin = async (credential) => { authActionRef.current += 1; const { data } = await api.post('/auth/google', { credential }); setUser(data); setLoading(false); return data; };
  const logout = async () => { authActionRef.current += 1; try { await api.post('/auth/logout'); } finally { setUser(null); setLoading(false); } };
  return <AuthContext.Provider value={{ user, loading, refresh, login, register, googleLogin, logout }}>{children}</AuthContext.Provider>;
}
export const useAuth = () => useContext(AuthContext);
