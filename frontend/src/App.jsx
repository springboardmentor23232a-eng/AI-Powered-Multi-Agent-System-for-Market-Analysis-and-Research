import React, { useState, useEffect } from 'react';
import AuthLayout from './components/AuthLayout';
import RegisterForm from './components/RegisterForm';
import LoginForm from './components/LoginForm';
import TopNav from './components/TopNav';
import PageHeader from './components/PageHeader';
import DashboardView from './components/DashboardView';
import ResearchView from './components/ResearchView';
import ReportView from './components/ReportView';
import HistoryView from './components/HistoryView';
import CompareView from './components/CompareView';
import { api, clearAuthSession, setAuthSession } from './api/client';

export default function App() {
  // If unauthenticated, default directly to the Login page
  const [authView, setAuthView] = useState('login'); // 'login' or 'register'
  const [token, setToken] = useState(localStorage.getItem('fincrew_token') || '');
  const [user, setUser] = useState(null);
  const [initializing, setInitializing] = useState(true);

  // Main Application Navigation State
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard', 'research', 'report', 'history', 'compare'
  const [activeReportId, setActiveReportId] = useState(null);
  const [researchSessionId, setResearchSessionId] = useState(null);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Validate existing stored JWT session on startup
  useEffect(() => {
    const verifyExistingToken = async () => {
      const storedToken = localStorage.getItem('fincrew_token');
      if (!storedToken) {
        clearAuthSession();
        setToken('');
        setUser(null);
        setAuthView('login');
        setInitializing(false);
        return;
      }

      try {
        // Authenticate token against backend /api/auth/me
        const userData = await api.getMe();
        if (userData && userData.email) {
          setUser(userData);
          setToken(storedToken);
          setAuthSession(storedToken, userData);
        } else {
          throw new Error('Invalid user profile response');
        }
      } catch (err) {
        // Token invalid, expired, or rejected
        clearAuthSession();
        setToken('');
        setUser(null);
        setAuthView('login');
      } finally {
        setInitializing(false);
      }
    };

    verifyExistingToken();

    // Listen for session expiry events from API client
    const handleExpired = () => {
      clearAuthSession();
      setToken('');
      setUser(null);
      setAuthView('login');
    };

    window.addEventListener('fincrew-session-expired', handleExpired);
    return () => window.removeEventListener('fincrew-session-expired', handleExpired);
  }, []);

  const handleLoginSuccess = (newToken, newUser) => {
    setAuthSession(newToken, newUser);
    setToken(newToken);
    setUser(newUser);
    setActiveTab('dashboard');
  };

  const handleRegisterSuccess = async (registeredEmail, registeredPassword) => {
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: registeredEmail,
          password: registeredPassword,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        handleLoginSuccess(data.access_token, data.user);
      } else {
        setAuthView('login');
      }
    } catch {
      setAuthView('login');
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      clearAuthSession();
    } finally {
      setToken('');
      setUser(null);
      setAuthView('login');
    }
  };

  const handleSelectSession = (sessionId, targetView = 'report') => {
    if (targetView === 'report') {
      setActiveReportId(sessionId);
      setActiveTab('report');
    } else if (targetView === 'research') {
      setResearchSessionId(sessionId);
      setActiveTab('research');
    } else {
      setActiveTab(targetView);
    }
    setIsMobileSidebarOpen(false);
  };

  const getPageMeta = () => {
    switch (activeTab) {
      case 'dashboard':
        return {
          title: 'Investment Dashboard',
          subtitle: 'Workspace consensus analytics, research status & recent activity',
          actionLabel: 'New Research',
        };
      case 'research':
        return {
          title: 'Stock Equity Research',
          subtitle: 'Initiate autonomous multi-agent analysis for any stock ticker',
          actionLabel: 'New Research',
        };
      case 'report':
        return {
          title: 'Consensus Research Report',
          subtitle: 'Synthesized committee rating, target prices & specialist agent breakdowns',
          actionLabel: 'New Research',
        };
      case 'history':
        return {
          title: 'Research History & Archives',
          subtitle: 'Browse, review, export, and manage your multi-agent stock research sessions',
          actionLabel: 'New Stock Analysis',
        };
      case 'compare':
        return {
          title: 'Multi-Stock Comparison',
          subtitle: 'Side-by-side comparative analysis across 2 to 5 equities',
          actionLabel: 'New Comparison',
        };
      default:
        return {
          title: 'FinCrew Platform',
          subtitle: 'Multi-Agent Research Desk',
          actionLabel: 'New Research',
        };
    }
  };

  // Initializing Spinner
  if (initializing) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center bg-[#17191F]">
        <div className="w-10 h-10 border-4 border-[#C5F500] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Not authenticated: Render Clean Authentication Layout (defaulting to Login)
  if (!token || !user) {
    return (
      <AuthLayout>
        {authView === 'login' && (
          <LoginForm
            onSwitchToRegister={() => setAuthView('register')}
            onLoginSuccess={handleLoginSuccess}
          />
        )}

        {authView === 'register' && (
          <RegisterForm
            onSwitchToLogin={() => setAuthView('login')}
            onRegisterSuccess={handleRegisterSuccess}
          />
        )}
      </AuthLayout>
    );
  }

  // Authenticated: Render Institutional Top Navigation & Canvas Layout
  const meta = getPageMeta();

  return (
    <div className="min-h-screen w-full bg-[#EAF2FF] text-[#111318] flex flex-col selection:bg-[#C5F500] selection:text-[#111318]">
      {/* Institutional Top Navigation Bar */}
      <TopNav
        activeTab={activeTab}
        setActiveTab={(tab) => {
          if (tab !== 'report') setActiveReportId(null);
          if (tab !== 'research') setResearchSessionId(null);
          setActiveTab(tab);
        }}
        user={user}
        onLogout={handleLogout}
        onOpenQuickResearch={() => {
          setActiveTab('research');
          setResearchSessionId(null);
        }}
      />

      {/* Main Page Canvas Container */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-8 py-4 sm:py-6 overflow-y-auto">
        <PageHeader
          title={meta.title}
          subtitle={meta.subtitle}
          onBack={activeTab !== 'dashboard' ? () => setActiveTab('dashboard') : null}
          actionLabel={meta.actionLabel}
          onAction={() => {
            setActiveTab('research');
            setResearchSessionId(null);
          }}
        />

        {/* View Routing Components */}
        <main className="w-full">
          {activeTab === 'dashboard' && (
            <DashboardView
              onSelectSession={handleSelectSession}
              onNavigateToResearch={() => {
                setActiveTab('research');
                setResearchSessionId(null);
              }}
              onNavigateToHistory={() => {
                setActiveTab('history');
              }}
            />
          )}

          {activeTab === 'research' && (
            <ResearchView
              initialSessionId={researchSessionId}
              onViewReport={(sessionId) => {
                setActiveReportId(sessionId);
                setActiveTab('report');
              }}
            />
          )}

          {activeTab === 'report' && (
            <ReportView
              sessionId={activeReportId}
              onBack={() => setActiveTab('dashboard')}
            />
          )}

          {activeTab === 'history' && (
            <HistoryView
              onSelectReport={(sessionId, target = 'report') => {
                if (target === 'report') {
                  setActiveReportId(sessionId);
                  setActiveTab('report');
                } else {
                  setResearchSessionId(sessionId);
                  setActiveTab('research');
                }
              }}
              onNavigateToResearch={() => {
                setActiveTab('research');
                setResearchSessionId(null);
              }}
            />
          )}

          {activeTab === 'compare' && (
            <CompareView
              onSelectReport={(sessionId) => {
                setActiveReportId(sessionId);
                setActiveTab('report');
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
}
