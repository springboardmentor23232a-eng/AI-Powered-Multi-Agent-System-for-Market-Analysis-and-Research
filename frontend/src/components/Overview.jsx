import Icon from "./Icon";
import ResearchTasks from "./ResearchTasks";
import WatchlistCard from "./WatchlistCard";

export default function Overview({ tasks, saved, prefs, onGo, onOpen, onView, onResearch, onRemove, onRefresh }) {
  const done = tasks.filter((t) => t.status === "completed").length;
  const running = tasks.filter((t) => t.status === "pending" || t.status === "processing").length;

  return (
    <div className="stack">
      <div className="quote-grid">
        <button className="panel stat stat-btn" onClick={() => onGo("watchlist")}>
          <span className="stat-label">Saved stocks</span>
          <div className="stat-value display">{saved.length}</div>
          <div className="stat-foot"><span>Open watchlist</span></div>
        </button>
        <button className="panel stat stat-btn" onClick={() => onGo("history")}>
          <span className="stat-label">Research tasks</span>
          <div className="stat-value display">{tasks.length}</div>
          <div className="stat-foot"><span>Open research history</span></div>
        </button>
        <button className="panel stat stat-btn" onClick={() => onGo("history")}>
          <span className="stat-label">Reports ready</span>
          <div className="stat-value display">{done}</div>
          <div className="stat-foot"><span>{running ? `${running} still running` : "Nothing running"}</span></div>
        </button>
        <button className="panel stat stat-btn" onClick={() => onGo("preferences")}>
          <span className="stat-label">Default market</span>
          <div className="stat-value display">{prefs.market}</div>
          <div className="stat-foot"><span>Change preferences</span></div>
        </button>
      </div>

      <section className="panel cta">
        <div>
          <h2 className="panel-title">Research a stock</h2>
          <p className="panel-sub">Search by company name or ticker, view its data, then run a full research task.</p>
        </div>
        <button className="btn btn-primary" onClick={() => onGo("search", true)}>
          <Icon name="search" /> Open stock search
        </button>
      </section>

      <div className="two-col">
        <ResearchTasks tasks={tasks} limit={5} onViewAll={() => onGo("history")} onOpen={onOpen} onView={onView} onRefresh={onRefresh} />
        <WatchlistCard saved={saved} prefs={prefs} limit={5} onViewAll={() => onGo("watchlist")} onResearch={onResearch} onRemove={onRemove} onView={onView} />
      </div>
    </div>
  );
}
