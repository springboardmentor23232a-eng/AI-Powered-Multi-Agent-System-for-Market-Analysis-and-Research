import { useState } from "react";
import API from "../services/api";

function FinancialStatements() {
  const [symbol, setSymbol] = useState("RELIANCE");
  const [exchange, setExchange] = useState("NSI");
  const [frequency, setFrequency] = useState("annual");
  const [statementType, setStatementType] = useState("income_statement");

  const [financialStatements, setFinancialStatements] = useState(null);
  const [searchedTicker, setSearchedTicker] = useState("");
  const [retrievedAt, setRetrievedAt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchFinancialStatements = async (e) => {
    e.preventDefault();

    if (!symbol.trim()) {
      setError("Please enter a company ticker.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setFinancialStatements(null);

      const ticker = symbol.trim().toUpperCase();

      const response = await API.get(`/market-data/${ticker}/financials`, {
        params: {
          exchange,
          frequency,
        },
      });

      setFinancialStatements(response.data.financial_statements);
      setSearchedTicker(response.data.ticker);
      setRetrievedAt(response.data.retrieved_at);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Unable to fetch financial statements.",
      );
    } finally {
      setLoading(false);
    }
  };

  const statementLabels = {
    income_statement: "Income Statement",
    balance_sheet: "Balance Sheet",
    cash_flow_statement: "Cash Flow Statement",
  };

  const records = financialStatements?.[statementType] || [];

  const lineItems = [
    ...new Set(
      records.flatMap((record) => Object.keys(record.line_items || {})),
    ),
  ];

  const formatValue = (value) => {
    if (value === null || value === undefined || value === "") {
      return "—";
    }

    if (typeof value === "number") {
      return value.toLocaleString("en-IN", {
        maximumFractionDigits: 2,
      });
    }

    return value;
  };

  return (
    <div className="financial-statements-container">
      <h2>Financial Statements</h2>

      <p>
        View company income statements, balance sheets, and cash flow
        statements.
      </p>

      <form
        onSubmit={fetchFinancialStatements}
        className="financial-statements-form"
      >
        <input
          type="text"
          placeholder="Enter ticker (e.g. RELIANCE)"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value)}
        />

        <select value={exchange} onChange={(e) => setExchange(e.target.value)}>
          <option value="NSI">NSE</option>
          <option value="BSE">BSE</option>
          <option value="NASDAQ">NASDAQ</option>
          <option value="NYSE">NYSE</option>
        </select>

        <select
          value={frequency}
          onChange={(e) => setFrequency(e.target.value)}
        >
          <option value="annual">Annual</option>
          <option value="quarterly">Quarterly</option>
        </select>

        <button type="submit" disabled={loading}>
          {loading ? "Loading..." : "Get Financials"}
        </button>
      </form>

      {error && <p className="financial-statements-error">{error}</p>}

      {financialStatements && (
        <div className="financial-statements-results">
          <h3>{searchedTicker}</h3>

          <div className="financial-statement-tabs">
            {Object.entries(statementLabels).map(([key, label]) => (
              <button
                key={key}
                type="button"
                className={statementType === key ? "active" : ""}
                onClick={() => setStatementType(key)}
              >
                {label}
              </button>
            ))}
          </div>

          <h4>{statementLabels[statementType]}</h4>

          {records.length > 0 ? (
            <div className="financial-statements-table-wrapper">
              <table className="financial-statements-table">
                <thead>
                  <tr>
                    <th>Financial Item</th>
                    {records.map((record) => (
                      <th key={record.period}>{record.period}</th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {lineItems.map((item) => (
                    <tr key={item}>
                      <td>{item}</td>

                      {records.map((record) => (
                        <td key={record.period}>
                          {formatValue(record.line_items?.[item])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>No data available for this statement.</p>
          )}

          <p className="financial-statements-meta">Frequency: {frequency}</p>

          <p className="financial-statements-meta">
            Data source: Yahoo Finance (via yfinance)
          </p>

          <p className="financial-statements-meta">
            Retrieved at: {retrievedAt}
          </p>
        </div>
      )}
    </div>
  );
}

export default FinancialStatements;
