import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, setCsrfToken, setUnauthorizedHandler } from "./api.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);      // true while we check for an existing session
  const [sessionNotice, setSessionNotice] = useState("");

  useEffect(() => {
    // Restore the session after a page refresh (cookie is sent automatically)
    api("/auth/me", { auth: false })
      .then((d) => { setCsrfToken(d.csrf_token); setUser(d.user); })
      .catch(() => {})
      .finally(() => setLoading(false));
    setUnauthorizedHandler((msg) => { setUser(null); setCsrfToken(null); setSessionNotice(msg); });
  }, []);

  const login = useCallback(async (email, password) => {
    const d = await api("/auth/login", { method: "POST", body: { email, password }, auth: false });
    setCsrfToken(d.csrf_token);
    setSessionNotice("");
    setUser(d.user);
  }, []);

  const logout = useCallback(async () => {
    await api("/auth/logout", { method: "POST", auth: false }).catch(() => {});
    setCsrfToken(null);
    setUser(null);
    setSessionNotice("");
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, sessionNotice, setSessionNotice }}>
      {children}
    </AuthContext.Provider>
  );
}
