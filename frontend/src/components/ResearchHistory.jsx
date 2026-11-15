import { useEffect, useState } from "react";
import API from "../services/api";
import jsPDF from "jspdf";

function ResearchHistory() {
  const [researchTasks, setResearchTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedReport, setSelectedReport] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  function extractReportMetrics(reportContent) {
    const getValue = (label) => {
      const line = reportContent
        .split("\n")
        .find((item) => item.trim().startsWith(label));

      if (!line) return "N/A";

      return line.split(":").slice(1).join(":").trim() || "N/A";
    };

    return {
      currentPrice: getValue("Current Price"),
      periodReturn: getValue("Period Return"),
      averagePrice: getValue("Average Closing Price"),
      highestPrice: getValue("Highest Closing Price"),
      lowestPrice: getValue("Lowest Closing Price"),
      sma20: getValue("SMA 20 (Short-term)"),
      sma50: getValue("SMA 50 (Medium-term)"),
      trend: getValue("Trend Classification"),
      volatility: getValue("Daily Return Volatility"),
      risk: getValue("Risk Classification"),
      signal: getValue("Analytical Signal"),
    };
  }
  useEffect(() => {
    async function fetchResearchHistory() {
      try {
        const response = await API.get("/research/tasks");
        setResearchTasks(response.data);
        setError("");
      } catch (err) {
        console.error("Failed to fetch research history:", err);
        setError("Unable to load research history.");
      } finally {
        setLoading(false);
      }
    }

    fetchResearchHistory();

    window.addEventListener("researchHistoryUpdated", fetchResearchHistory);

    return () => {
      window.removeEventListener(
        "researchHistoryUpdated",
        fetchResearchHistory,
      );
    };
  }, []);
  const selectedMetrics = selectedReport
    ? extractReportMetrics(selectedReport.report_content)
    : null;

  const downloadResearchReport = (task) => {
    const doc = new jsPDF();

    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 20;
    const contentWidth = pageWidth - margin * 2;

    // Report heading
    doc.setFontSize(20);
    doc.setFont("helvetica", "bold");
    doc.text("AI STOCK RESEARCH REPORT", margin, 25);

    // Company details
    doc.setFontSize(14);
    doc.text(task.company_name, margin, 40);

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");

    doc.text(`Ticker: ${task.ticker}`, margin, 50);
    doc.text(`Market: ${task.market}`, margin, 57);
    doc.text(`Analysis Period: ${task.analysis_period}`, margin, 64);
    doc.text(
      `Generated: ${new Date(task.research_date).toLocaleDateString()}`,
      margin,
      71,
    );

    // Separator
    doc.setDrawColor(200, 200, 200);
    doc.line(margin, 78, pageWidth - margin, 78);

    // Research report content
    doc.setFontSize(10);

    const reportLines = doc.splitTextToSize(task.report_content, contentWidth);

    let yPosition = 90;

    reportLines.forEach((line) => {
      if (yPosition > 275) {
        doc.addPage();
        yPosition = 20;
      }

      doc.text(line, margin, yPosition);
      yPosition += 6;
    });

    // Save PDF
    const filename = `${task.ticker}_Research_Report.pdf`;

    doc.save(filename);
  };
  const deleteResearchReport = async (researchId) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this research report?",
    );

    if (!confirmed) return;

    try {
      setDeletingId(researchId);

      await API.delete(`/research/tasks/${researchId}`);

      setResearchTasks((previousTasks) =>
        previousTasks.filter((task) => task.research_id !== researchId),
      );

      if (selectedReport?.research_id === researchId) {
        setSelectedReport(null);
      }
    } catch (error) {
      console.error("Failed to delete research report:", error);
      alert("Unable to delete research report. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };
  const deleteAllResearchHistory = async () => {
    if (researchTasks.length === 0) return;

    const confirmed = window.confirm(
      "Are you sure you want to permanently delete ALL your research history? This action cannot be undone.",
    );

    if (!confirmed) return;

    try {
      setDeletingId("all");

      await API.delete("/research/tasks");

      setResearchTasks([]);
      setSelectedReport(null);

      alert("All research history deleted successfully.");
    } catch (error) {
      console.error("Failed to delete all research history:", error);
      alert("Unable to delete research history. Please try again.");
    } finally {
      setDeletingId(null);
    }
  };
  if (loading) {
    return <p>Loading research history...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <div className="research-history">
      <div className="research-history-header">
        <div>
          <h2>Research History</h2>
          <p>View your previously created stock research tasks.</p>
        </div>

        {researchTasks.length > 0 && (
          <button
            className="delete-all-history-button"
            onClick={deleteAllResearchHistory}
            disabled={deletingId === "all"}
          >
            {deletingId === "all" ? "Deleting..." : "Delete All History"}
          </button>
        )}
      </div>

      {researchTasks.length === 0 ? (
        <p>No research history available yet.</p>
      ) : (
        <div className="research-table-container">
          <table className="research-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Ticker</th>
                <th>Market</th>
                <th>Period</th>
                <th>Date</th>
                <th>Status</th>
                <th>Report</th>
              </tr>
            </thead>

            <tbody>
              {researchTasks.map((task) => (
                <tr key={task.research_id}>
                  <td>{task.company_name}</td>
                  <td>{task.ticker}</td>
                  <td>{task.market}</td>
                  <td>{task.analysis_period}</td>
                  <td>{new Date(task.research_date).toLocaleDateString()}</td>
                  <td>
                    <span
                      className={`research-status ${task.status.toLowerCase()}`}
                    >
                      {task.status}
                    </span>
                  </td>
                  <td>
                    <div className="research-action-buttons">
                      {task.status === "Completed" && task.report_content && (
                        <>
                          <button
                            className="view-report-button"
                            onClick={() => setSelectedReport(task)}
                          >
                            View Report
                          </button>

                          <button
                            className="download-report-button"
                            onClick={() => downloadResearchReport(task)}
                          >
                            Download PDF
                          </button>
                        </>
                      )}

                      <button
                        className="delete-report-button"
                        onClick={() => deleteResearchReport(task.research_id)}
                        disabled={deletingId === task.research_id}
                      >
                        {deletingId === task.research_id
                          ? "Deleting..."
                          : "Delete"}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {selectedReport && (
        <div
          className="report-modal-overlay"
          onClick={() => setSelectedReport(null)}
        >
          <div className="report-modal" onClick={(e) => e.stopPropagation()}>
            <button
              className="close-report-button"
              onClick={() => setSelectedReport(null)}
            >
              ×
            </button>

            <div className="report-header">
              <span className="report-label">AI STOCK RESEARCH</span>

              <h2>{selectedReport.company_name}</h2>

              <p>
                {selectedReport.ticker} | {selectedReport.market}
              </p>

              <div className="report-meta">
                <span>Analysis Period: {selectedReport.analysis_period}</span>

                <span>
                  Generated:{" "}
                  {new Date(selectedReport.research_date).toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="report-metrics-grid">
              <div className="report-metric-card">
                <span>Current Price</span>
                <strong>{selectedMetrics.currentPrice}</strong>
              </div>
              <div className="report-metric-card">
                <span>SMA 20 (Short-term)</span>
                <strong>{selectedMetrics.sma20}</strong>
              </div>

              <div className="report-metric-card">
                <span>SMA 50 (Medium-term)</span>
                <strong>{selectedMetrics.sma50}</strong>
              </div>
              <div className="report-metric-card">
                <span>Period Return</span>
                <strong
                  className={
                    Number.parseFloat(selectedMetrics.periodReturn) >= 0
                      ? "metric-positive"
                      : "metric-negative"
                  }
                >
                  {selectedMetrics.periodReturn}
                </strong>
              </div>

              <div className="report-metric-card">
                <span>Average Price</span>
                <strong>{selectedMetrics.averagePrice}</strong>
              </div>

              <div className="report-metric-card">
                <span>Highest Price</span>
                <strong>{selectedMetrics.highestPrice}</strong>
              </div>

              <div className="report-metric-card">
                <span>Lowest Price</span>
                <strong>{selectedMetrics.lowestPrice}</strong>
              </div>

              <div className="report-metric-card">
                <span>Volatility</span>
                <strong>{selectedMetrics.volatility}</strong>
              </div>

              <div className="report-metric-card">
                <span>Trend</span>
                <strong
                  className={`metric-trend ${selectedMetrics.trend.toLowerCase()}`}
                >
                  {selectedMetrics.trend}
                </strong>
              </div>

              <div className="report-metric-card">
                <span>Risk Level</span>
                <strong
                  className={`metric-risk ${selectedMetrics.risk.toLowerCase()}`}
                >
                  {selectedMetrics.risk}
                </strong>
              </div>
            </div>

            <div className="report-signal-section">
              <span>Analytical Signal</span>

              <strong
                className={`report-signal-badge ${selectedMetrics.signal.toLowerCase().replace(/\s+/g, "-")}`}
              >
                {selectedMetrics.signal}
              </strong>
            </div>

            <div className="report-content">
              <pre>{selectedReport.report_content}</pre>
            </div>

            <div className="report-footer">
              <p>
                Generated using historical stock data and rule-based financial
                analysis.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ResearchHistory;
