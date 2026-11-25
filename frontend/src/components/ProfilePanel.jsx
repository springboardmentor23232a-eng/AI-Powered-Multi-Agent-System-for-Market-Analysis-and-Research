import { compact, int } from "../format";

export default function ProfilePanel({ profile }) {
  if (profile.loading || (!profile.data && !profile.error)) return <div className="panel skeleton" style={{ height: 150 }} />;
  if (profile.error) return <div className="notice notice-warn">Company profile unavailable: {profile.error}</div>;

  const p = profile.data.profile;
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Company profile</h2>
          <p className="panel-sub">Reported by the data provider, not verified by us</p>
        </div>
        {p.website && <a href={p.website} target="_blank" rel="noreferrer">{p.website.replace(/^https?:\/\//, "")}</a>}
      </div>
      <div className="profile-meta">
        {p.sector && <span className="badge">{p.sector}</span>}
        {p.industry && <span className="badge">{p.industry}</span>}
        {p.country && <span className="badge">{p.country}</span>}
        {p.employees != null && <span className="badge">{int(p.employees)} employees</span>}
        {p.market_cap != null && <span className="badge">Market cap {compact(p.market_cap, p.currency)}</span>}
      </div>
      <p className="profile-text">{p.business_summary || "No business summary available for this company."}</p>
    </section>
  );
}
