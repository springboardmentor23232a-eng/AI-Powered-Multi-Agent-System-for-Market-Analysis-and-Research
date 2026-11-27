import React, { useState } from 'react';
import { User, Calendar, ShieldCheck, Check, Edit2, Loader2, Key } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function ProfilePage() {
  const { user, updateProfileName, addToast } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [saving, setSaving] = useState(false);

  const handleUpdateName = async (e) => {
    e.preventDefault();
    if (!fullName.trim() || fullName.trim().length < 2) {
      addToast('Full name must be at least 2 characters.', 'error');
      return;
    }

    setSaving(true);
    try {
      await updateProfileName(fullName.trim());
      setIsEditing(false);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update profile.';
      addToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl">
      <div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-[#0A624C] font-semibold">
          Identity & JWT Security
        </span>
        <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <User className="w-6 h-6 text-[#0A624C]" />
          Analyst Profile & Security
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          View your analyst credentials, session metadata, and database isolation guarantees
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 glass-panel rounded-3xl p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-[#E4E1D8]">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[#0A624C] to-[#0D7A5F] text-white font-mono font-extrabold text-xl flex items-center justify-center shadow-md shadow-emerald-900/15">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'Q'}
              </div>
              <div>
                <h2 className="font-display text-lg font-bold text-slate-900">{user?.full_name}</h2>
                <span className="inline-flex items-center gap-1.5 text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-[#0A624C] border border-emerald-200 mt-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> VERIFIED ANALYST
                </span>
              </div>
            </div>

            {!isEditing && (
              <button
                onClick={() => {
                  setFullName(user?.full_name || '');
                  setIsEditing(true);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono font-semibold text-slate-700 bg-[#FAF9F5] hover:bg-[#EFECE4] border border-[#DCD8CD] transition-colors"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>EDIT</span>
              </button>
            )}
          </div>

          <form onSubmit={handleUpdateName} className="space-y-4">
            <div>
              <label className="block text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Full Name
              </label>
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="flex-1 px-4 py-2.5 bg-[#FAF9F5] border border-[#DCD8CD] rounded-xl text-sm font-medium text-slate-900 focus:bg-white focus:outline-none focus:border-[#0A624C]"
                  />
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2.5 bg-[#0A624C] hover:bg-[#084C3B] text-white rounded-xl text-xs font-mono font-bold transition-all disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    SAVE
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-2.5 bg-[#FAF9F5] hover:bg-[#EFECE4] text-slate-700 border border-[#DCD8CD] rounded-xl text-xs font-mono font-semibold"
                  >
                    CANCEL
                  </button>
                </div>
              ) : (
                <div className="p-3 bg-[#FAF9F5] border border-[#E4E1D8] rounded-xl text-sm font-semibold text-slate-900">
                  {user?.full_name}
                </div>
              )}
            </div>

            <div>
              <label className="block text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="p-3 bg-[#FAF9F5] border border-[#E4E1D8] rounded-xl text-sm font-mono text-slate-700 flex items-center justify-between">
                <span>{user?.email}</span>
                <span className="text-[10px] font-mono font-semibold text-[#0A624C]">ACTIVE</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-mono font-semibold text-slate-500 uppercase tracking-wider mb-1.5">
                Account Created
              </label>
              <div className="p-3 bg-[#FAF9F5] border border-[#E4E1D8] rounded-xl text-sm font-mono text-slate-700 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>{user?.created_at ? new Date(user.created_at).toLocaleString() : 'Active'}</span>
              </div>
            </div>
          </form>
        </div>

        <div className="glass-panel rounded-3xl p-6 sm:p-7 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="p-3 rounded-2xl bg-sky-50 border border-sky-200 text-[#1E3A5F] inline-block">
              <Key className="w-6 h-6" />
            </div>
            <h3 className="font-display text-base font-bold text-slate-900">Security & Integrity</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Salted bcrypt password hashing with claims-based JWT session verification and strict per-user PostgreSQL isolation.
            </p>

            <div className="pt-2 space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-[#E4E1D8]">
                <span className="text-slate-500">Hashing</span>
                <span className="font-mono text-[#0A624C] font-semibold">bcrypt</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[#E4E1D8]">
                <span className="text-slate-500">Protocol</span>
                <span className="font-mono text-[#1E3A5F] font-semibold">JWT HS256</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-[#E4E1D8]">
                <span className="text-slate-500">Database</span>
                <span className="font-mono text-amber-700 font-semibold">PostgreSQL</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500">Isolation</span>
                <span className="font-mono text-[#0A624C] font-semibold">Multi-Tenant</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[#E4E1D8] text-[11px] font-mono text-slate-400">
            QuantAgent Studio • Modules 1–4
          </div>
        </div>
      </div>
    </div>
  );
}
