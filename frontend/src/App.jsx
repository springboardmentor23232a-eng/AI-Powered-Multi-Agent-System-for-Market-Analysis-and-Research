import { useEffect, useState } from "react";
import axios from "axios";
import api from "./api/client";
import AuthForm from "./components/AuthForm";
import Dashboard from "./components/Dashboard";

export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const handleGoogleRedirect = async () => {
      // Handle OAuth implicit token returned from accounts.google.com
      if (window.location.hash && window.location.hash.includes("access_token=")) {
        const params = new URLSearchParams(window.location.hash.substring(1));
        const googleToken = params.get("access_token");
        window.history.replaceState(null, "", window.location.pathname);

        if (googleToken) {
          try {
            const profileRes = await axios.get("https://www.googleapis.com/oauth2/v3/userinfo", {
              headers: { Authorization: `Bearer ${googleToken}` },
            });
            const loginRes = await api.post("/api/auth/oauth", {
              provider: "google",
              email: profileRes.data.email,
              full_name: profileRes.data.name,
              id_token: googleToken,
            });
            localStorage.setItem("access_token", loginRes.data.access_token);
            setUser(loginRes.data.user);
            setChecking(false);
            return;
          } catch {
            // Fall through to normal /me check
          }
        }
      }

      try {
        const res = await api.get("/api/auth/me");
        setUser(res.data);
      } catch {
        setUser(null);
      } finally {
        setChecking(false);
      }
    };

    handleGoogleRedirect();
  }, []);

  const handleLogout = async () => {
    try {
      await api.post("/api/auth/logout");
    } finally {
      localStorage.removeItem("access_token");
      setUser(null);
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950 text-slate-300">
        Loading workspace...
      </div>
    );
  }

  return user ? (
    <Dashboard user={user} onLogout={handleLogout} />
  ) : (
    <AuthForm onAuthenticated={setUser} />
  );
}