import React, { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { X, Sliders, Globe, Clock, CheckCircle2, AlertCircle } from "lucide-react";

const MARKETS = [
  { id: "NASDAQ", name: "NASDAQ", desc: "US Technology & Growth Equities (e.g. AAPL, NVDA, TSLA)" },
  { id: "NYSE", name: "NYSE", desc: "New York Stock Exchange (e.g. JPM, WMT, DIS)" },
  { id: "NSE", name: "NSE", desc: "National Stock Exchange of India (e.g. RELIANCE, TCS, INFY)" },
  { id: "BSE", name: "BSE", desc: "BSE Limited, India (e.g. ITC, SBIN, LT)" },
];

const PERIODS = [
  { id: "1 Month", label: "1 Month (Short-term momentum)" },
  { id: "3 Months", label: "3 Months (Quarterly cycle)" },
  { id: "6 Months", label: "6 Months (Mid-term trend)" },
  { id: "1 Year", label: "1 Year (Standard institutional baseline)" },
  { id: "5 Years", label: "5 Years (Long-term secular cycle)" },
];

export default function PreferencesModal({ isOpen, onClose }) {
  const { user, updatePreferences } = useAuth();

  const [market, setMarket] = useState("NASDAQ");
  const [analysisPeriod, setAnalysisPeriod] = useState("1 Year");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (user?.preferences) {
      if (user.preferences.market) setMarket(user.preferences.market);
      if (user.preferences.analysis_period) setAnalysisPeriod(user.preferences.analysis_period);
    }
  }, [user]);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      await updatePreferences(market, analysisPeriod);
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 900);
    } catch (err) {
      setError(err.message || "Failed to update preferences");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog">
        <div className="modal-header">
          <div className="modal-title-with-icon">
            <Sliders size={20} className="text-accent" />
            <h3>Market & Analysis Preferences</h3>
          </div>
          <button className="modal-close-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSave} className="modal-body">
          {error && (
            <div className="alert alert-error">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              <CheckCircle2 size={16} />
              <span>Preferences saved and synced with research engine!</span>
            </div>
          )}

          <div className="form-section">
            <label className="section-label">
              <Globe size={16} /> Default Market / Exchange
            </label>
            <div className="options-grid">
              {MARKETS.map((m) => (
                <div
                  key={m.id}
                  className={`option-card ${market === m.id ? "selected" : ""}`}
                  onClick={() => setMarket(m.id)}
                >
                  <div className="option-header">
                    <span className="option-code">{m.name}</span>
                    {market === m.id && <span className="option-check">●</span>}
                  </div>
                  <p className="option-desc">{m.desc}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="form-section">
            <label className="section-label">
              <Clock size={16} /> Default Historical Analysis Period
            </label>
            <div className="options-list">
              {PERIODS.map((p) => (
                <label
                  key={p.id}
                  className={`radio-card ${analysisPeriod === p.id ? "selected" : ""}`}
                >
                  <input
                    type="radio"
                    name="analysis_period"
                    value={p.id}
                    checked={analysisPeriod === p.id}
                    onChange={(e) => setAnalysisPeriod(e.target.value)}
                  />
                  <span>{p.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Saving Preferences..." : "Save Preferences"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
