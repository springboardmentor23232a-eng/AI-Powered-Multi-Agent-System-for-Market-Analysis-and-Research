
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

function formatAmount(value) {
  if (value == null) return "N/A";

  const abs = Math.abs(value);

  if (abs >= 1e12) {
    return `${(value / 1e12).toFixed(2)}T`;
  }

  if (abs >= 1e9) {
    return `${(value / 1e9).toFixed(2)}B`;
  }

  if (abs >= 1e6) {
    return `${(value / 1e6).toFixed(2)}M`;
  }

  return Number(value).toLocaleString();
}

function formatPercent(value) {
  return value == null
    ? "N/A"
    : `${Number(value).toFixed(2)}%`;
}

function ChartPanel({ title, children }) {
  return (
    <div className="rounded-xl border border-gray-200 p-4">
      <h5 className="mb-4 text-sm font-semibold text-gray-800">
        {title}
      </h5>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default function HistoricalAnalysis({ historical }) {
  if (!historical) return null;

  const records = historical.records || [];
  const currency = historical.currency || "Currency unavailable";

  // Exclude completely empty periods from charts
  const usable = records.filter((row) =>
    [
      "revenue",
      "net_income",
      "gross_profit",
      "ebitda",
      "total_debt",
      "equity",
      "operating_cash_flow",
    ].some((key) => row[key] != null)
  );

  const emptyPeriods = records.filter(
    (row) => !usable.includes(row)
  );

  const data = usable.map((row) => ({
    ...row,
    year: row.period,
    revenue_b: row.revenue == null
      ? null : row.revenue / 1e9,
    income_b: row.net_income == null
      ? null : row.net_income / 1e9,
    debt_b: row.total_debt == null
      ? null : row.total_debt / 1e9,
    cash_flow_b: row.operating_cash_flow == null
      ? null : row.operating_cash_flow / 1e9,
  }));

  const trendLabels = {
    revenue: "Revenue trend",
    earnings: "Earnings trend",
    debt: "Debt trend",
    cash_flow: "Cash flow trend",
  };

  return (
    <section className="mt-6 space-y-5">

      <div>
        <h4 className="text-lg font-semibold text-gray-900">
          Historical financial performance
        </h4>

        <p className="mt-1 text-xs text-gray-500">
          Annual financial statements · {currency} ·
          {" "}{usable.length} usable reporting periods
        </p>
      </div>

      {/* Missing reporting periods */}
      {emptyPeriods.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
          Financial figures are unavailable for:
          {" "}
          {emptyPeriods.map((row) => row.period).join(", ")}.
          These periods are excluded from the charts.
        </div>
      )}

      {usable.length === 0 ? (
        <p className="text-sm text-gray-500">
          No usable historical financial data is available.
        </p>
      ) : (
        <>
          {usable.length < 2 && (
            <p className="text-sm text-amber-700">
              At least two reporting periods are required
              for a meaningful historical comparison.
            </p>
          )}

          {/* Revenue and earnings */}
          <ChartPanel
            title={`Revenue and earnings (${currency} billions)`}
          >
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" fontSize={10} />
              <YAxis fontSize={11} />
              <Tooltip
                formatter={(value) =>
                  `${Number(value).toFixed(2)} B ${currency}`
                }
              />
              <Legend />

              <Line
                type="linear"
                dataKey="revenue_b"
                name="Revenue"
                stroke="#2563eb"
                strokeWidth={2}
                connectNulls={false}
              />

              <Line
                type="linear"
                dataKey="income_b"
                name="Net income"
                stroke="#16a34a"
                strokeWidth={2}
                connectNulls={false}
              />
            </LineChart>
          </ChartPanel>

          {/* Growth comparison */}
          <ChartPanel title="Year-over-year growth (%)">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" fontSize={10} />
              <YAxis fontSize={11} />
              <Tooltip
                formatter={(value) =>
                  `${Number(value).toFixed(2)}%`
                }
              />
              <Legend />

              <Bar
                dataKey="revenue_growth"
                name="Revenue growth"
                fill="#2563eb"
              />

              <Bar
                dataKey="earnings_growth"
                name="Earnings growth"
                fill="#16a34a"
              />
            </BarChart>
          </ChartPanel>

          {/* Profitability */}
          <ChartPanel title="Historical profitability (%)">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" fontSize={10} />
              <YAxis fontSize={11} />
              <Tooltip
                formatter={(value) =>
                  `${Number(value).toFixed(2)}%`
                }
              />
              <Legend />

              <Line
                dataKey="gross_margin"
                name="Gross margin"
                stroke="#2563eb"
                strokeWidth={2}
              />

              <Line
                dataKey="net_margin"
                name="Net margin"
                stroke="#16a34a"
                strokeWidth={2}
              />

              <Line
                dataKey="ebitda_margin"
                name="EBITDA margin"
                stroke="#9333ea"
                strokeWidth={2}
              />
            </LineChart>
          </ChartPanel>

          {/* Debt and cash flow */}
          <ChartPanel
            title={`Debt and cash flow (${currency} billions)`}
          >
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" fontSize={10} />
              <YAxis fontSize={11} />
              <Tooltip
                formatter={(value) =>
                  `${Number(value).toFixed(2)} B ${currency}`
                }
              />
              <Legend />

              <Bar
                dataKey="debt_b"
                name="Total debt"
                fill="#ef4444"
              />

              <Bar
                dataKey="cash_flow_b"
                name="Operating cash flow"
                fill="#16a34a"
              />
            </BarChart>
          </ChartPanel>

          {/* Historical comparison table */}
          <div>
            <h5 className="mb-3 font-semibold text-gray-900">
              Year-wise financial comparison
            </h5>

            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full whitespace-nowrap text-left text-sm">
                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    {[
                      "Period",
                      "Revenue",
                      "Net income",
                      "Gross profit",
                      "EBITDA",
                      "Total debt",
                      "Cash flow",
                      "Net margin",
                      "Revenue growth",
                      "Earnings growth",
                      "Debt-to-equity",
                      "ROE",
                    ].map((heading) => (
                      <th key={heading} className="p-3">
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody className="divide-y divide-gray-200">
                  {records.map((row) => (
                    <tr key={row.period}>
                      <td className="p-3">{row.period}</td>
                      <td className="p-3">
                        {formatAmount(row.revenue)}
                      </td>
                      <td className="p-3">
                        {formatAmount(row.net_income)}
                      </td>
                      <td className="p-3">
                        {formatAmount(row.gross_profit)}
                      </td>
                      <td className="p-3">
                        {formatAmount(row.ebitda)}
                      </td>
                      <td className="p-3">
                        {formatAmount(row.total_debt)}
                      </td>
                      <td className="p-3">
                        {formatAmount(row.operating_cash_flow)}
                      </td>
                      <td className="p-3">
                        {formatPercent(row.net_margin)}
                      </td>
                      <td className="p-3">
                        {formatPercent(row.revenue_growth)}
                      </td>
                      <td className="p-3">
                        {formatPercent(row.earnings_growth)}
                      </td>
                      <td className="p-3">
                        {row.debt_equity ?? "N/A"}
                      </td>
                      <td className="p-3">
                        {formatPercent(row.roe)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mt-2 text-xs text-gray-500">
              Currency: {currency}. T = trillion,
              B = billion, M = million.
              N/A indicates unavailable or non-calculable data.
            </p>
          </div>

          {/* Historical explanations */}
          <div>
            <h5 className="mb-3 font-semibold text-gray-900">
              Historical assessment
            </h5>

            <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">
              {Object.entries(historical.trends || {}).map(
                ([key, message]) => (
                  <div key={key} className="p-4">
                    <h6 className="text-sm font-semibold">
                      {trendLabels[key] || key}
                    </h6>

                    <p className="mt-1 text-sm text-gray-600">
                      {message}
                    </p>
                  </div>
                )
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
