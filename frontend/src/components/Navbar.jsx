import React from "react";
import { useAuth } from "../context/AuthContext";
import {
  TrendingUp,
  Sliders,
  LogOut,
  User,
  PlusCircle,
  Globe,
  Clock,
  ShieldCheck,
} from "lucide-react";

export default function Navbar({
  onOpenPreferences,
  onOpenNewResearch,
  onOpenAuth,
}) {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="navbar-container">
      <div className="navbar-brand">
        <div className="brand-icon-wrapper">
          <TrendingUp className="brand-icon" size={24} />
        </div>
        <div>
          <div className="brand-title">
            Multi-Agent Stock Research Analyst
          </div>
          <div className="brand-subtitle">
            <ShieldCheck size={12} className="inline-icon" /> Module 1: Auth & Workspace
          </div>
        </div>
      </div>

      <div className="navbar-actions">
        {isAuthenticated ? (
          <>
            <div className="market-badges">
              <span className="badge-pill active">
                <Globe size={13} /> {user?.preferences?.market || "NASDAQ"}
              </span>
              <span className="badge-pill active">
                <Clock size={13} /> {user?.preferences?.analysis_period || "1 Year"}
              </span>
            </div>

            <button
              className="btn btn-secondary"
              onClick={onOpenPreferences}
              title="Configure Market & Period Preferences"
            >
              <Sliders size={15} /> Preferences
            </button>

            <button
              className="btn btn-primary"
              onClick={onOpenNewResearch}
              title="Start New Multi-Agent Stock Research"
            >
              <PlusCircle size={15} /> Start Research
            </button>

            <div className="user-profile-badge">
              <div className="avatar">
                <User size={15} />
              </div>
              <div className="user-info">
                <span className="user-name">{user?.full_name}</span>
                <span className="user-email">{user?.email}</span>
              </div>
              <button
                className="btn-icon"
                onClick={logout}
                title="Sign Out"
                aria-label="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          </>
        ) : (
          <button className="btn btn-primary" onClick={() => onOpenAuth("login")}>
            Sign In / Register
          </button>
        )}
      </div>
    </header>
  );
}
