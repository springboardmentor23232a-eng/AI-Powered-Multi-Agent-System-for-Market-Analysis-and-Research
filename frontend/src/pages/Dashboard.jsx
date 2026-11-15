import { useEffect, useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import API from "../services/api";
import "./Dashboard.css";
import MarketChart from "../components/MarketChart";
import Watchlist from "../components/Watchlist";
import StockComparisonChart from "../components/StockComparisonChart";
import MarketMovers from "../components/MarketMovers";
import StockSearch from "../components/StockSearch";
import StockHistoryChart from "../components/StockHistoryChart";
import ResearchHistory from "../components/ResearchHistory";
import Preferences from "../components/Preferences";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem("marketmind-theme") === "dark",
  );

  function toggleTheme() {
    setDarkMode((previous) => {
      const newTheme = !previous;

      localStorage.setItem("marketmind-theme", newTheme ? "dark" : "light");

      return newTheme;
    });
  }
  const [marketOverview, setMarketOverview] = useState({
    nifty: null,
    sensex: null,
    loading: true,
    error: "",
  });
  const [researchCount, setResearchCount] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchUser() {
      try {
        const response = await API.get("/auth/me");
        setUser(response.data);
      } catch (err) {
        console.error("Failed to fetch user:", err);

        sessionStorage.removeItem("access_token");
        navigate("/login", { replace: true });
      }
    }

    fetchUser();
  }, [navigate]);
  useEffect(() => {
    async function fetchMarketOverview() {
      try {
        const [niftyResponse, sensexResponse] = await Promise.all([
          API.get("/market-data/^NSEI"),
          API.get("/market-data/^BSESN"),
        ]);

        setMarketOverview({
          nifty: niftyResponse.data,
          sensex: sensexResponse.data,
          loading: false,
          error: "",
        });
      } catch (err) {
        console.error("Failed to fetch market overview:", err);

        setMarketOverview((previous) => ({
          ...previous,
          loading: false,
          error: "Unable to load market overview.",
        }));
      }
    }

    fetchMarketOverview();
  }, []);
  useEffect(() => {
    async function fetchResearchCount() {
      try {
        const response = await API.get("/research/tasks");
        setResearchCount(response.data.length);
      } catch (err) {
        console.error("Failed to fetch research count:", err);
      }
    }

    fetchResearchCount();

    window.addEventListener("researchHistoryUpdated", fetchResearchCount);

    return () => {
      window.removeEventListener("researchHistoryUpdated", fetchResearchCount);
    };
  }, []);
  function handleLogout() {
    sessionStorage.removeItem("access_token");
    navigate("/login", { replace: true });
  }

  if (!user) {
    return <p>Loading dashboard...</p>;
  }

  return (
    <div className={`dashboard-container ${darkMode ? "dark-mode" : ""}`}>
      {/* Sidebar */}
      <aside className="dashboard-sidebar">
        <div className="dashboard-logo">Stock Analyst</div>

        <nav className="dashboard-nav">
          <nav className="dashboard-nav">
            <a href="#overview">Overview</a>
            <a href="#market-analysis">Market Analysis</a>
            <a href="#research-history">AI Research Agents</a>
            <a href="#watchlist">Watchlist</a>
            <a href="#watchlist">Portfolio</a>
          </nav>
        </nav>

        <button className="logout-button" onClick={handleLogout}>
          Logout
        </button>
      </aside>

      {/* Main Dashboard */}
      <main className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <h1>Dashboard Overview</h1>
            <p>Welcome to your Stock Research Analyst workspace.</p>
          </div>

          <div className="dashboard-header-actions">
            <button className="theme-toggle-button" onClick={toggleTheme}>
              {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
            </button>

            <div className="dashboard-user">{user.full_name}</div>
          </div>
        </header>

        <section className="dashboard-content account-summary">
          <div className="account-summary-header">
            <div>
              <span className="account-label">ACCOUNT OVERVIEW</span>
              <h2>Welcome back, {user.full_name}!</h2>
              <p>
                Manage your account information and monitor your profile status.
              </p>
            </div>

            <span
              className={`account-status ${
                user.is_active ? "active" : "inactive"
              }`}
            >
              {user.is_active ? "● Active" : "● Inactive"}
            </span>
          </div>

          <div className="account-details">
            <div className="account-detail-card">
              <span>EMAIL ADDRESS</span>
              <h3>{user.email}</h3>
            </div>

            <div className="account-detail-card">
              <span>ACCOUNT STATUS</span>
              <h3>{user.is_active ? "Verified Active" : "Inactive"}</h3>
            </div>
          </div>
        </section>

        <section className="overview-cards" id="overview">
          <div className="overview-card">
            <h3>NIFTY 50</h3>

            <h2>
              {marketOverview.loading
                ? "Loading..."
                : marketOverview.nifty
                  ? `₹${marketOverview.nifty.current_price.toLocaleString("en-IN")}`
                  : "N/A"}
            </h2>

            <p
              className={
                marketOverview.nifty?.percentage_change >= 0
                  ? "positive-value"
                  : "negative-value"
              }
            >
              {marketOverview.nifty?.percentage_change != null
                ? `${marketOverview.nifty.percentage_change >= 0 ? "+" : ""}${marketOverview.nifty.percentage_change.toFixed(2)}%`
                : "Change unavailable"}
            </p>

            <p className="card-description">Indian Stock Market Index</p>
          </div>

          <div className="overview-card">
            <h3>SENSEX</h3>

            <h2>
              {marketOverview.loading
                ? "Loading..."
                : marketOverview.sensex
                  ? `₹${marketOverview.sensex.current_price.toLocaleString("en-IN")}`
                  : "N/A"}
            </h2>

            <p
              className={
                marketOverview.sensex?.percentage_change >= 0
                  ? "positive-value"
                  : "negative-value"
              }
            >
              {marketOverview.sensex?.percentage_change != null
                ? `${marketOverview.sensex.percentage_change >= 0 ? "+" : ""}${marketOverview.sensex.percentage_change.toFixed(2)}%`
                : "Change unavailable"}
            </p>

            <p className="card-description">BSE Stock Market Index</p>
          </div>

          <div className="overview-card">
            <h3>MARKET DATA</h3>

            <h2>
              {marketOverview.loading
                ? "Loading..."
                : marketOverview.error
                  ? "Unavailable"
                  : "Connected"}
            </h2>

            <p className="card-description">
              Live index data via Yahoo Finance
            </p>
          </div>

          <div className="overview-card">
            <h3>AI RESEARCH TASKS</h3>
            <h2>{researchCount}</h2>
            <p className="card-description">Total research tasks created</p>
          </div>
        </section>
        <div className="dashboard-content" id="market-analysis">
          <StockSearch />
        </div>
        <section className="dashboard-content">
          <MarketChart />
        </section>
        <section className="dashboard-content">
          <StockHistoryChart />
        </section>
        <section className="dashboard-content">
          <StockComparisonChart />
        </section>
        <section className="dashboard-content">
          <MarketMovers />
        </section>
        <section className="dashboard-content" id="watchlist">
          <Watchlist />
        </section>
        <section className="dashboard-content" id="research-history">
          <ResearchHistory />
        </section>
        <section className="dashboard-content">
          <Preferences />
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
