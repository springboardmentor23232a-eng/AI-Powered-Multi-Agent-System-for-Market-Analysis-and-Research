import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import {
  History,
  FileText,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  RefreshCw,
  TrendingUp,
} from "lucide-react";

export default function ResearchHistorySection({ onViewReport, refreshTrigger }) {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadTasks = async () => {
    try {
      setLoading(true);
      const data = await api.getResearchTasks();
      setTasks(data || []);
      setError("");
    } catch (err) {
      setError(err.message || "Failed to load research tasks");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [refreshTrigger]);

  const getStatusBadge = (status) => {
    switch (status?.toLowerCase()) {
      case "completed":
        return (
          <span className="status-badge status-completed">
            <CheckCircle2 size={12} /> Completed
          </span>
        );
      case "processing":
        return (
          <span className="status-badge status-processing">
            <Loader2 size={12} className="spin" /> Processing
          </span>
        );
      case "failed":
        return (
          <span className="status-badge status-failed">
            <AlertTriangle size={12} /> Failed
          </span>
        );
      default:
        return (
          <span className="status-badge status-pending">
            <Clock size={12} /> Pending
          </span>
        );
    }
  };

  return (
    <div className="card workspace-card">
      <div className="card-header">
        <div className="card-title-group">
          <History className="card-icon" size={20} />
          <div>
            <h2 className="card-title">Research History & Task Outputs</h2>
            <p className="card-subtitle">
              Prior multi-agent market analyses linked strictly to your account
            </p>
          </div>
        </div>
        <button
          className="btn-icon"
          onClick={loadTasks}
          title="Refresh History"
          disabled={loading}
        >
          <RefreshCw size={16} className={loading ? "spin" : ""} />
        </button>
      </div>

      <div className="card-body">
        {error && (
          <div className="alert alert-error my-3">
            <span>{error}</span>
          </div>
        )}

        <div className="table-responsive">
          {loading ? (
            <div className="loading-state">
              <Loader2 size={24} className="spin" />
              <span>Loading research history...</span>
            </div>
          ) : tasks.length === 0 ? (
            <div className="empty-state">
              <FileText size={36} className="empty-icon" />
              <p className="empty-title">No Research Tasks Yet</p>
              <p className="empty-desc">
                Click <b>"Start Research"</b> in the top bar or pick a stock from your watchlist to trigger multi-agent analysis.
              </p>
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Ticker / Company</th>
                  <th>Market</th>
                  <th>Period</th>
                  <th>Date & Time</th>
                  <th>Status</th>
                  <th className="text-right">Report</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((task) => (
                  <tr key={task.task_id}>
                    <td>
                      <div className="cell-stock-flex">
                        <span className="ticker-pill">{task.ticker}</span>
                        <span className="company-text">{task.company_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className="market-tag">{task.market}</span>
                    </td>
                    <td>
                      <span className="period-tag">{task.analysis_period}</span>
                    </td>
                    <td className="text-muted">
                      {new Date(task.created_at).toLocaleString(undefined, {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td>{getStatusBadge(task.status)}</td>
                    <td className="text-right action-cell">
                      <button
                        className="btn btn-xs btn-outline open-report-btn"
                        onClick={() => onViewReport(task)}
                        disabled={task.status !== "Completed" && !task.report_data}
                      >
                        <FileText size={13} /> View Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
