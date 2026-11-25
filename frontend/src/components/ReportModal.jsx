import { useEffect } from "react";
import { useApi } from "../hooks";
import { dateTimeOf } from "../format";
import Icon from "./Icon";

const inline = (s) =>
  s.split(/(_[^_]+_)/g).map((part, i) =>
    part.length > 2 && part.startsWith("_") && part.endsWith("_") ? <em key={i}>{part.slice(1, -1)}</em> : part
  );

function MiniMarkdown({ text }) {
  const blocks = [];
  let list = [];
  const flush = () => {
    if (list.length) {
      blocks.push(<ul key={`u${blocks.length}`}>{list}</ul>);
      list = [];
    }
  };
  text.split("\n").forEach((line, i) => {
    if (line.startsWith("- ")) {
      list.push(<li key={i}>{inline(line.slice(2))}</li>);
      return;
    }
    flush();
    if (line.startsWith("## ")) blocks.push(<h4 key={i}>{line.slice(3)}</h4>);
    else if (line.startsWith("# ")) blocks.push(<h3 key={i}>{line.slice(2)}</h3>);
    else if (line.trim()) blocks.push(<p key={i}>{inline(line)}</p>);
  });
  flush();
  return <div className="report">{blocks}</div>;
}

export default function ReportModal({ taskId, onClose }) {
  const res = useApi(`/research/${taskId}`);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const task = res.data;
  const report = task?.report;

  return (
    <div className="backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label="Research report">
        <div className="modal-head">
          <div>
            <h2 className="panel-title">{task ? `${task.ticker} research report` : "Research report"}</h2>
            {task && (
              <div className="row" style={{ marginTop: 6 }}>
                <span className="badge">{task.market}</span>
                <span className="badge">{task.requested_period}</span>
                <span className="badge">Finished {dateTimeOf(task.completed_at)}</span>
              </div>
            )}
          </div>
          <button className="icon-btn" onClick={onClose} aria-label="Close report"><Icon name="x" size={18} /></button>
        </div>

        {res.loading && <div className="skeleton" style={{ height: 160, borderRadius: 12 }} />}
        {res.error && <div className="notice notice-warn">{res.error}</div>}
        {task && !report && <div className="empty-note">This task has no report yet.</div>}
        {report && (
          <>
            <MiniMarkdown text={report.report_content} />
            <div className="limits">
              <strong><Icon name="alert" size={15} /> Data limitations and disclaimers</strong>
              {report.limitations}
              <br />
              Prices and ratios describe the past and are not financial advice.
            </div>
          </>
        )}

        <div className="modal-foot">
          <span>{task ? `Stored in research_reports for task ${task.task_id}` : ""}</span>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
}
