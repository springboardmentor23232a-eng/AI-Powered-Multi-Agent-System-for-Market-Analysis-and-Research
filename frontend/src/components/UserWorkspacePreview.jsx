import React, { useState } from 'react';
import { User, LogOut, CheckCircle2, ShieldCheck, Loader2 } from 'lucide-react';
import FinCrewLogo from './FinCrewLogo';

export default function UserWorkspacePreview({ user, token, onLogout }) {
  const [loggingOut, setLoggingOut] = useState(false);

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      if (token) {
        await fetch('/api/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setLoggingOut(false);
      if (onLogout) onLogout();
    }
  };

  return (
    <div className="w-full flex flex-col items-center">
      {/* FinCrew Brand Logo */}
      <div className="mb-6">
        <FinCrewLogo size="md" />
      </div>

      {/* Success Badge */}
      <div className="w-12 h-12 rounded-full bg-[#d3f3b4] flex items-center justify-center mb-4 text-[#1f4631]">
        <CheckCircle2 className="w-6 h-6 text-[#1f4631]" />
      </div>

      <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111827] text-center mb-2 tracking-tight">
        Authenticated
      </h1>
      <p className="text-sm text-gray-500 text-center mb-6">
        You are securely signed in to FinCrew.
      </p>

      {/* User Profile Card */}
      <div className="w-full bg-[#f8fafc] border border-gray-100 rounded-2xl p-5 mb-6 space-y-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#9bd946]/20 flex items-center justify-center text-[#1f4631] font-bold text-base">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div className="flex-1 overflow-hidden">
            <div className="font-bold text-[#111827] truncate">{user?.full_name || ''}</div>
            <div className="text-xs text-gray-500 truncate">{user?.email || ''}</div>
          </div>
        </div>

        <div className="pt-2 border-t border-gray-200/60 flex items-center justify-between text-xs text-gray-600">
          <span className="flex items-center gap-1.5 text-[#1f4631] font-semibold">
            <ShieldCheck className="w-4 h-4 text-[#9bd946]" />
            JWT Bearer Active
          </span>
          <span className="bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full font-bold text-[11px]">
            Verified
          </span>
        </div>
      </div>

      {/* Logout Button */}
      <button
        onClick={handleLogout}
        disabled={loggingOut}
        className="w-full h-12 rounded-full border-2 border-gray-200 hover:border-red-400 hover:bg-red-50 text-gray-700 hover:text-red-700 font-bold text-[15px] transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
      >
        {loggingOut ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Revoking token...</span>
          </>
        ) : (
          <>
            <LogOut className="w-4 h-4" />
            <span>Log out</span>
          </>
        )}
      </button>
    </div>
  );
}
