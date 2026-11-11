import React, { useState, useEffect } from 'react';
import { Sliders, Globe2, Calendar, Check, Save, Loader2, Sparkles } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function PreferencesPage() {
  const { preferences, savePreferences, addToast } = useAuth();

  const [market, setMarket] = useState(preferences?.preferred_market || 'NASDAQ');
  const [period, setPeriod] = useState(preferences?.analysis_period || '1 Year');
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (preferences) {
      setMarket(preferences.preferred_market);
      setPeriod(preferences.analysis_period);
    }
  }, [preferences]);

  const marketOptions = [
    {
      id: 'NSE',
      title: 'NSE – National Stock Exchange of India',
      subtitle: 'Primary Indian equity & derivatives exchange (NIFTY 50)',
      region: 'India',
    },
    {
      id: 'BSE',
      title: 'BSE Ltd., India',
      subtitle: 'Asia’s oldest stock exchange, Bombay Stock Exchange (SENSEX)',
      region: 'India',
    },
    {
      id: 'NASDAQ',
      title: 'NASDAQ – US Stock Exchange',
      subtitle: 'Global electronic marketplace for tech & growth equities',
      region: 'United States',
    },
    {
      id: 'NYSE',
      title: 'NYSE – New York Stock Exchange',
      subtitle: 'World’s largest stock exchange by market capitalization',
      region: 'United States',
    },
  ];

  const periodOptions = [
    { id: '1 Month', label: '1 Month', desc: 'Short-term momentum & earnings drift' },
    { id: '3 Months', label: '3 Months', desc: 'Quarterly financial cycle' },
    { id: '6 Months', label: '6 Months', desc: 'Mid-term trend & multi-quarter analysis' },
    { id: '1 Year', label: '1 Year', desc: 'Annual valuation & corporate performance (Standard)' },
    { id: '5 Years', label: '5 Years', desc: 'Long-term secular compounding & macro cycles' },
  ];

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await savePreferences(market, period);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to update preferences.';
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
          <Sliders className="w-6 h-6 text-blue-600" />
          Research Preferences
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Customize your default stock exchange and quantitative analysis horizon
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-8">
        {/* Section A: Preferred Market */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
            <div className="p-2.5 rounded-xl bg-blue-50 text-blue-600">
              <Globe2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Preferred Stock Market</h2>
              <p className="text-xs text-slate-500">
                Default exchange applied when initiating new multi-agent research tasks
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-2">
            {marketOptions.map((opt) => {
              const isSelected = market === opt.id;
              return (
                <div
                  key={opt.id}
                  onClick={() => setMarket(opt.id)}
                  className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex items-start justify-between gap-3 ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50/50 shadow-sm shadow-blue-600/10'
                      : 'border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-slate-900 text-sm tracking-wide">
                        {opt.id}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-600">
                        {opt.region}
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-slate-700">{opt.title}</p>
                    <p className="text-[11px] text-slate-500 leading-relaxed">{opt.subtitle}</p>
                  </div>

                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                      isSelected
                        ? 'border-blue-600 bg-blue-600 text-white'
                        : 'border-slate-300 bg-white'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Section B: Analysis Period */}
        <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200/80 shadow-sm space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
            <div className="p-2.5 rounded-xl bg-indigo-50 text-indigo-600">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Default Analysis Period</h2>
              <p className="text-xs text-slate-500">
                Evaluation window for price trends, performance calculations, and multi-agent synthesis
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
            {periodOptions.map((opt) => {
              const isSelected = period === opt.id;
              return (
                <div
                  key={opt.id}
                  onClick={() => setPeriod(opt.id)}
                  className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50/50 shadow-sm shadow-blue-600/10'
                      : 'border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-extrabold text-slate-900 text-sm">{opt.label}</span>
                    <div
                      className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                        isSelected
                          ? 'border-blue-600 bg-blue-600 text-white'
                          : 'border-slate-300 bg-white'
                      }`}
                    >
                      {isSelected && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                    </div>
                  </div>
                  <p className="text-xs text-slate-500 leading-snug">{opt.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Save Bar */}
        <div className="flex items-center justify-end gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-600/25 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Saving to Database...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Preferences</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

