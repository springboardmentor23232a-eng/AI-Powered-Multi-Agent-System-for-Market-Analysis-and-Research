
const STATUS = {
  complete: {
    label: "No issues detected",
    style: "bg-green-50 text-green-700",
  },
  partial: {
    label: "Partial data",
    style: "bg-amber-50 text-amber-700",
  },
  inconsistent: {
    label: "Inconsistent data",
    style: "bg-red-50 text-red-700",
  },
};

const CATEGORIES = {
  missing_data: "Missing information",
  inconsistent_data: "Inconsistent information",
  invalid_value: "Invalid numerical value",
  insufficient_data: "Insufficient historical data",
  ratio_unavailable: "Unavailable financial ratio",
};

export default function DataQuality({ quality }) {
  if (!quality) return null;

  const status = STATUS[quality.status] || {
    label: "Unknown",
    style: "bg-gray-100 text-gray-700",
  };

  const coverage = quality.total_periods > 0
    ? (quality.usable_periods / quality.total_periods) * 100
    : 0;

  return (
    <section className="mt-6 space-y-5">

      {/* Heading */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h4 className="text-lg font-semibold text-gray-900">
          Financial data quality
        </h4>

        <span
          className={`rounded-lg px-3 py-1 text-sm font-medium ${status.style}`}
        >
          {status.label}
        </span>
      </div>

      <p className="text-sm text-gray-500">
        Assessment of financial data availability,
        completeness and internal consistency.
      </p>

      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">

        {[
          ["Total periods", quality.total_periods],
          ["Usable periods", quality.usable_periods],
          ["Errors", quality.error_count],
          ["Warnings", quality.warning_count],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-lg border border-gray-200 bg-gray-50 p-4"
          >
            <p className="text-xs text-gray-500">
              {label}
            </p>

            <p className="mt-1 text-xl font-semibold text-gray-900">
              {value}
            </p>
          </div>
        ))}

      </div>

      {/* Historical coverage */}
      <div className="rounded-lg border border-gray-200 p-4">

        <div className="mb-2 flex justify-between text-sm">
          <span>Historical period coverage</span>

          <span className="font-semibold">
            {quality.total_periods > 0
              ? `${coverage.toFixed(1)}%`
              : "N/A"}
          </span>
        </div>

        <div className="h-2 overflow-hidden rounded-full bg-gray-200">
          <div
            className="h-full rounded-full bg-green-500"
            style={{ width: `${coverage}%` }}
          />
        </div>

        <p className="mt-2 text-xs text-gray-500">
          Percentage of reported periods containing usable
          financial information. This does not measure
          the completeness of every financial field.
        </p>

      </div>

      {/* Checks performed */}
      <div>
        <h5 className="mb-3 font-semibold text-gray-900">
          Validation checks performed
        </h5>

        <div className="space-y-2 rounded-lg border border-gray-200 p-4">

          {(quality.checks_performed || []).map((check) => (
            <div
              key={check}
              className="flex items-center gap-2 text-sm text-gray-700"
            >
              <span className="text-blue-600">✓</span>
              {check}
            </div>
          ))}

        </div>

        <p className="mt-2 text-xs text-gray-500">
          A check mark indicates that the validation was
          performed, not necessarily that it passed.
        </p>
      </div>

      {/* Detected issues */}
      <div>
        <h5 className="mb-3 font-semibold text-gray-900">
          Detected issues
        </h5>

        {quality.issues?.length > 0 ? (
          <div className="space-y-3">

            {quality.issues.map((issue, index) => (
              <div
                key={index}
                className={`rounded-lg border p-4 ${
                  issue.severity === "error"
                    ? "border-red-200 bg-red-50 text-red-700"
                    : "border-amber-200 bg-amber-50 text-amber-800"
                }`}
              >

                <div className="flex flex-wrap items-center justify-between gap-2">

                  <h6 className="text-sm font-semibold">
                    {CATEGORIES[issue.category] ||
                      issue.category}
                  </h6>

                  <span className="text-xs font-medium uppercase">
                    {issue.severity}
                  </span>

                </div>

                <p className="mt-2 text-xs">
                  Field / Period: {issue.field}
                </p>

                <p className="mt-2 break-words text-sm">
                  {issue.message}
                </p>

              </div>
            ))}

          </div>
        ) : (
          <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-700">
            No missing or inconsistent information was
            detected by the implemented validation checks.
          </div>
        )}

      </div>

      {/* Disclaimer */}
      <div className="rounded-lg bg-gray-50 p-4 text-xs text-gray-500">
        <p>{quality.note}</p>

        <p className="mt-2">
          Data quality assessment is independent of the
          KNN financial health classification.
        </p>
      </div>

    </section>
  );
}
