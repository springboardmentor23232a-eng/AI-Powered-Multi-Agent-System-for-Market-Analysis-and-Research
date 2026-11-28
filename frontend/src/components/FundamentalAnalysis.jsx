import DataQuality from "./DataQuality.jsx";
import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import PeerComparison from "./PeerComparison";
import HistoricalAnalysis from "./HistoricalAnalysis";
const METRICS = {
  rev_growth: ["Revenue growth", "%"],
  gross_margin: ["Gross margin", "%"],
  net_margin: ["Net profit margin", "%"],
  ebitda_margin: ["EBITDA margin", "%"],
  ocf_margin: ["Operating cash flow margin", "%"],
  roa: ["Return on assets", "%"],
  current_ratio: ["Current ratio", ""],
  debt_equity: ["Debt-to-equity", ""],
};
const RATIOS = {
  pe_ratio: [
    "Price-to-Earnings (P/E)",
    "x",
    "Measures share price relative to earnings per share."
  ],
  pb_ratio: [
    "Price-to-Book (P/B)",
    "x",
    "Measures share price relative to book value per share."
  ],
  roe: [
    "Return on Equity (ROE)",
    "%",
    "Measures profitability relative to shareholders' equity."
  ],
};
const EXPLANATIONS = {
  revenue_growth: "Revenue growth",
  earnings: "Earnings",
  profitability: "Profitability",
  cash_flow: "Cash flow",
  liquidity: "Liquidity",
  leverage: "Debt and financial stability",
  overall: "Overall assessment",
};

const CLASS_COLORS = {
  Strong: "text-green-700 bg-green-50",
  Moderate: "text-yellow-700 bg-yellow-50",
  Weak: "text-red-700 bg-red-50",
};


function FinancialRatios({ result }) {
  return (
    <div className="mt-5">
      <h4 className="mb-3 font-semibold text-gray-900">
        Valuation and return ratios
      </h4>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(RATIOS).map(
          ([key, [label, unit, description]]) => {
            const value = result.ratios?.[key];

            return (
              <div
                key={key}
                className="rounded-lg border border-gray-200 bg-gray-50 p-4"
              >
                <p className="text-xs text-gray-500">
                  {label}
                </p>

                <p className="mt-1 text-xl font-semibold text-gray-900">
                  {value == null
                    ? "N/A"
                    : `${Number(value).toFixed(2)}${unit}`}
                </p>

                <p className="mt-2 text-xs text-gray-500">
                  {description}
                </p>

                {value == null && (
                  <p className="mt-2 text-xs text-amber-700">
                    {result.ratio_reasons?.[key] ||
                      "Required financial data is unavailable."}
                  </p>
                )}
              </div>
            );
          }
        )}
      </div>

      <p className="mt-3 text-xs text-gray-500">
        These supplementary ratios are calculated independently
        and are not used as KNN classification inputs.
      </p>
    </div>
  );
}

export default function FundamentalAnalysis({ ticker }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setError("");
    setResult(null);

    api
      .get(`/stocks/${encodeURIComponent(ticker)}/fundamental-analysis`)
      .then((res) => {
        if (!cancelled) setResult(res.data);
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (loading) {
    return (
      <p className="mt-5 text-sm text-gray-500">
        Retrieving financial data and running fundamental analysis...
      </p>
    );
  }

  if (error) {
    return (
      <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
        <h4 className="font-semibold text-red-700">
          Analysis request failed
        </h4>
        <p className="mt-2 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!result) return null;

  
if (result.status === "error") {
  return (
    <div className="mt-5 space-y-5">

      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <h4 className="font-semibold text-red-700">
          Fundamental analysis unavailable
        </h4>

        <p className="mt-2 text-sm text-red-700">
          {result.message}
        </p>

        <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-red-600">
          {result.reasons?.map((reason, index) => (
            <li key={index}>{reason.message}</li>
          ))}
        </ul>

        <p className="mt-4 text-xs text-gray-500">
          Source: {result.source}
        </p>
      </div>

      {result.ratios && (
        <FinancialRatios result={result} />
      )}
      <HistoricalAnalysis historical={result.historical} />
      <PeerComparison key={ticker} ticker={ticker} />
      <DataQuality quality={result.data_quality} />
    </div>
  );
}


  if (result.status !== "ok") {
    return (
      <p className="mt-5 text-sm text-red-600">
        Unexpected response from the analysis service.
      </p>
    );
  }

  return (
    <div className="mt-5 space-y-6">

      {/* Classification */}
      <div className="rounded-xl border border-gray-200 p-5">
        <p className="text-xs uppercase tracking-wide text-gray-500">
          Annual fundamental analysis
        </p>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm text-gray-500">
              Financial health
            </p>

            <span
              className={`mt-1 inline-block rounded-lg px-4 py-2 text-xl font-semibold ${
                CLASS_COLORS[result.classification] ||
                "bg-gray-100 text-gray-700"
              }`}
            >
              {result.classification}
            </span>
          </div>

          <div>
            <p className="text-sm text-gray-500">
              KNN confidence
            </p>

            <p className="text-2xl font-semibold text-gray-900">
              {result.confidence == null
                ? "N/A"
                : `${(result.confidence * 100).toFixed(1)}%`}
            </p>
          </div>
        </div>

        <p className="mt-3 text-xs text-gray-500">
          Confidence represents the weighted neighbour vote,
          not a guarantee of prediction accuracy.
        </p>
      </div>

      {/* Financial metrics */}
      <div>
        <h4 className="mb-3 font-semibold text-gray-900">
          Key financial metrics
        </h4>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {Object.entries(METRICS).map(([key, [label, unit]]) => {
            const value = result.metrics?.[key];

            return (
              <div
                key={key}
                className="rounded-lg border border-gray-200 bg-gray-50 p-4"
              >
                <p className="text-xs text-gray-500">
                  {label}
                </p>

                <p className="mt-1 text-xl font-semibold text-gray-900">
                  {value == null
                    ? "N/A"
                    : `${Number(value).toFixed(2)}${unit}`}
                </p>
              </div>
            );
          })}
        </div>
      </div>
      {/* Valuation and return ratios */}
      <FinancialRatios result={result} />
      {/* Financial explanations */}
      <div>
        <h4 className="mb-3 font-semibold text-gray-900">
          Financial analysis
        </h4>

        <div className="divide-y rounded-lg border border-gray-200">
          {Object.entries(EXPLANATIONS).map(([key, label]) =>
            result.explanation?.[key] ? (
              <div key={key} className="p-4">
                <h5 className="text-sm font-semibold text-gray-900">
                  {label}
                </h5>

                <p className="mt-1 text-sm leading-relaxed text-gray-600">
                  {result.explanation[key]}
                </p>
              </div>
            ) : null
          )}
        </div>
      </div>
      {/* Historical financial performance */}
      <HistoricalAnalysis historical={result.historical} />
      <PeerComparison key={ticker} ticker={ticker} />
      <DataQuality quality={result.data_quality} />
      {/* Classification probabilities */}
      <div>
        <h4 className="mb-3 font-semibold text-gray-900">
          Classification scores
        </h4>

        <div className="space-y-3">
          {Object.entries(result.probabilities || {}).map(
            ([label, probability]) => (
              <div key={label}>
                <div className="mb-1 flex justify-between text-sm">
                  <span>{label}</span>
                  <span>{(probability * 100).toFixed(1)}%</span>
                </div>

                <div className="h-2 rounded-full bg-gray-200">
                  <div
                    className={`h-2 rounded-full ${
                      label === "Strong"
                        ? "bg-green-500"
                        : label === "Moderate"
                        ? "bg-yellow-500"
                        : "bg-red-500"
                    }`}
                    style={{ width: `${probability * 100}%` }}
                  />
                </div>
              </div>
            )
          )}
        </div>
      </div>

      {/* Nearest neighbours */}
      <div>
        <h4 className="mb-2 font-semibold text-gray-900">
          Similar historical companies
        </h4>

        <p className="mb-3 text-xs text-gray-500">
          The nearest company-year records used by the KNN model.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b text-gray-500">
              <tr>
                <th className="py-2">Company</th>
                <th className="py-2">Year</th>
                <th className="py-2">Financial health</th>
              </tr>
            </thead>

            <tbody className="divide-y">
              {result.nearest_matches?.map((match, index) => (
                <tr key={index}>
                  <td className="py-2">{match.Company}</td>
                  <td className="py-2">{match.Year}</td>
                  <td className="py-2">
                    <span
                      className={`rounded px-2 py-1 text-xs ${
                        CLASS_COLORS[match.label] || "bg-gray-100"
                      }`}
                    >
                      {match.label}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model information */}
      <div className="rounded-lg bg-gray-50 p-4 text-xs text-gray-500">
        <h4 className="mb-2 text-sm font-semibold text-gray-700">
          Model information
        </h4>

        <p>Algorithm: {result.model_info?.algorithm}</p>
        <p>Training data: {result.model_info?.trained_on}</p>

        <p>
          Trained at:{" "}
          {result.model_info?.trained_at
            ? new Date(result.model_info.trained_at).toLocaleString()
            : "N/A"}
        </p>

        <p>Source: {result.source}</p>

        <p>
          Retrieved at:{" "}
          {result.retrieved_at
            ? new Date(result.retrieved_at).toLocaleString()
            : "N/A"}
        </p>

        <p className="mt-3 italic">{result.note}</p>
      </div>
    </div>
  );
}
