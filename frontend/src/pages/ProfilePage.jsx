import React, { useState } from 'react';
import { User, Mail, Calendar, ShieldCheck, Check, Edit2, Loader2, Key } from 'lucide-react';
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
    <div className="space-y-6 animate-fade-in pb-12 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
          <User className="w-6 h-6 text-blue-600" />
          Analyst Profile & Security
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          View your analyst credentials, session metadata, and workspace settings
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Profile Card */}
        <div className="md:col-span-2 bg-white rounded-3xl border border-slate-200/80 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-extrabold text-xl flex items-center justify-center shadow-lg shadow-blue-600/20">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'}
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">{user?.full_name}</h2>
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 mt-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> Certified Analyst
                </span>
              </div>
            </div>

            {!isEditing && (
              <button
                onClick={() => {
                  setFullName(user?.full_name || '');
                  setIsEditing(true);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Edit Name</span>
              </button>
            )}
          </div>

          {/* Form / Details */}
          <form onSubmit={handleUpdateName} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Full Name
              </label>
              {isEditing ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="flex-1 px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all"
                  />
                  <button
                    type="submit"
                    disabled={saving}
                    className="px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-all disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-sm font-semibold text-slate-900">
                  {user?.full_name}
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Corporate Email Address
              </label>
              <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-sm font-medium text-slate-600 flex items-center justify-between">
                <span>{user?.email}</span>
                <span className="text-[11px] font-semibold text-slate-400">Verified</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Email is linked to your institutional identity and audit trail.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Account Creation Date
              </label>
              <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-sm font-medium text-slate-700 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-slate-400" />
                <span>
                  {user?.created_at
                    ? new Date(user.created_at).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })
                    : 'Active'}
                </span>
              </div>
            </div>
          </form>
        </div>

        {/* Security / Architecture Card */}
        <div className="bg-slate-900 text-slate-300 rounded-3xl p-6 sm:p-7 border border-slate-800 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 inline-block">
              <Key className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-white">Security & Integrity</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Passwords are salted and hashed with bcrypt. Sessions are protected via JWT with claims-derived identity verification.
            </p>

            <div className="pt-2 space-y-2.5 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Password Hashing</span>
                <span className="font-mono text-emerald-400 font-semibold">bcrypt (12 rounds)</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Token Protocol</span>
                <span className="font-mono text-blue-400 font-semibold">JWT HS256</span>
              </div>
              <div className="flex items-center justify-between py-1.5 border-b border-slate-800">
                <span className="text-slate-400">Database Engine</span>
                <span className="font-mono text-indigo-400 font-semibold">PostgreSQL 18</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-400">Data Isolation</span>
                <span className="font-mono text-emerald-400 font-semibold">Multi-Tenant Enforced</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-500">
            Multi-Agent Stock Research Analyst • Module 1
          </div>
        </div>
      </div>
    </div>
  );
}

