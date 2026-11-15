import { useEffect, useState } from "react";
import API from "../services/api";

function Preferences() {
  const [market, setMarket] = useState("NSI");
  const [analysisPeriod, setAnalysisPeriod] = useState("1y");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Load saved preferences
  useEffect(() => {
    async function fetchPreferences() {
      try {
        const response = await API.get("/preferences/");

        setMarket(response.data.market);
        setAnalysisPeriod(response.data.analysis_period);
      } catch (err) {
        console.error("Failed to load preferences:", err);
        setError("Unable to load your preferences.");
      } finally {
        setLoading(false);
      }
    }

    fetchPreferences();
  }, []);

  // Save preferences
  async function savePreferences() {
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const response = await API.put("/preferences/", {
        market,
        analysis_period: analysisPeriod,
      });

      setMarket(response.data.market);
      setAnalysisPeriod(response.data.analysis_period);

      // Notify other components about updated preferences
      window.dispatchEvent(
        new CustomEvent("preferencesUpdated", {
          detail: {
            market: response.data.market,
            analysis_period: response.data.analysis_period,
          },
        }),
      );

      setMessage("Preferences saved successfully!");
    } catch (err) {
      console.error("Failed to save preferences:", err.response?.data);

      setError(err.response?.data?.detail || "Unable to save preferences.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p>Loading preferences...</p>;
  }

  return (
    <div className="preferences-container">
      <h2>User Preferences</h2>

      <p>
        Customize your preferred stock market and historical analysis period.
      </p>

      {error && <p className="preferences-error">{error}</p>}

      <div className="preferences-form">
        <div className="preference-field">
          <label htmlFor="preferred-market">Preferred Stock Market</label>

          <select
            id="preferred-market"
            value={market}
            onChange={(event) => setMarket(event.target.value)}
          >
            <option value="NSI">NSE - India</option>
            <option value="BSE">BSE - India</option>
            <option value="NASDAQ">NASDAQ - USA</option>
            <option value="NYSE">NYSE - USA</option>
          </select>
        </div>

        <div className="preference-field">
          <label htmlFor="preferred-period">Default Analysis Period</label>

          <select
            id="preferred-period"
            value={analysisPeriod}
            onChange={(event) => setAnalysisPeriod(event.target.value)}
          >
            <option value="1mo">1 Month</option>
            <option value="3mo">3 Months</option>
            <option value="6mo">6 Months</option>
            <option value="1y">1 Year</option>
            <option value="5y">5 Years</option>
          </select>
        </div>

        <button
          className="save-preferences-button"
          onClick={savePreferences}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save Preferences"}
        </button>

        {message && <p className="preferences-success">{message}</p>}
      </div>
    </div>
  );
}

export default Preferences;
