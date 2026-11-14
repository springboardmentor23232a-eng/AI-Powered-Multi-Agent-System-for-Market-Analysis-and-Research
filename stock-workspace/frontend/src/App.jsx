import React, { useEffect, useState } from "react";
import { api } from "./api.js";
import { ToastProvider, Spinner } from "./ui.jsx";
import AuthPage from "./AuthPage.jsx";
import Dashboard from "./Dashboard.jsx";

export default function App() {
  const [user, setUser] = useState(undefined); // undefined = checking session, null = signed out
  const [dark, setDark] = useState(() => localStorage.getItem("theme") === "dark");

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("theme", dark ? "dark" : "light");
  }, [dark]);

  useEffect(() => {
    api.me().then(setUser).catch(() => setUser(null));
  }, []);

  const logout = async () => {
    await api.logout().catch(() => {});
    setUser(null);
  };

  return (
    <ToastProvider>
      {user === undefined ? (
        <div className="flex h-screen items-center justify-center text-indigo-600"><Spinner className="h-8 w-8" /></div>
      ) : user ? (
        <Dashboard user={user} setUser={setUser} onLogout={logout} dark={dark} toggleTheme={() => setDark(!dark)} />
      ) : (
        <AuthPage onLogin={setUser} dark={dark} toggleTheme={() => setDark(!dark)} />
      )}
    </ToastProvider>
  );
}
