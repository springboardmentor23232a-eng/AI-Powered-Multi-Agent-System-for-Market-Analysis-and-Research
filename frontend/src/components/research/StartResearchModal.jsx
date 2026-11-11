import React, { useState, useEffect } from 'react';
import { X, Play, Sparkles, Building2, Globe2, Calendar } from 'lucide-react';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';

export default function StartResearchModal({
  isOpen,
  onClose,
  initialData = null,
  onTaskCreated,
}) {
  const { preferences, addToast } = useAuth();

  const [ticker, setTicker] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [market, setMarket] = useState('NASDAQ');
  const [analysisPeriod, setAnalysisPeriod] = useState('1 Year');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialData) {
      setTicker(initialData.ticker || '');
      setCompanyName(initialData.company_name || '');
      setMarket(initialData.market || preferences?.preferred_market || 'NASDAQ');
      setAnalysisPeriod(preferences?.analysis_period || '1 Year');
    } else {
      setTicker('');
      setCompanyName('');
      setMarket(preferences?.preferred_market || 'NASDAQ');
      setAnalysisPeriod(preferences?.analysis_period || '1 Year');
    }
    setError(null);
  }, [initialData, preferences, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticker.trim()) {
      setError('Please provide a valid stock ticker symbol.');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        ticker: ticker.trim().toUpperCase(),
        company_name: companyName.trim() || undefined,
        market,
        analysis_period: analysisPeriod,
      };

      const res = await api.post('/research', payload);
      addToast(`Research task initialized for ${payload.ticker}. Multi-agent analysis running...`, 'success');
      if (onTaskCreated) {
        onTaskCreated(res.data);
      }
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to start research task. Please verify ticker and market.';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden transform transition-all">
        {/* Header */}
        <div className="px-6 py-5 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 rounded-xl border border-blue-400/30 text-blue-300">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold">Start Multi-Agent Research</h3>
              <p className="text-xs text-slate-300">Launch automated fundamental and financial analysis</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Stock Ticker Symbol <span className="text-rose-500">*</span>
            </label>
            <div className="relative">
              <input
                type="text"
                required
                placeholder="e.g. AAPL, NVDA, INFY, RELIANCE"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 font-mono font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all uppercase placeholder:normal-case placeholder:font-sans"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Company Name (Optional)
            </label>
            <div className="relative">
              <Building2 className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                placeholder="e.g. Apple Inc. (Auto-resolved if left empty)"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Globe2 className="w-3.5 h-3.5 text-slate-500" />
                Target Market
              </label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all text-sm"
              >
                <option value="NASDAQ">NASDAQ (US)</option>
                <option value="NYSE">NYSE (US)</option>
                <option value="NSE">NSE (India)</option>
                <option value="BSE">BSE (India)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                Analysis Period
              </label>
              <select
                value={analysisPeriod}
                onChange={(e) => setAnalysisPeriod(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 font-medium focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all text-sm"
              >
                <option value="1 Month">1 Month</option>
                <option value="3 Months">3 Months</option>
                <option value="6 Months">6 Months</option>
                <option value="1 Year">1 Year</option>
                <option value="5 Years">5 Years</option>
              </select>
            </div>
          </div>

          {/* Action buttons */}
          <div className="pt-4 flex items-center justify-end gap-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2.5 text-sm font-medium text-slate-600 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-all shadow-md shadow-blue-600/25 flex items-center gap-2 disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Initiating Agents...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  Execute Analysis
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

