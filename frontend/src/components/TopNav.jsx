import React, { useState, useRef, useEffect } from 'react';
import {
  LayoutGrid,
  Search,
  History,
  GitCompare,
  LogOut,
  User as UserIcon,
  Menu,
  X,
  Sparkles,
} from 'lucide-react';
import FinCrewLogo from './FinCrewLogo';

export default function TopNav({
  activeTab,
  setActiveTab,
  user,
  onLogout,
  onOpenQuickResearch,
}) {
  const [profileOpen, setProfileOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const profileRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutGrid,
    },
    {
      id: 'research',
      label: 'Stock Research',
      icon: Search,
    },
    {
      id: 'history',
      label: 'Research History',
      icon: History,
    },
    {
      id: 'compare',
      label: 'Stock Comparison',
      icon: GitCompare,
    },
  ];

  const userInitial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : user?.email
    ? user.email.charAt(0).toUpperCase()
    : 'U';

  const handleNavClick = (tabId) => {
    setActiveTab(tabId);
    setMobileMenuOpen(false);
  };

  return (
    <header className="w-full bg-[#EAF2FF] pt-4 px-4 sm:px-8 pb-3 select-none">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Left: FinCrew Brand Logo */}
        <div
          onClick={() => handleNavClick('dashboard')}
          className="cursor-pointer shrink-0"
        >
          <FinCrewLogo variant="bars" />
        </div>

        {/* Center: Deep Charcoal Pill Navigation Bar (Desktop) */}
        <nav className="hidden md:flex items-center bg-[#17191F] text-white rounded-full p-1 shadow-md border border-[#232731]">
          {navItems.map((item) => {
            const isActive =
              activeTab === item.id ||
              (item.id === 'research' && activeTab === 'report');
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`flex items-center gap-2 px-4 lg:px-5 py-2 rounded-full text-xs lg:text-[13px] font-bold transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#C5F500] text-[#111318] shadow-xs'
                    : 'text-gray-300 hover:text-white hover:bg-white/5'
                }`}
              >
                {item.id === 'dashboard' && <Icon className="w-3.5 h-3.5" />}
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right: User Avatar Profile */}
        <div className="flex items-center gap-2.5">
          {/* User Profile Dropdown */}
          <div className="relative" ref={profileRef}>
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              title={`${user?.full_name || 'User Profile'}`}
              className="w-9 h-9 rounded-full bg-[#17191F] text-[#C5F500] font-black text-xs flex items-center justify-center border border-[#232731] shadow-xs hover:ring-2 hover:ring-[#C5F500]/60 transition-all cursor-pointer"
            >
              <span>{userInitial}</span>
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-[#DCE7F6] shadow-xl p-3 z-50 animate-fadeIn text-xs">
                <div className="p-3 bg-[#F0F6FE] rounded-xl mb-2">
                  <div className="font-extrabold text-[#111318] text-sm truncate">
                    {user?.full_name || 'User'}
                  </div>
                  <div className="text-gray-500 truncate mt-0.5">
                    {user?.email || ''}
                  </div>
                </div>

                <button
                  onClick={() => {
                    setProfileOpen(false);
                    if (onLogout) onLogout();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-rose-600 hover:bg-rose-50 font-bold transition cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Log Out</span>
                </button>
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden w-9 h-9 rounded-full bg-white border border-[#DCE7F6] shadow-xs flex items-center justify-center text-[#111318] hover:bg-gray-50 transition cursor-pointer"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Overlay / Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden mt-3 p-4 bg-[#17191F] text-white rounded-3xl shadow-xl border border-[#232731] space-y-2 animate-fadeIn">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => handleNavClick(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl text-xs font-bold transition ${
                  isActive
                    ? 'bg-[#C5F500] text-[#111318]'
                    : 'text-gray-300 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </button>
            );
          })}

          <div className="pt-2 border-t border-gray-800 flex items-center justify-between text-xs text-gray-400 px-2">
            <div>
              <div className="font-bold text-white">{user?.full_name}</div>
              <div className="text-[11px] truncate">{user?.email}</div>
            </div>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                if (onLogout) onLogout();
              }}
              className="px-3 py-1.5 rounded-xl bg-red-950/40 text-red-400 font-bold hover:bg-red-900/50"
            >
              Log Out
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
