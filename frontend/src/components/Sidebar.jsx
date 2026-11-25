import Icon from "./Icon";

const ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: "grid" },
  { id: "search", label: "Stock search", icon: "search" },
  { id: "preferences", label: "Preferences", icon: "sliders" },
  { id: "chart", label: "Price chart", icon: "bar" },
  { id: "watchlist", label: "Watchlist", icon: "bookmark", count: "watch" },
  { id: "history", label: "Research history", icon: "clock", count: "history" },
];

export default function Sidebar({ user, counts, online, current, onGo, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark"><Icon name="trend" size={18} /></span>
        <div>
          <div className="brand-name">EquityLens</div>
          <div className="brand-sub">Multi-agent stock research</div>
        </div>
      </div>

      <nav className="nav" aria-label="Sections">
        {ITEMS.map((i) => (
          <button
            key={i.id}
            className={`nav-item ${current === i.id ? "is-active" : ""}`}
            onClick={() => onGo(i.id)}
          >
            <Icon name={i.icon} />
            <span>{i.label}</span>
            {i.count && <span className="nav-count">{counts[i.count]}</span>}
          </button>
        ))}
      </nav>

      <div className="engine">
        <div className="engine-row">
          <span className={`dot ${online ? "dot-up" : "dot-down"}`} />
          <strong>{online ? "API connected" : "API offline"}</strong>
        </div>
        <p>Market data pipeline is live. Analysis agents arrive in Weeks 3 to 6.</p>
      </div>

      <div className="user-chip">
        <span className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</span>
        <div className="user-meta">
          <strong>{user.full_name}</strong>
          <span>{user.email}</span>
        </div>
        <button className="icon-btn" onClick={onLogout} aria-label="Log out" title="Log out">
          <Icon name="logout" />
        </button>
      </div>
    </aside>
  );
}
