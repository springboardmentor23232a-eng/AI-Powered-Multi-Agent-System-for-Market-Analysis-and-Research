import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Navbar from "./components/Navbar";
import WatchlistSection from "./components/WatchlistSection";
import ResearchHistorySection from "./components/ResearchHistorySection";
import AuthModal from "./components/AuthModal";
import PreferencesModal from "./components/PreferencesModal";
import NewResearchModal from "./components/NewResearchModal";
import ReportModal from "./components/ReportModal";
import {
  TrendingUp,
  Bookmark,
  History,
  ShieldCheck,
  Zap,
  Globe,
  Clock,
  Cpu,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import "./App.css";

function DashboardContent() {
  const { user, isAuthenticated, loading } = useAuth();

  // Modals state
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authModalTab, setAuthModalTab] = useState("login");
  const [prefModalOpen, setPrefModalOpen] = useState(false);
  const [researchModalOpen, setResearchModalOpen] = useState(false);
  const [activeResearchTarget, setActiveResearchTarget] = useState(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);
  const [activeReportTask, setActiveReportTask] = useState(null);

  // Cross-component refresh signals
  const [refreshHistoryTrigger, setRefreshHistoryTrigger] = useState(0);
  const [refreshWatchlistTrigger, setRefreshWatchlistTrigger] = useState(0);

  const openAuth = (tab = "login") => {
    setAuthModalTab(tab);
    setAuthModalOpen(true);
  };

  const handleLaunchResearchFromWatchlist = (stockData) => {
    setActiveResearchTarget(stockData);
    setResearchModalOpen(true);
  };

  const handleNewResearchSuccess = (createdTask) => {
    setRefreshHistoryTrigger((prev) => prev + 1);
    setActiveReportTask(createdTask);
    setReportModalOpen(true);
  };

  const handleOpenReport = (task) => {
    setActiveReportTask(task);
    setReportModalOpen(true);
  };

  if (loading) {
    return (
      <div className="app-loading-screen">
        <div className="spin-large" />
        <p>Loading Multi-Agent Research Workspace...</p>
      </div>
    );
  }

  return (
    <div className="app-wrapper">
      <Navbar
        onOpenPreferences={() => setPrefModalOpen(true)}
        onOpenNewResearch={() => {
          setActiveResearchTarget(null);
          setResearchModalOpen(true);
        }}
        onOpenAuth={openAuth}
      />

      <main className="main-content">
        {!isAuthenticated ? (
          <div className="hero-landing">
            <div className="hero-badge">
              <Sparkles size={14} className="text-accent" /> Autonomous Equity Intelligence
            </div>
            <h1 className="hero-headline">
              Multi-Agent Stock Research Analyst
            </h1>
            <p className="hero-subtext">
              Institutional-grade market analysis synthesized by autonomous AI agents.
              Track your saved stocks, manage global exchange preferences, and inspect
              deep-dive fundamental and technical valuation reports.
            </p>

            <div className="hero-cta-group">
              <button
                className="btn btn-primary btn-lg"
                onClick={() => openAuth("register")}
              >
                Create Free Account <ArrowRight size={18} />
              </button>
              <button
                className="btn btn-secondary btn-lg"
                onClick={() => openAuth("login")}
              >
                Sign In to Workspace
              </button>
            </div>

            <div className="features-grid">
              <div className="feature-card">
                <div className="feature-icon">
                  <ShieldCheck size={24} />
                </div>
                <h3>JWT Secure Authentication</h3>
                <p>
                  Bcrypt hashed password storage and tokenized user sessions strictly
                  isolating watchlists and historical research tasks.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">
                  <Bookmark size={24} />
                </div>
                <h3>Watchlist Management</h3>
                <p>
                  Real-time ticker lookups for NASDAQ, NYSE, NSE, and BSE with duplicate
                  prevention and 1-click research deployment.
                </p>
              </div>

              <div className="feature-card">
                <div className="feature-icon">
                  <Cpu size={24} />
                </div>
                <h3>Multi-Agent Synthesis</h3>
                <p>
                  Autonomous cooperation between Fundamental, Technical Momentum, and
                  Macro Sentiment agents delivering actionable investment ratings.
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="dashboard-container">
            {/* Quick Metrics Bar */}
            <div className="metrics-summary-bar">
              <div className="summary-item">
                <span className="summary-label">Authenticated User</span>
                <span className="summary-value user-highlight">{user?.full_name}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Active Market</span>
                <span className="summary-value">
                  <Globe size={14} className="inline-icon" /> {user?.preferences?.market || "NASDAQ"}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Analysis Horizon</span>
                <span className="summary-value">
                  <Clock size={14} className="inline-icon" /> {user?.preferences?.analysis_period || "1 Year"}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Workspace Module</span>
                <span className="summary-value text-accent">Module 1 (Production Ready)</span>
              </div>
            </div>

            {/* Main Sections Layout */}
            <div className="workspace-layout">
              {/* Watchlist Section */}
              <section className="workspace-column">
                <WatchlistSection
                  onLaunchResearch={handleLaunchResearchFromWatchlist}
                  refreshTrigger={refreshWatchlistTrigger}
                />
              </section>

              {/* Research History Section */}
              <section className="workspace-column">
                <ResearchHistorySection
                  onViewReport={handleOpenReport}
                  refreshTrigger={refreshHistoryTrigger}
                />
              </section>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <div>
          Multi-Agent Stock Research Analyst Platform &bull; Student Implementation Guide &bull; Module 1
        </div>
      </footer>

      {/* Modals */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialTab={authModalTab}
      />

      <PreferencesModal
        isOpen={prefModalOpen}
        onClose={() => setPrefModalOpen(false)}
      />

      <NewResearchModal
        isOpen={researchModalOpen}
        onClose={() => setResearchModalOpen(false)}
        initialData={activeResearchTarget}
        onSuccess={handleNewResearchSuccess}
      />

      <ReportModal
        isOpen={reportModalOpen}
        onClose={() => setReportModalOpen(false)}
        task={activeReportTask}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}
