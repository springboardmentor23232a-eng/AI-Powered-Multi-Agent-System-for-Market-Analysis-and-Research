
import { useState } from "react";
import api, { errorMessage } from "../api";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const METRICS = {
  revenue_growth: ["Revenue growth", "%"],
  gross_margin: ["Gross margin", "%"],
  net_margin: ["Net profit margin", "%"],
  ebitda_margin: ["EBITDA margin", "%"],
  debt_equity: ["Debt-to-equity", "x"],
  roe: ["Return on equity", "%"],
  pe_ratio: ["P/E ratio", "x"],
  pb_ratio: ["P/B ratio", "x"],
};

function formatValue(value, unit) {
  return value == null
    ? "N/A"
    : `${Number(value).toFixed(2)}${unit}`;
}

export default function PeerComparison({ ticker }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [metric, setMetric] = useState("net_margin");

  async function loadPeers() {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await api.get(
        `/stocks/${encodeURIComponent(ticker)}/peer-comparison`
      );

      setResult(res.data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const companies =
    result?.status === "ok"
      ? [result.company, ...(result.peers || [])]
      : [];

  const chartData = companies
    .filter((company) => company.metrics?.[metric] != null)
    .map((company) => ({
      ticker: company.ticker,
      value: company.metrics[metric],
    }));

  return (
    <section className="mt-6 space-y-5">

      {/* Heading and button */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h4 className="text-lg font-semibold text-gray-900">
            Industry peer comparison
          </h4>

          <p className="mt-1 text-xs text-gray-500">
            Compare financial performance with similar companies.
          </p>
        </div>

        <button
          onClick={loadPeers}
          disabled={loading}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading
            ? "Comparing..."
            : result
            ? "Refresh comparison"
            : "Compare peers"}
        </button>
      </div>

      {!result && !loading && !error && (
        <p className="text-sm text-gray-500">
          Click Compare peers to discover companies in the
          same industry and compare their financial metrics.
        </p>
      )}

      {/* Loading */}
      {loading && (
        <div className="rounded-lg bg-blue-50 p-4 text-sm text-blue-700">
          Discovering industry peers and retrieving financial
          statements. This may take a little time.
        </div>
      )}

      {/* Request error */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* No suitable peers */}
      {result && result.status !== "ok" && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h5 className="font-semibold text-amber-800">
            Peer comparison unavailable
          </h5>

          <p className="mt-2 text-sm text-amber-700">
            {result.message ||
              "No comparable industry peers were found."}
          </p>
        </div>
      )}

      {result?.status === "ok" && (
        <>
          {/* Industry information */}
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm">
            <p>
              <strong>Sector:</strong> {result.sector || "N/A"}
            </p>

            <p className="mt-1">
              <strong>Industry:</strong> {result.industry || "N/A"}
            </p>

            <p className="mt-1">
              <strong>Comparable peers:</strong> {result.peer_count}
            </p>
          </div>

          {/* Comparison table */}
          <div>
            <h5 className="mb-3 font-semibold text-gray-900">
              Financial metrics comparison
            </h5>

            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <table className="w-full whitespace-nowrap text-left text-sm">

                <thead className="bg-gray-50 text-gray-600">
                  <tr>
                    <th className="p-3">Metric</th>

                    {companies.map((company, index) => (
                      <th
                        key={company.ticker}
                        className={`p-3 ${
                          index === 0 ? "bg-blue-50 text-blue-700" : ""
                        }`}
                      >
                        {company.ticker}

                        {index === 0 && (
                          <span className="block text-xs">
                            Selected company
                          </span>
                        )}
                      </th>
                    ))}

                    <th className="p-3">Peer average</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-gray-200">

                  <tr>
                    <td className="p-3 font-medium">
                      Reporting period
                    </td>

                    {companies.map((company) => (
                      <td key={company.ticker} className="p-3">
                        {company.period || "N/A"}
                      </td>
                    ))}

                    <td className="p-3">—</td>
                  </tr>

                  {Object.entries(METRICS).map(
                    ([key, [label, unit]]) => (
                      <tr key={key}>

                        <td className="p-3 font-medium">
                          {label}
                        </td>

                        {companies.map((company, index) => (
                          <td
                            key={company.ticker}
                            className={`p-3 ${
                              index === 0
                                ? "bg-blue-50 font-semibold"
                                : ""
                            }`}
                          >
                            {formatValue(
                              company.metrics?.[key],
                              unit
                            )}
                          </td>
                        ))}

                        <td className="p-3 font-medium">
                          {formatValue(
                            result.comparison?.[key]?.peer_average,
                            unit
                          )}
                        </td>

                      </tr>
                    )
                  )}
                </tbody>
              </table>
            </div>

            <p className="mt-2 text-xs text-gray-500">
              N/A indicates unavailable or non-comparable data.
              Peer averages exclude the selected company.
            </p>
          </div>

          {/* Interactive comparison chart */}
          <div className="rounded-xl border border-gray-200 p-4">

            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">

              <h5 className="font-semibold text-gray-900">
                Visual comparison
              </h5>

              <select
                value={metric}
                onChange={(e) => setMetric(e.target.value)}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                {Object.entries(METRICS).map(
                  ([key, [label]]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  )
                )}
              </select>

            </div>

            {chartData.length >= 2 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis dataKey="ticker" fontSize={11} />

                    <YAxis
                      fontSize={11}
                      tickFormatter={(value) =>
                        `${value}${METRICS[metric][1]}`
                      }
                    />

                    <Tooltip
                      formatter={(value) => [
                        formatValue(value, METRICS[metric][1]),
                        METRICS[metric][0],
                      ]}
                    />

                    <Bar
                      dataKey="value"
                      fill="#2563eb"
                      radius={[5, 5, 0, 0]}
                    />

                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-sm text-gray-500">
                Insufficient comparable values for this metric.
              </p>
            )}

          </div>

          {/* Comparison explanations */}
          <div>
            <h5 className="mb-3 font-semibold text-gray-900">
              Peer comparison assessment
            </h5>

            <div className="divide-y divide-gray-200 rounded-lg border border-gray-200">

              {Object.entries(result.comparison || {}).map(
                ([key, assessment]) => (
                  <div key={key} className="p-4">

                    <h6 className="text-sm font-semibold">
                      {METRICS[key]?.[0] || key}
                    </h6>

                    <p className="mt-1 text-sm text-gray-600">
                      {assessment.message}
                    </p>

                    <p className="mt-1 text-xs text-gray-500">
                      Comparable peers: {assessment.peer_count}
                    </p>

                  </div>
                )
              )}

            </div>
          </div>
        </>
      )}

      {/* Excluded companies */}
      {result?.excluded?.length > 0 && (
        <details className="rounded-lg border border-gray-200 p-4">
          <summary className="cursor-pointer text-sm font-medium">
            Excluded companies ({result.excluded.length})
          </summary>

          <div className="mt-3 space-y-2">
            {result.excluded.map((company, index) => (
              <p key={index} className="text-sm text-gray-600">
                <strong>{company.ticker}:</strong>{" "}
                {company.reason}
              </p>
            ))}
          </div>
        </details>
      )}

      {/* Source and disclaimer */}
      {result && (
        <div className="rounded-lg bg-gray-50 p-4 text-xs text-gray-500">
          <p>Source: {result.source || "Yahoo Finance"}</p>

          <p className="mt-1">
            Retrieved at:{" "}
            {result.retrieved_at
              ? new Date(result.retrieved_at).toLocaleString()
              : "N/A"}
          </p>

          <p className="mt-2 italic">{result.note}</p>
        </div>
      )}

    </section>
  );
}
