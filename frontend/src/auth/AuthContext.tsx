import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, setUnauthorizedHandler, tokenStore } from "../api/client";

interface AuthState {
  authenticated: boolean;
  signIn: (email: string, password: string, mode: "login" | "register", fullName?: string, confirmPassword?: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => tokenStore.get());

  useEffect(() => {
    setUnauthorizedHandler(() => setToken(null));
    return () => setUnauthorizedHandler(null);
  }, []);

  const signIn = useCallback(async (email: string, password: string, mode: "login" | "register", fullName?: string, confirmPassword?: string) => {
    const { access_token } = mode === "login"
      ? await api.login(email, password)
      : await api.register(email, password, fullName, confirmPassword);
    tokenStore.set(access_token);
    setToken(access_token);
  }, []);

  const signOut = useCallback(() => {
    tokenStore.clear();
    setToken(null);
  }, []);

  const value = useMemo(() => ({ authenticated: token !== null, signIn, signOut }), [token, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
