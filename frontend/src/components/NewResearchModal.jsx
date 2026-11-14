import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../services/api";
import {
  X,
  PlusCircle,
  TrendingUp,
  Globe,
  Clock,
  Loader2,
  AlertCircle,
  Sparkles,
} from "lucide-react";

const SUGGESTED_TICKERS = ["AAPL", "NVDA", "TSLA", "RELIANCE", "TCS", "MSFT"];

export default function NewResearchModal({ isOpen, onClose, initialData = null, onSuccess }) {
  const { user } = useAuth();

  const [ticker, setTicker] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [market, setMarket] = useState("NASDAQ");
  const [period, setPeriod] = useState("1 Year");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (initialData) {
      setTicker(initialData.ticker || "");
      setCompanyName(initialData.company_name || "");
      if (initialData.market) setMarket(initialData.market);
    } else {
      setTicker("");
      setCompanyName("");
      setMarket(user?.preferences?.market || "NASDAQ");
    }
    setPeriod(user?.preferences?.analysis_period || "1 Year");
    setError("");
  }, [initialData, user, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!ticker.trim()) {
      setError("Please enter a stock ticker symbol.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const createdTask = await api.startResearchTask({
        ticker: ticker.trim().toUpperCase(),
        company_name: companyName.trim() || undefined,
        market,
        analysis_period: period,
      });

      if (onSuccess) {
        onSuccess(createdTask);
      }
      onClose();
    } catch (err) {
      setError(err.message || "Failed to start research task");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <div className="modal-title-with-icon">
            <PlusCircle size={20} className="text-accent" />
            <h3>Launch Multi-Agent Stock Research</h3>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {error && (
            <div className="alert alert-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="form-group">
            <label>Stock Ticker Symbol</label>
            <input
              type="text"
              required
              placeholder="e.g. AAPL, TSLA, NVDA, RELIANCE..."
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              className="form-input text-uppercase font-mono"
            />
            <div className="quick-suggestions">
              <span className="suggestion-label">Quick Suggestions:</span>
              {SUGGESTED_TICKERS.map((t) => (
                <button
                  type="button"
                  key={t}
                  className="ticker-chip"
                  onClick={() => setTicker(t)}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Company Name (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Apple Inc. (Auto-resolved if blank)"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-row">
            <div className="form-group flex-1">
              <label>
                <Globe size={14} className="inline-icon" /> Market / Exchange
              </label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="form-select"
              >
                <option value="NASDAQ">NASDAQ (US)</option>
                <option value="NYSE">NYSE (US)</option>
                <option value="NSE">NSE (India)</option>
                <option value="BSE">BSE (India)</option>
              </select>
            </div>

            <div className="form-group flex-1">
              <label>
                <Clock size={14} className="inline-icon" /> Historical Period
              </label>
              <select
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                className="form-select"
              >
                <option value="1 Month">1 Month</option>
                <option value="3 Months">3 Months</option>
                <option value="6 Months">6 Months</option>
                <option value="1 Year">1 Year</option>
                <option value="5 Years">5 Years</option>
              </select>
            </div>
          </div>

          <div className="agent-pipeline-preview">
            <div className="pipeline-title">
              <Sparkles size={14} className="text-accent" /> Autonomous Agents to Deploy:
            </div>
            <div className="pipeline-badges">
              <span className="pipeline-badge">Fundamental Valuation</span>
              <span className="pipeline-badge">Technical Momentum</span>
              <span className="pipeline-badge">Sentiment & Risk</span>
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 size={16} className="spin inline-icon" /> Synthesizing Analysis...
                </>
              ) : (
                "Launch Research Task"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
