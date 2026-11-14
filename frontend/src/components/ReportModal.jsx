import React from "react";
import {
  X,
  TrendingUp,
  BarChart3,
  Activity,
  Layers,
  ShieldAlert,
  Sparkles,
  Download,
  Calendar,
  Globe,
  Clock,
} from "lucide-react";

export default function ReportModal({ isOpen, onClose, task }) {
  if (!isOpen || !task) return null;

  const report = task.report_data || {};
  const metadata = report.metadata || {
    ticker: task.ticker,
    company_name: task.company_name,
    market: task.market,
    analysis_period: task.analysis_period,
    currency: "$",
    current_price: 150.0,
    target_price: 185.0,
    expected_upside: "+23.3%",
    consensus_rating: "BUY",
  };

  const agents = report.agents || {};
  const fundamental = agents.fundamental_agent;
  const technical = agents.technical_agent;
  const sentiment = agents.sentiment_agent;
  const synthesis = report.synthesis;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-dialog report-dialog">
        <div className="modal-header report-header">
          <div>
            <div className="report-badges-row">
              <span className="ticker-pill large">{metadata.ticker}</span>
              <span className="market-tag">{metadata.market}</span>
              <span className="period-tag">{metadata.analysis_period}</span>
              <span className="rating-badge rating-bullish">
                {metadata.consensus_rating}
              </span>
            </div>
            <h2 className="report-company-title">{metadata.company_name}</h2>
            <div className="report-meta-text">
              <Calendar size={13} className="inline-icon" /> Generated:{" "}
              {metadata.generated_at || new Date(task.created_at).toLocaleString()}
            </div>
          </div>
          <div className="report-header-actions">
            <button className="btn btn-secondary btn-sm" onClick={handlePrint} title="Print or Save PDF">
              <Download size={14} /> Export / Print
            </button>
            <button className="modal-close-btn" onClick={onClose}>
              <X size={18} />
            </button>
          </div>
        </div>

        <div className="modal-body report-body">
          {/* Target Price & Valuation Header Cards */}
          <div className="price-overview-grid">
            <div className="metric-box">
              <span className="metric-box-label">Current Market Price</span>
              <span className="metric-box-val">
                {metadata.currency}{metadata.current_price}
              </span>
            </div>
            <div className="metric-box highlight">
              <span className="metric-box-label">Consensus Target Price</span>
              <span className="metric-box-val text-accent">
                {metadata.currency}{metadata.target_price}
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Projected Upside</span>
              <span className="metric-box-val text-success">
                {metadata.expected_upside}
              </span>
            </div>
            <div className="metric-box">
              <span className="metric-box-label">Synthesis Rating</span>
              <span className="metric-box-val text-bold">
                {metadata.consensus_rating}
              </span>
            </div>
          </div>

          {/* Executive Summary */}
          <div className="report-card">
            <div className="report-card-title">
              <Sparkles size={16} className="text-accent" />
              <h4>Executive Summary & Autonomous Agent Thesis</h4>
            </div>
            <p className="report-summary-p">
              {report.executive_summary || task.report_summary}
            </p>
          </div>

          {/* Multi-Agent Deep Dive Grid */}
          <div className="agents-grid">
            {/* Fundamental Valuation Agent */}
            {fundamental && (
              <div className="agent-card">
                <div className="agent-card-header">
                  <BarChart3 size={16} className="agent-icon" />
                  <div>
                    <h5>{fundamental.agent_name}</h5>
                    <span className="agent-verdict">{fundamental.verdict}</span>
                  </div>
                </div>
                <div className="agent-metrics-list">
                  {Object.entries(fundamental.metrics || {}).map(([key, val]) => (
                    <div key={key} className="agent-metric-row">
                      <span className="metric-k">{key}</span>
                      <span className="metric-v">{val}</span>
                    </div>
                  ))}
                </div>
                <div className="agent-highlights">
                  <h6>Agent Highlights:</h6>
                  <ul>
                    {(fundamental.highlights || []).map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Technical Momentum Agent */}
            {technical && (
              <div className="agent-card">
                <div className="agent-card-header">
                  <Activity size={16} className="agent-icon" />
                  <div>
                    <h5>{technical.agent_name}</h5>
                    <span className="agent-verdict">{technical.trend}</span>
                  </div>
                </div>
                <div className="agent-metrics-list">
                  {Object.entries(technical.indicators || {}).map(([key, val]) => (
                    <div key={key} className="agent-metric-row">
                      <span className="metric-k">{key}</span>
                      <span className="metric-v">{val}</span>
                    </div>
                  ))}
                </div>
                <div className="agent-highlights">
                  <h6>Technical Signals:</h6>
                  <ul>
                    {(technical.highlights || []).map((h, i) => (
                      <li key={i}>{h}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Market Sentiment & Macro Agent */}
            {sentiment && (
              <div className="agent-card full-width">
                <div className="agent-card-header">
                  <Layers size={16} className="agent-icon" />
                  <div>
                    <h5>{sentiment.agent_name}</h5>
                    <span className="agent-verdict">Sentiment Score: {sentiment.sentiment_score}</span>
                  </div>
                </div>
                <p className="macro-p">{sentiment.macro_context}</p>
                <div className="sentiment-columns">
                  <div className="sent-col">
                    <h6 className="text-success">Institutional Catalysts:</h6>
                    <ul>
                      {(sentiment.catalysts || []).map((c, i) => (
                        <li key={i}>{c}</li>
                      ))}
                    </ul>
                  </div>
                  <div className="sent-col">
                    <h6 className="text-danger">
                      <ShieldAlert size={14} className="inline-icon" /> Downside Risks:
                    </h6>
                    <ul>
                      {(sentiment.risk_factors || []).map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Synthesis & Final Takeaway */}
          {synthesis && (
            <div className="synthesis-card">
              <h5>Final Multi-Agent Recommendation</h5>
              <p>{synthesis.key_takeaway}</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
}
