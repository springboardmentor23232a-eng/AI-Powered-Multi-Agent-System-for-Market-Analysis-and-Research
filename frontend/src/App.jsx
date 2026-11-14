import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";

const MARKETS = ["NSE", "BSE", "NASDAQ", "NYSE"];
const PERIODS = ["1 Month", "3 Months", "6 Months", "1 Year", "5 Years"];

function dateLabel(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric"
  });
}

function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [authMode, setAuthMode] = useState("login");
  const [activePage, setActivePage] = useState("overview");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: ""
  });

  const [watchlist, setWatchlist] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [preferences, setPreferences] = useState({
    market: "NSE",
    analysis_period: "1 Year"
  });

  const [searchText, setSearchText] = useState("");
  const [searchMarket, setSearchMarket] = useState("NSE");
  const [searchResults, setSearchResults] = useState([]);
  const [searchBusy, setSearchBusy] = useState(false);
  const [taskTicker, setTaskTicker] = useState("");
  const [report, setReport] = useState(null);

  const clearFeedback = () => {
    setNotice("");
    setError("");
  };

  
const loadWorkspace = useCallback(async () => {
  const results = await Promise.allSettled([
    api.getWatchlist(),
    api.getTasks(),
    api.getPreferences()
  ]);

  const errors = [];

  if (results[0].status === "fulfilled") {
    setWatchlist(results[0].value);
  } else {
    errors.push("Watchlist could not be loaded.");
  }

  if (results[1].status === "fulfilled") {
    setTasks(results[1].value);
  } else {
    errors.push("Research tasks could not be loaded.");
  }

  if (results[2].status === "fulfilled") {
    const savedPreferences = results[2].value;

    setPreferences({
      market: savedPreferences.market,
      analysis_period: savedPreferences.analysis_period
    });
  } else {
    errors.push("Preferences could not be loaded.");
  }

  if (errors.length > 0) {
    setError(errors.join(" "));
  }
}, []);


  useEffect(() => {
    api.me()
      .then(async (profile) => {
        setUser(profile);
        await loadWorkspace();
      })
      .catch(() => setUser(null))
      .finally(() => setCheckingSession(false));

    const handleExpired = () => {
      setUser(null);
      setError("Your session has expired. Please sign in again.");
    };

    window.addEventListener("session-expired", handleExpired);
    return () => window.removeEventListener("session-expired", handleExpired);
  }, [loadWorkspace]);

  async function handleRegister(event) {
    event.preventDefault();
    clearFeedback();

    if (registerForm.password !== registerForm.confirm_password) {
      setError("The passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      const result = await api.register(registerForm);
      setNotice(result.message);
      setLoginForm({ email: registerForm.email, password: "" });
      setRegisterForm({
        full_name: "",
        email: "",
        password: "",
        confirm_password: ""
      });
      setAuthMode("login");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  
async function handleLogin(event) {
  event.preventDefault();
  clearFeedback();
  setBusy(true);

  try {
    const profile = await api.login(loginForm);

    setUser(profile);
    setActivePage("overview");

    await loadWorkspace();

  } catch (err) {
    setError(err.message);
  } finally {
    setBusy(false);
  }
}


  async function handleLogout() {
    clearFeedback();
    setBusy(true);
    try {
      await api.logout();
      setUser(null);
      setWatchlist([]);
      setTasks([]);
      setActivePage("overview");
      setNotice("You have been signed out.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function runStockSearch(event) {
    event.preventDefault();
    clearFeedback();

    if (!searchText.trim()) {
      setError("Enter a company name or ticker first.");
      return;
    }

    setSearchBusy(true);
    try {
      const results = await api.searchStocks(searchText.trim(), searchMarket);
      setSearchResults(results);
      if (results.length === 0) {
        setNotice("No matching stocks were found for this market.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSearchBusy(false);
    }
  }

  async function addStock(stock) {
    clearFeedback();
    try {
      await api.addStock(stock);
      await loadWorkspace();
      setNotice(`${stock.ticker} has been added to your watchlist.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function removeStock(id) {
    clearFeedback();
    try {
      await api.removeStock(id);
      await loadWorkspace();
      setNotice("Stock removed from your watchlist.");
    } catch (err) {
      setError(err.message);
    }
  }

  async function savePreferences(event) {
    event.preventDefault();
    clearFeedback();
    setBusy(true);
    try {
      const saved = await api.savePreferences(preferences);
      setPreferences({
        market: saved.market,
        analysis_period: saved.analysis_period
      });
      setNotice("Your research preferences have been saved.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function startResearch(stock) {
    clearFeedback();
    try {
      const created = await api.createTask({
        ticker: stock.ticker,
        company_name: stock.company_name,
        market: stock.market || preferences.market,
        analysis_period: preferences.analysis_period
      });
      await loadWorkspace();
      setTaskTicker("");
      setActivePage("history");
      setNotice(`Research request for ${created.ticker} was saved.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function openReport(task) {
    clearFeedback();
    setActivePage("history");
    try {
      const result = await api.getReport(task.task_id);
      setReport(result);
    } catch (err) {
      setError(err.message);
    }
  }

  const completedCount = useMemo(
    () => tasks.filter((task) => task.status === "Completed").length,
    [tasks]
  );

  if (checkingSession) {
    return <div className="loading-screen"><span className="spinner" />Checking your session…</div>;
  }

  if (!user) {
    return (
      <div className="auth-layout">
        <section className="auth-story">
          <div className="brand"><span className="brand-icon">S</span> Stock Research Analyst</div>
          <div className="story-copy">
            <span className="kicker">YOUR MARKET RESEARCH WORKSPACE</span>
            <h1>Make room for<br /><span>better questions.</span></h1>
            <p>Keep the companies you follow, your research activity and your preferred markets together in one workspace.</p>
          </div>
          <div className="story-bottom"><span>Multi-Agent Stock Research Analyst</span><span>MODULE 01</span></div>
        </section>

        <section className="auth-main">
          <div className="auth-card">
            <span className="kicker">{authMode === "login" ? "WELCOME BACK" : "GET STARTED"}</span>
            <h2>{authMode === "login" ? "Sign in to your account" : "Create your account"}</h2>
            <p className="muted">{authMode === "login" ? "Pick up where your research left off." : "A few details are all you need to get started."}</p>

            {notice && <div className="feedback success">{notice}</div>}
            {error && <div className="feedback error">{error}</div>}

            {authMode === "login" ? (
              <form className="form-stack" onSubmit={handleLogin}>
                <label>Email address<input type="email" autoComplete="email" required value={loginForm.email} onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })} placeholder="name@example.com" /></label>
                <label>Password<input type="password" autoComplete="current-password" required value={loginForm.password} onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })} placeholder="Your password" /></label>
                <button className="btn primary" disabled={busy}>{busy ? "Signing in…" : "Sign in"} <span>→</span></button>
              </form>
            ) : (
              <form className="form-stack" onSubmit={handleRegister}>
                <label>Full name<input type="text" autoComplete="name" minLength="2" maxLength="120" required value={registerForm.full_name} onChange={(e) => setRegisterForm({ ...registerForm, full_name: e.target.value })} placeholder="Your full name" /></label>
                <label>Email address<input type="email" autoComplete="email" required value={registerForm.email} onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })} placeholder="name@example.com" /></label>
                <label>Password<input type="password" autoComplete="new-password" minLength="8" required value={registerForm.password} onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })} placeholder="At least 8 characters" /></label>
                <label>Confirm password<input type="password" autoComplete="new-password" minLength="8" required value={registerForm.confirm_password} onChange={(e) => setRegisterForm({ ...registerForm, confirm_password: e.target.value })} placeholder="Enter the password again" /></label>
                <button className="btn primary" disabled={busy}>{busy ? "Creating account…" : "Create account"} <span>→</span></button>
              </form>
            )}

            <div className="or-divider"><span>OR</span></div>
            <button className="btn google" onClick={() => { window.location.href = api.googleLoginUrl; }}>
              <b className="google-mark">G</b> Continue with Google
            </button>
            <p className="auth-switch">
              {authMode === "login" ? "New to the workspace?" : "Already have an account?"}
              <button onClick={() => { clearFeedback(); setAuthMode(authMode === "login" ? "register" : "login"); }}>
                {authMode === "login" ? "Create an account" : "Sign in"}
              </button>
            </p>
            <p className="small-print">Your password is stored as a secure hash. Your session is protected by a signed token.</p>
          </div>
        </section>
      </div>
    );
  }

  const navItems = [
    ["overview", "Overview", "⌂"],
    ["watchlist", "Watchlist", "☆"],
    ["history", "Research history", "◷"],
    ["preferences", "Preferences", "⚙"]
  ];

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand"><span className="brand-icon">S</span><span>Stock Research<br />Analyst</span></div>
        <div className="side-caption">WORKSPACE</div>
        <nav>
          {navItems.map(([key, label, icon]) => (
            <button key={key} className={`nav-item ${activePage === key ? "selected" : ""}`} onClick={() => { setActivePage(key); clearFeedback(); setReport(null); }}>
              <span>{icon}</span>{label}
              {key === "watchlist" && <small>{watchlist.length}</small>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="user-mini"><div className="avatar">{user.full_name.charAt(0).toUpperCase()}</div><div><strong>{user.full_name}</strong><span>{user.email}</span></div></div>
          <button className="signout" onClick={handleLogout} disabled={busy}>↗ Sign out</button>
        </div>
      </aside>

      <main className="main-area">
        <header className="page-header">
          <div><span className="kicker">STOCK RESEARCH WORKSPACE</span><h1>{navItems.find((item) => item[0] === activePage)?.[1]}</h1></div>
          <div className="header-user"><span className="online-dot" /> Signed in as {user.full_name.split(" ")[0]}</div>
        </header>

        {(notice || error) && (
          <div className={`global-feedback ${error ? "error" : "success"}`}>
            {error || notice}
            <button onClick={clearFeedback}>×</button>
          </div>
        )}

        {activePage === "overview" && (
          <section className="content">
            <div className="welcome-row">
              <div><span className="kicker">YOUR PERSONAL RESEARCH SPACE</span><h2>Good to have you here, {user.full_name.split(" ")[0]}.</h2><p className="muted">Your watchlist and recent research activity are ready when you are.</p></div>
              <button className="btn primary compact" onClick={() => setActivePage("watchlist")}>Explore stocks <span>→</span></button>
            </div>
            <div className="stat-grid">
              <div className="stat-card"><span>Saved stocks</span><strong>{watchlist.length}</strong><small>Companies in your watchlist</small></div>
              <div className="stat-card"><span>Research requests</span><strong>{tasks.length}</strong><small>Requests saved to your history</small></div>
              <div className="stat-card"><span>Completed reports</span><strong>{completedCount}</strong><small>Reports ready to view</small></div>
            </div>
            <div className="section-heading"><div><span className="kicker">RECENT ACTIVITY</span><h3>Your latest research</h3></div><button className="text-button" onClick={() => setActivePage("history")}>View history →</button></div>
            {tasks.length ? <TaskTable tasks={tasks.slice(0, 5)} onOpen={openReport} /> : <EmptyState title="No research activity yet" text="When you start researching a company, your requests will appear here." action="Browse your watchlist" onClick={() => setActivePage("watchlist")} />}
            <div className="tip-card"><div className="tip-icon">✦</div><div><strong>A small tip</strong><p>Set your preferred market and analysis period once. New research requests will use those settings by default.</p></div><button className="text-button" onClick={() => setActivePage("preferences")}>Set preferences →</button></div>
          </section>
        )}

        {activePage === "watchlist" && (
          <section className="content">
            <div className="intro-block"><span className="kicker">KEEP AN EYE ON WHAT MATTERS</span><h2>Your watchlist</h2><p className="muted">Search for a company or ticker, then save it here so it is easy to find next time.</p></div>
            <form className="search-panel" onSubmit={runStockSearch}>
              <div className="search-input-wrap"><span>⌕</span><input value={searchText} onChange={(e) => setSearchText(e.target.value)} placeholder="Search by company name or ticker (e.g. TCS)" /></div>
              <select value={searchMarket} onChange={(e) => setSearchMarket(e.target.value)}>{MARKETS.map((market) => <option key={market}>{market}</option>)}</select>
              <button className="btn primary" disabled={searchBusy}>{searchBusy ? "Searching…" : "Search stocks"}</button>
            </form>
            {searchResults.length > 0 && <div className="results-panel"><div className="section-heading"><h3>Search results</h3><span className="muted">{searchResults.length} matches</span></div>{searchResults.map((stock) => <div className="result-row" key={`${stock.ticker}-${stock.market}`}><div><strong>{stock.company_name}</strong><span>{stock.ticker} · {stock.exchange}</span></div><button className="btn outline compact" onClick={() => addStock(stock)}>＋ Add</button></div>)}</div>}
            <div className="section-heading"><div><span className="kicker">YOUR SAVED COMPANIES</span><h3>Saved stocks <span className="count-pill">{watchlist.length}</span></h3></div></div>
            {watchlist.length ? <div className="stock-grid">{watchlist.map((stock) => <article className="stock-card" key={stock.saved_stock_id}><div className="stock-symbol">{stock.ticker.slice(0, 2)}</div><div className="stock-details"><strong>{stock.company_name}</strong><span>{stock.ticker} · {stock.market}</span></div><div className="stock-actions"><button className="text-button" onClick={() => startResearch(stock)}>Research →</button><button className="icon-button" title="Remove stock" onClick={() => removeStock(stock.saved_stock_id)}>×</button></div></article>)}</div> : <EmptyState title="Your watchlist is empty" text="Use the search above to find a company and add it to your list." />}
          </section>
        )}

        {activePage === "history" && (
          <section className="content">
            <div className="intro-block"><span className="kicker">YOUR RESEARCH, IN ONE PLACE</span><h2>Research history</h2><p className="muted">Each request is tied to your account, so your activity stays personal.</p></div>
            <div className="create-task-panel">
              <div><strong>Start a research request</strong><p className="muted">Choose a stock from your watchlist to add it to your history.</p></div>
              <select value={taskTicker} onChange={(e) => setTaskTicker(e.target.value)}><option value="">Choose a saved stock</option>{watchlist.map((stock) => <option key={stock.saved_stock_id} value={stock.saved_stock_id}>{stock.ticker} — {stock.company_name}</option>)}</select>
              <button className="btn primary" disabled={!taskTicker} onClick={() => { const stock = watchlist.find((item) => String(item.saved_stock_id) === taskTicker); if (stock) startResearch(stock); }}>Create request</button>
            </div>
            {tasks.length ? <TaskTable tasks={tasks} onOpen={openReport} /> : <EmptyState title="Nothing here yet" text="Create a research request from one of your saved stocks to begin your history." action="Go to watchlist" onClick={() => setActivePage("watchlist")} />}
            {report && <div className="report-modal-backdrop" onClick={() => setReport(null)}><article className="report-modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setReport(null)}>×</button><span className="kicker">RESEARCH REPORT</span><h2>{report.title}</h2><p className="muted">{report.summary}</p><div className="report-body">{report.report_body}</div><small className="muted">Created {dateLabel(report.created_at)}</small></article></div>}
          </section>
        )}

        {activePage === "preferences" && (
          <section className="content narrow-content">
            <div className="intro-block"><span className="kicker">MAKE THE WORKSPACE YOURS</span><h2>Research preferences</h2><p className="muted">Choose a default market and analysis period. You can change these whenever you need to.</p></div>
            <form className="preferences-card" onSubmit={savePreferences}>
              <label>Preferred stock market<span>Choose the exchange you usually follow.</span><select value={preferences.market} onChange={(e) => setPreferences({ ...preferences, market: e.target.value })}>{MARKETS.map((market) => <option key={market}>{market}</option>)}</select></label>
              <label>Default analysis period<span>How far back should a new research request look?</span><select value={preferences.analysis_period} onChange={(e) => setPreferences({ ...preferences, analysis_period: e.target.value })}>{PERIODS.map((period) => <option key={period}>{period}</option>)}</select></label>
              <button className="btn primary" disabled={busy}>{busy ? "Saving…" : "Save preferences"}</button>
            </form>
            <div className="notice-card"><strong>About your preferences</strong><p>These settings are saved to your account in PostgreSQL. When a research request is created without a specific market or period, the backend uses these defaults.</p></div>
          </section>
        )}
      </main>
    </div>
  );
}

function TaskTable({ tasks, onOpen }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Company</th><th>Market</th><th>Period</th><th>Research date</th><th>Status</th><th>Report</th></tr></thead>
        <tbody>{tasks.map((task) => <tr key={task.task_id}><td><strong>{task.company_name}</strong><span className="table-sub">{task.ticker}</span></td><td>{task.market}</td><td>{task.analysis_period}</td><td>{dateLabel(task.created_at)}</td><td><span className={`status status-${task.status.toLowerCase()}`}>{task.status}</span></td><td>{task.status === "Completed" ? <button className="text-button" onClick={() => onOpen(task)}>Open report →</button> : <span className="muted">Not ready</span>}</td></tr>)}</tbody>
      </table>
    </div>
  );
}

function EmptyState({ title, text, action, onClick }) {
  return <div className="empty-state"><div className="empty-symbol">⌁</div><strong>{title}</strong><p>{text}</p>{action && <button className="text-button" onClick={onClick}>{action} →</button>}</div>;
}

export default App;
