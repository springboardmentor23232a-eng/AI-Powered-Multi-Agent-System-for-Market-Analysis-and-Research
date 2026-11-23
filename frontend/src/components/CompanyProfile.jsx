import { useState } from "react";
import API from "../services/api";

function CompanyProfile() {
  const [symbol, setSymbol] = useState("RELIANCE");
  const [exchange, setExchange] = useState("NSI");
  const [profile, setProfile] = useState(null);
  const [searchedTicker, setSearchedTicker] = useState("");
  const [retrievedAt, setRetrievedAt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchProfile = async (e) => {
    e.preventDefault();

    if (!symbol.trim()) {
      setError("Please enter a company name or ticker symbol.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setProfile(null);

      const ticker = symbol.trim().toUpperCase();

      const response = await API.get(`/market-data/${ticker}/profile`, {
        params: { exchange },
      });

      setProfile(response.data.profile);
      setSearchedTicker(response.data.ticker);
      setRetrievedAt(response.data.retrieved_at);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to fetch company profile.",
      );
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value) => {
    if (value === null || value === undefined || value === "") {
      return "Not available";
    }

    return value;
  };

  const formatMarketCap = (value) => {
    if (value === null || value === undefined) {
      return "Not available";
    }

    return Number(value).toLocaleString("en-IN");
  };

  return (
    <div className="company-profile-container">
      <h2>Company Profile</h2>

      <p>View company information, business details, and market information.</p>

      <form onSubmit={fetchProfile} className="company-profile-form">
        <input
          type="text"
          placeholder="Enter company symbol (e.g. RELIANCE)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />

        <select value={exchange} onChange={(e) => setExchange(e.target.value)}>
          <option value="NSI">NSE</option>
          <option value="BSE">BSE</option>
          <option value="NASDAQ">NASDAQ</option>
          <option value="NYSE">NYSE</option>
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Get Profile"}
        </button>
      </form>

      {error && <p className="company-profile-error">{error}</p>}

      {profile && (
        <div className="company-profile-results">
          <h3>{formatValue(profile.company_name)}</h3>

          <div className="company-profile-grid">
            <div className="company-profile-item">
              <span>Sector</span>
              <strong>{formatValue(profile.sector)}</strong>
            </div>

            <div className="company-profile-item">
              <span>Industry</span>
              <strong>{formatValue(profile.industry)}</strong>
            </div>

            <div className="company-profile-item">
              <span>Country</span>
              <strong>{formatValue(profile.country)}</strong>
            </div>

            <div className="company-profile-item">
              <span>City</span>
              <strong>{formatValue(profile.city)}</strong>
            </div>

            <div className="company-profile-item">
              <span>Exchange</span>
              <strong>{formatValue(profile.exchange)}</strong>
            </div>

            <div className="company-profile-item">
              <span>Currency</span>
              <strong>{formatValue(profile.currency)}</strong>
            </div>

            <div className="company-profile-item">
              <span>Market Capitalization</span>
              <strong>{formatMarketCap(profile.market_cap)}</strong>
            </div>

            <div className="company-profile-item">
              <span>Employees</span>
              <strong>{formatValue(profile.employees)}</strong>
            </div>
          </div>

          <div className="company-profile-description">
            <h4>Business Description</h4>
            <p>{formatValue(profile.business_description)}</p>
          </div>

          <div className="company-profile-website">
            <strong>Website: </strong>
            {profile.website ? (
              <a
                href={profile.website}
                target="_blank"
                rel="noopener noreferrer"
              >
                {profile.website}
              </a>
            ) : (
              "Not available"
            )}
          </div>

          <p className="company-profile-meta">Ticker: {searchedTicker}</p>

          <p className="company-profile-meta">
            Data source: Yahoo Finance (via yfinance)
          </p>

          <p className="company-profile-meta">Retrieved at: {retrievedAt}</p>
        </div>
      )}
    </div>
  );
}

export default CompanyProfile;
