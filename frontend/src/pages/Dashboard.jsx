import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api, BASE } from "../api";
import { useStockData } from "../hooks";
import Icon from "../components/Icon";
import Sidebar from "../components/Sidebar";
import Overview from "../components/Overview";
import SearchPanel from "../components/SearchPanel";
import PreferencesCard from "../components/PreferencesCard";
import StockView from "../components/StockView";
import ChartView from "../components/ChartView";
import EmptyState from "../components/EmptyState";
import ResearchTasks from "../components/ResearchTasks";
import WatchlistCard from "../components/WatchlistCard";
import ReportModal from "../components/ReportModal";
import ErrorBoundary from "../components/ErrorBoundary";

const VIEWS = ["dashboard", "search", "preferences", "chart", "watchlist", "history"];

const initialView = () => {
  const h = window.location.hash.slice(1);
  return VIEWS.includes(h) ? h : "dashboard";
};

export default function Dashboard() {
  const nav = useNavigate();
  const [user, setUser] = useState(null);
  const [unauth, setUnauth] = useState(false);
  const [prefs, setPrefs] = useState(null);
  const [view, setView] = useState(initialView);
  const [active, setActive] = useState(null); // stock being viewed: { ticker, market }
  const [range, setRange] = useState("1y");
  const [tasks, setTasks] = useState([]);
  const [saved, setSaved] = useState([]);
  const [toast, setToast] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [online, setOnline] = useState(true);
  const searchRef = useRef(null);

  const data = useStockData(active, range);

  const notify = useCallback((type, msg) => setToast({ type, msg, id: Date.now() }), []);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(t);
  }, [toast]);

  // keep the chosen view in the address bar (#search) so a refresh stays on it
  useEffect(() => {
    window.history.replaceState(null, "", `#${view}`);
    window.scrollTo({ top: 0 });
  }, [view]);

  const loadTasks = useCallback(() => api("/research").then(setTasks).catch(() => {}), []);
  const loadSaved = useCallback(() => api("/watchlist").then(setSaved).catch(() => {}), []);

  useEffect(() => {
    api("/auth/me").then(setUser).catch(() => setUnauth(true));
    api("/preferences").then(setPrefs).catch(() => setPrefs({ market: "NSE", analysis_period: "1y" }));
    loadTasks();
    loadSaved();
  }, [loadTasks, loadSaved]);

  useEffect(() => {
    const ping = () => fetch(`${BASE}/health`).then((r) => setOnline(r.ok)).catch(() => setOnline(false));
    ping();
    const id = setInterval(ping, 20000);
    return () => clearInterval(id);
  }, []);

  // keep polling while any research task is still running
  useEffect(() => {
    if (!tasks.some((t) => t.status === "pending" || t.status === "processing")) return;
    const id = setInterval(loadTasks, 3000);
    return () => clearInterval(id);
  }, [tasks, loadTasks]);

  const go = (id, focusSearch = false) => {
    setView(id);
    if (focusSearch) setTimeout(() => searchRef.current?.focus(), 0);
  };

  // open a stock's data: always lands on the Stock search view
  const openStock = (item) => {
    setActive({ ticker: item.ticker, market: item.market });
    setRange(prefs.analysis_period);
    setView("search");
  };

  const research = async ({ ticker, company_name, market, analysis_period }) => {
    try {
      await api("/research", {
        method: "POST",
        body: JSON.stringify({ ticker, company_name: company_name || null, market, analysis_period }),
      });
      notify("success", `Research started for ${ticker}. Follow it under Research history.`);
      loadTasks();
      if (view === "search") setActive({ ticker, market });
    } catch (e) {
      notify("error", e.message);
    }
  };

  const addWatch = async ({ ticker, company_name, market }) => {
    try {
      await api("/watchlist", {
        method: "POST",
        body: JSON.stringify({ ticker, company_name: company_name || null, market }),
      });
      notify("success", `${ticker} added to your watchlist.`);
      loadSaved();
    } catch (e) {
      notify("error", e.message);
    }
  };

  const removeWatch = async (s) => {
    try {
      await api(`/watchlist/${s.saved_stock_id}`, { method: "DELETE" });
      notify("success", `${s.ticker} removed from your watchlist.`);
      loadSaved();
    } catch (e) {
      notify("error", e.message);
    }
  };

  const savePrefs = async (p) => {
    try {
      setPrefs(await api("/preferences", { method: "PUT", body: JSON.stringify(p) }));
      notify("success", "Preferences saved.");
    } catch (e) {
      notify("error", e.message);
    }
  };

  const logout = async () => {
    await api("/auth/logout", { method: "POST" }).catch(() => {});
    nav("/login");
  };

  if (unauth) return <Navigate to="/login" replace />;
  if (!user || !prefs) return <p style={{ padding: 24, color: "var(--eq-muted)" }}>Loading your workspace…</p>;

  const TITLES = {
    dashboard: [`Welcome back, ${user.full_name.split(" ")[0]}`, "Here is where your research stands."],
    search: ["Stock search", "Look up a stock, check its data, then run a full research task."],
    preferences: ["Preferences", "Choose your default market and history length."],
    chart: ["Price chart", "Daily prices for the stock you are viewing."],
    watchlist: ["Watchlist", "Stocks you saved to come back to."],
    history: ["Research history", "Every research task you have run, newest first."],
  };
  const [title, subtitle] = TITLES[view];

  return (
    <div className="shell">
      <Sidebar
        user={user}
        counts={{ watch: saved.length, history: tasks.length }}
        online={online}
        current={view}
        onGo={go}
        onLogout={logout}
      />

      <div className="main">
        <header className="topbar">
          <div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div className="row">
            <button className="btn btn-primary" onClick={() => go("search", true)}>
              <Icon name="plus" /> New research
            </button>
            <button className="icon-btn only-mobile" onClick={logout} aria-label="Log out">
              <Icon name="logout" size={18} />
            </button>
          </div>
        </header>

        <main className="page">
          <ErrorBoundary key={view}>
          {toast && (
            <div className={`toast toast-${toast.type}`} role="status" key={toast.id}>
              <span>{toast.msg}</span>
              <button className="icon-btn" onClick={() => setToast(null)} aria-label="Dismiss">
                <Icon name="x" />
              </button>
            </div>
          )}

          {view === "dashboard" && (
            <Overview
              tasks={tasks}
              saved={saved}
              prefs={prefs}
              onGo={go}
              onOpen={setReportId}
              onView={openStock}
              onResearch={research}
              onRemove={removeWatch}
              onRefresh={loadTasks}
            />
          )}

          {view === "search" && (
            <>
              <SearchPanel
                prefs={prefs}
                saved={saved}
                active={active}
                inputRef={searchRef}
                onView={openStock}
                onResearch={research}
                onAddWatch={addWatch}
              />
              {active && data ? (
                <StockView
                  key={`${active.ticker}-${active.market}`}
                  active={active}
                  data={data}
                  range={range}
                  onRange={setRange}
                  saved={saved}
                  onAddWatch={addWatch}
                  onResearch={research}
                />
              ) : (
                <EmptyState onPick={openStock} />
              )}
            </>
          )}

          {view === "preferences" && <PreferencesCard prefs={prefs} onSave={savePrefs} />}

          {view === "chart" && (
            <ChartView
              active={active}
              data={data}
              range={range}
              onRange={setRange}
              onGoSearch={() => go("search", true)}
            />
          )}

          {view === "watchlist" && (
            <WatchlistCard saved={saved} prefs={prefs} onResearch={research} onRemove={removeWatch} onView={openStock} />
          )}

          {view === "history" && (
            <ResearchTasks tasks={tasks} onOpen={setReportId} onView={openStock} onRefresh={loadTasks} />
          )}
          </ErrorBoundary>
        </main>
      </div>

      {reportId && <ReportModal taskId={reportId} onClose={() => setReportId(null)} />}
    </div>
  );
}
