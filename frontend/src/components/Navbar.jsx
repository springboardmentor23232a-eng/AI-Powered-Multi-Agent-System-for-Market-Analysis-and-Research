import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { marketAPI } from '../services/api';
import {
  TrendingUp,
  User,
  LogOut,
  LayoutDashboard,
  LogIn,
  UserPlus,
  Sun,
  Moon,
  ArrowRight,
} from 'lucide-react';

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Real-Time Indices Ticker Tape (Yahoo Finance via FastAPI)
  const [tickerItems, setTickerItems] = useState([
    { symbol: 'NIFTY 50', value: '...', change: '0.00%', isPositive: true },
    { symbol: 'SENSEX', value: '...', change: '0.00%', isPositive: true },
    { symbol: 'NASDAQ', value: '...', change: '0.00%', isPositive: true },
    { symbol: 'S&P 500', value: '...', change: '0.00%', isPositive: true },
    { symbol: 'BRENT CRUDE', value: '...', change: '0.00%', isPositive: true },
    { symbol: 'GOLD (10G)', value: '...', change: '0.00%', isPositive: true },
  ]);

  // Fetch real-time indices from backend
  useEffect(() => {
    const fetchTape = async () => {
      try {
        const liveItems = await marketAPI.getTickerTape();
        if (liveItems && liveItems.length > 0) {
          setTickerItems(liveItems);
        }
      } catch (err) {
        console.warn('Ticker tape cached:', err);
      }
    };
    fetchTape();
    const interval = setInterval(fetchTape, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className={`sticky top-0 z-50 border-b transition-colors duration-200 ${
      isDark ? 'bg-slate-900 border-slate-800 text-slate-100 shadow-lg' : 'bg-white border-slate-200 text-slate-800 shadow-sm'
    }`}>
      {/* 1. Live Market Ticker Tape */}
      <div className={`border-b px-4 py-1.5 text-[11px] font-mono tracking-tight overflow-x-auto no-scrollbar transition-colors ${
        isDark ? 'bg-slate-950 border-slate-800/80 text-slate-300' : 'bg-slate-100 border-slate-200 text-slate-700'
      }`}>
        <div className="max-w-7xl mx-auto flex items-center justify-between space-x-6 min-w-max">
          <div className={`flex items-center space-x-2 font-semibold pr-3 border-r ${
            isDark ? 'text-slate-400 border-slate-800' : 'text-slate-600 border-slate-300'
          }`}>
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="uppercase text-[10px] tracking-wider font-bold">MARKETS LIVE</span>
          </div>

          <div className="flex items-center space-x-6">
            {tickerItems.map((item, idx) => (
              <div key={idx} className="flex items-center space-x-1.5">
                <span className={isDark ? 'text-slate-400 font-medium' : 'text-slate-500 font-medium'}>
                  {item.symbol}
                </span>
                <span className={isDark ? 'text-slate-200 font-bold' : 'text-slate-900 font-bold'}>
                  {item.value}
                </span>
                <span
                  className={`text-[10px] font-semibold ${
                    item.isPositive ? 'text-emerald-500 font-bold' : 'text-rose-500 font-bold'
                  }`}
                >
                  {item.change}
                </span>
              </div>
            ))}
          </div>

          <div className={`text-[10px] pl-4 border-l hidden md:block ${
            isDark ? 'text-slate-500 border-slate-800' : 'text-slate-400 border-slate-300'
          }`}>
            NSE • BSE • NASDAQ • NYSE
          </div>
        </div>
      </div>

      {/* 2. Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <div className="flex items-center space-x-4">
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="bg-gradient-to-tr from-sky-600 to-indigo-600 text-white p-2.5 rounded-xl shadow-md group-hover:from-sky-500 group-hover:to-indigo-500 transition">
                <TrendingUp className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-center space-x-2">
                  <span className={`font-black text-xl tracking-tight font-mono ${isDark ? 'text-white' : 'text-slate-900'}`}>
                    ALPHA<span className="text-sky-500">AGENT</span>
                  </span>
                </div>
                <span className={`text-[10px] font-mono tracking-wider -mt-0.5 hidden sm:block ${isDark ? 'text-slate-400' : 'text-slate-500'}`}>
                  AI STOCK RESEARCH PLATFORM
                </span>
              </div>
            </Link>
          </div>

          {/* Right Actions & Theme Toggle */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Theme Toggle (Light / Dark Mode) */}
            <button
              onClick={toggleTheme}
              className={`p-2 rounded-xl transition flex items-center justify-center border cursor-pointer ${
                isDark
                  ? 'bg-slate-800 hover:bg-slate-700 text-amber-400 border-slate-700'
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
              }`}
              title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>

            {isAuthenticated ? (
              <>
                <Link
                  to="/dashboard"
                  className={`flex items-center space-x-2 text-xs font-mono font-semibold px-3.5 py-2 rounded-xl border transition ${
                    isDark
                      ? 'bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300'
                  }`}
                >
                  <LayoutDashboard className="h-4 w-4 text-sky-500" />
                  <span>Research Workspace</span>
                </Link>

                {/* User Pill & Logout */}
                <div className="flex items-center space-x-2 pl-2 border-l border-slate-700/50">
                  <div className={`flex items-center space-x-2 px-2.5 py-1.5 rounded-lg border text-xs font-medium ${
                    isDark ? 'bg-slate-950 border-slate-800 text-slate-200' : 'bg-slate-100 border-slate-200 text-slate-800'
                  }`}>
                    <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-[10px] font-bold text-white uppercase">
                      {user?.full_name?.charAt(0) || 'U'}
                    </div>
                    <span className="hidden md:inline">{user?.full_name || 'Analyst'}</span>
                  </div>

                  <button
                    onClick={handleLogout}
                    className="text-slate-400 hover:text-rose-500 p-2 rounded-lg transition"
                    title="Sign Out"
                  >
                    <LogOut className="h-4 w-4" />
                  </button>
                </div>
              </>
            ) : (
              <div className="flex items-center space-x-3">
                <Link
                  to="/login"
                  className={`text-xs font-bold px-3.5 py-2 rounded-xl transition border ${
                    isDark
                      ? 'text-slate-200 hover:text-white bg-slate-800 hover:bg-slate-700 border-slate-700'
                      : 'text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 border-slate-300'
                  }`}
                >
                  Log In
                </Link>

                <Link
                  to="/register"
                  className="flex items-center space-x-1.5 text-xs font-bold text-white bg-sky-600 hover:bg-sky-500 px-4 py-2 rounded-xl shadow-md shadow-sky-600/20 transition cursor-pointer"
                >
                  <UserPlus className="h-4 w-4" />
                  <span>Create Account</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
