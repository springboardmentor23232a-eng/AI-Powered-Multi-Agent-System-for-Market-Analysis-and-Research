import { dateOf } from "../format";
import Icon from "./Icon";

const LABEL = { pending: "Queued", processing: "Running", completed: "Done", failed: "Failed" };

function StatusIcon({ status }) {
  const name = status === "completed" ? "check" : status === "failed" ? "alert" : "loader";
  return (
    <span className={`status status-${status}`} title={LABEL[status] || status}>
      <Icon name={name} size={15} className={status === "pending" || status === "processing" ? "spin" : ""} />
    </span>
  );
}

export default function ResearchTasks({ tasks, limit, onViewAll, onOpen, onView, onRefresh }) {
  const shown = limit ? tasks.slice(0, limit) : tasks;
  return (
    <section className="panel" id="history">
      <div className="panel-head">
        <div>
          <h2 className="panel-title">Research history</h2>
          <p className="panel-sub">{tasks.length} saved for your account</p>
        </div>
        <div className="row">
          {onViewAll && tasks.length > shown.length && (
            <button className="btn btn-ghost btn-sm" onClick={onViewAll}>View all</button>
          )}
          <button className="btn btn-ghost btn-sm" onClick={onRefresh}>
            <Icon name="refresh" size={14} /> Refresh
          </button>
        </div>
      </div>

      {tasks.length === 0 ? (
        <div className="empty-note">No research yet. Search for a stock and choose Research.</div>
      ) : (
        <div className="list">
          {shown.map((t) => (
            <div key={t.task_id} className="task">
              <StatusIcon status={t.status} />
              <div className="task-main">
                <div className="task-title">
                  <button className="link-btn" onClick={() => onView({ ticker: t.ticker, market: t.market })}>{t.ticker}</button>
                  <span className="badge">{t.market}</span>
                  <span className="badge">{t.requested_period}</span>
                </div>
                <div className="task-sub">
                  {t.company_name || "Company name not saved"}. {LABEL[t.status] || t.status} on {dateOf(t.created_at)}
                </div>
              </div>
              {t.status === "completed" && (
                <button className="btn btn-primary btn-sm" onClick={() => onOpen(t.task_id)}>
                  <Icon name="file" size={14} /> Report
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
