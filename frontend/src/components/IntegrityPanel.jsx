import { dateTimeOf } from "../format";

export default function IntegrityPanel({ history, quote }) {
  const body = (content) => (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Data quality</h2>
          <p className="panel-sub">Checks run on every price download</p>
        </div>
      </div>
      {content}
    </section>
  );

  if (history.loading || (!history.data && !history.error)) return body(<div className="skeleton" style={{ height: 180, borderRadius: 12 }} />);
  if (history.error) return body(<div className="notice notice-warn">No data to check.</div>);

  const { validation: v, meta } = history.data;
  const dup = v.issues.find((i) => i.code === "duplicate_dates")?.count ?? 0;
  const invalid = Math.max(0, v.rows_raw - v.rows_clean - dup);
  const score = v.rows_raw ? (v.rows_clean / v.rows_raw) * 100 : 0;
  const r = 44, c = 2 * Math.PI * r;

  return body(
    <>
      <div className="health">
        <div className="donut">
          <svg width="104" height="104" viewBox="0 0 104 104" role="img" aria-label={`${score.toFixed(0)} percent of rows kept`}>
            <circle cx="52" cy="52" r={r} fill="none" stroke="var(--eq-line)" strokeWidth="8" />
            <circle cx="52" cy="52" r={r} fill="none" stroke="var(--eq-brand)" strokeWidth="8" strokeLinecap="round"
              strokeDasharray={c} strokeDashoffset={c * (1 - score / 100)} />
          </svg>
          <div className="donut-label">{score.toFixed(0)}%</div>
        </div>
        <div className="kv">
          <div><span>Rows downloaded</span><strong>{v.rows_raw}</strong></div>
          <div><span>Duplicates removed</span><strong>{dup}</strong></div>
          <div><span>Invalid rows removed</span><strong>{invalid}</strong></div>
          <div><span>Rows kept</span><strong>{v.rows_clean}</strong></div>
        </div>
      </div>

      {v.issues.length > 0 ? (
        <ul className="issue-list">
          {v.issues.slice(0, 4).map((i) => (
            <li key={i.code}>
              <span className={i.severity === "error" ? "down" : ""} style={i.severity === "warning" ? { color: "var(--eq-warn)" } : null}>●</span>
              <span>{i.message}{i.count ? ` (${i.count})` : ""}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="panel-sub" style={{ marginTop: 14 }}>No data quality issues found.</p>
      )}

      <div className="row" style={{ marginTop: 14 }}>
        {quote?.sector && <span className="badge">{quote.sector}</span>}
        {quote?.currency && <span className="badge">{quote.currency}</span>}
        {quote?.exchange && <span className="badge">{quote.exchange}</span>}
      </div>

      <p className="source-line">
        Source: {meta.provider}. Retrieved {dateTimeOf(meta.retrieved_at)}. Fingerprint {meta.content_hash.slice(0, 10)}.
      </p>
    </>
  );
}
