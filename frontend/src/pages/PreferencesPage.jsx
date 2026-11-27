import React, { useState, useEffect } from 'react';
import { Sliders, Globe2, Calendar, Check, Save, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function PreferencesPage() {
  const { preferences, savePreferences, addToast } = useAuth();

  const [market, setMarket] = useState(preferences?.preferred_market || 'NASDAQ');
  const [period, setPeriod] = useState(preferences?.analysis_period || '1 Year');
  const [saving, setSaving] = useState(false);

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
      subtitle: 'Primary Indian equity exchange (NIFTY 50)',
      region: 'India',
    },
    {
      id: 'BSE',
      title: 'BSE Ltd., India',
      subtitle: 'Bombay Stock Exchange (SENSEX)',
      region: 'India',
    },
    {
      id: 'NASDAQ',
      title: 'NASDAQ – US Stock Exchange',
      subtitle: 'Global marketplace for technology & growth equities',
      region: 'United States',
    },
    {
      id: 'NYSE',
      title: 'NYSE – New York Stock Exchange',
      subtitle: 'World’s largest exchange by market capitalization',
      region: 'United States',
    },
  ];

  const periodOptions = [
    { id: '1 Month', label: '1 Month', desc: 'Short-term momentum & earnings drift' },
    { id: '3 Months', label: '3 Months', desc: 'Quarterly financial cycle' },
    { id: '6 Months', label: '6 Months', desc: 'Mid-term trend & multi-quarter analysis' },
    { id: '1 Year', label: '1 Year', desc: 'Annual valuation & corporate performance' },
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
    <div className="space-y-6 pb-12 max-w-4xl">
      <div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-amber-700 font-semibold">
          Desk Configuration
        </span>
        <h1 className="font-display text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <Sliders className="w-6 h-6 text-[#0A624C]" />
          Market & Horizon Preferences
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 mt-1">
          Configure your default exchange desk and quantitative analysis window
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-[#E4E1D8]">
            <div className="p-2.5 rounded-xl bg-emerald-50 border border-emerald-200 text-[#0A624C]">
              <Globe2 className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-display text-base font-bold text-slate-900">Preferred Stock Market</h2>
              <p className="text-xs text-slate-500">Default exchange applied when launching new multi-agent runs</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-2">
            {marketOptions.map((opt) => {
              const isSelected = market === opt.id;
              return (
                <div
                  key={opt.id}
                  onClick={() => setMarket(opt.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-start justify-between gap-3 ${
                    isSelected
                      ? 'border-[#0A624C] bg-emerald-50/70'
                      : 'border-[#E4E1D8] bg-[#FAF9F5] hover:border-slate-300'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-extrabold text-slate-900 text-sm">{opt.id}</span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-white border border-[#DCD8CD] text-slate-600">
                        {opt.region}
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-slate-800">{opt.title}</p>
                    <p className="text-[11px] text-slate-500">{opt.subtitle}</p>
                  </div>

                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                      isSelected ? 'border-[#0A624C] bg-[#0A624C] text-white' : 'border-slate-300 bg-white'
                    }`}
                  >
                    {isSelected && <Check className="w-3 h-3 stroke-[3]" />}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="glass-panel p-6 sm:p-8 rounded-3xl space-y-4">
          <div className="flex items-center gap-3 pb-3 border-b border-[#E4E1D8]">
            <div className="p-2.5 rounded-xl bg-sky-50 border border-sky-200 text-[#1E3A5F]">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-display text-base font-bold text-slate-900">Default Analysis Period</h2>
              <p className="text-xs text-slate-500">Evaluation window for OHLCV trends, volatility & indicators</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2">
            {periodOptions.map((opt) => {
              const isSelected = period === opt.id;
              return (
                <div
                  key={opt.id}
                  onClick={() => setPeriod(opt.id)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'border-[#0A624C] bg-emerald-50/70'
                      : 'border-[#E4E1D8] bg-[#FAF9F5] hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono font-extrabold text-slate-900 text-sm">{opt.label}</span>
                    <div
                      className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                        isSelected ? 'border-[#0A624C] bg-[#0A624C] text-white' : 'border-slate-300 bg-white'
                      }`}
                    >
                      {isSelected && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">{opt.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-end pt-2">
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-3 bg-[#0A624C] hover:bg-[#084C3B] text-white font-mono font-bold text-xs rounded-xl shadow-sm flex items-center gap-2 disabled:opacity-50"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>SAVING...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>SAVE PREFERENCES</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
