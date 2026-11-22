import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

const TABS = [
  { key: "profile", label: "Profile" },
  { key: "income_statement", label: "Income statement" },
  { key: "balance_sheet", label: "Balance sheet" },
  { key: "cash_flow", label: "Cash flow" },
];

// Lines shown first in each statement ("Show all" reveals the rest)
const KEY_ITEMS = {
  income_statement: ["Total Revenue", "Gross Profit", "Operating Income", "EBITDA", "Net Income", "Basic EPS", "Diluted EPS"],
  balance_sheet: ["Total Assets", "Total Liabilities Net Minority Interest", "Stockholders Equity", "Cash And Cash Equivalents", "Total Debt"],
  cash_flow: ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "Free Cash Flow", "Capital Expenditure"],
};

const STATEMENT_LABEL = {
  income_statement: "income statement",
  balance_sheet: "balance sheet",
  cash_flow: "cash flow statement",
};

const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 2 });

function Field({ label, children }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-gray-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-gray-900">{children || "-"}</dd>
    </div>
  );
}

export default function CompanyDetails({ ticker, onClose }) {
  const [tab, setTab] = useState("profile");
  const [frequency, setFrequency] = useState("annual");
  const [showAll, setShowAll] = useState(false);
  const [profile, setProfile] = useState(null);
  const [profileError, setProfileError] = useState("");
  const [fin, setFin] = useState(null);
  const [finError, setFinError] = useState("");
  const [finLoading, setFinLoading] = useState(false);

  // Profile loads when the panel opens
  useEffect(() => {
    let cancelled = false;
    api
      .get(`/stocks/${ticker}/profile`)
      .then((res) => !cancelled && setProfile(res.data))
      .catch((err) => !cancelled && setProfileError(errorMessage(err)));
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  // Financial statements load when a statement tab is opened (or Annual/Quarterly changes)
  const needFin = tab !== "profile";
  useEffect(() => {
    if (!needFin) return;
    let cancelled = false;
    setFinLoading(true);
    setFinError("");
    setFin(null);
    api
      .get(`/stocks/${ticker}/financials`, { params: { frequency } })
      .then((res) => !cancelled && setFin(res.data))
      .catch((err) => !cancelled && setFinError(errorMessage(err)))
      .finally(() => !cancelled && setFinLoading(false));
    return () => {
      cancelled = true;
    };
  }, [needFin, frequency, ticker]);

  const statement = fin ? fin[tab] : null;
  const keyRows = statement?.available
    ? statement.rows.filter((r) => KEY_ITEMS[tab].includes(r.item))
    : [];
  const canToggle = keyRows.length > 0 && keyRows.length < (statement?.rows.length ?? 0);
  const rows = !statement?.available ? [] : canToggle && !showAll ? keyRows : statement.rows;

  const tabClass = (k) =>
    `rounded-lg border px-3 py-1 text-sm ${
      tab === k ? "border-blue-600 bg-blue-600 text-white" : "border-gray-300 hover:bg-gray-50"
    }`;

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <div className="flex items-start justify-between gap-4">
        <h3 className="font-semibold text-gray-900">
          {profile ? `${profile.name} (${profile.ticker})` : ticker} · company details
        </h3>
        <button onClick={onClose} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50">
          Close
        </button>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)} className={tabClass(t.key)}>
            {t.label}
          </button>
        ))}
        {tab !== "profile" && (
          <div className="ml-auto flex gap-2">
            {["annual", "quarterly"].map((f) => (
              <button
                key={f}
                onClick={() => setFrequency(f)}
                className={`rounded-lg border px-3 py-1 text-sm capitalize ${
                  frequency === f ? "border-gray-800 bg-gray-800 text-white" : "border-gray-300 hover:bg-gray-50"
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* ---------- Profile tab ---------- */}
      {tab === "profile" && (
        <div className="mt-5">
          {profileError && <p className="text-sm text-red-600">{profileError}</p>}
          {!profile && !profileError && <p className="text-sm text-gray-500">Loading profile from Yahoo Finance...</p>}
          {profile && (
            <>
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <Field label="Market">{profile.market}</Field>
                <Field label="Sector">{profile.sector}</Field>
                <Field label="Industry">{profile.industry}</Field>
                <Field label="Country">{profile.country}</Field>
                <Field label="Employees">{profile.employees ? profile.employees.toLocaleString() : null}</Field>
                <Field label="Market capitalisation">
                  {profile.market_cap ? `${compact.format(profile.market_cap)} ${profile.currency ?? ""}` : null}
                </Field>
                <Field label="Trading currency">{profile.currency}</Field>
                <Field label="Reporting currency">{profile.financial_currency}</Field>
                <Field label="Website">
                  {profile.website && /^https?:\/\//.test(profile.website) ? (
                    <a href={profile.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {profile.website}
                    </a>
                  ) : null}
                </Field>
              </dl>
              {profile.description ? (
                <p className="mt-5 text-sm leading-relaxed text-gray-700">{profile.description}</p>
              ) : (
                <p className="mt-5 text-sm text-gray-500">No business description is available for this company.</p>
              )}
            </>
          )}
        </div>
      )}

      {/* ---------- Statement tabs ---------- */}
      {tab !== "profile" && (
        <div className="mt-5">
          {finLoading && <p className="text-sm text-gray-500">Loading {frequency} {STATEMENT_LABEL[tab]} from Yahoo Finance...</p>}
          {finError && <p className="text-sm text-red-600">{finError}</p>}

          {statement && !statement.available && (
            <p className="text-sm text-gray-500">
              No {frequency} {STATEMENT_LABEL[tab]} is available from Yahoo for this company. Banks, newly
              listed companies and some foreign listings often have gaps, or Yahoo may be temporarily unavailable.
            </p>
          )}

          {statement?.available && (
            <>
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-sm text-gray-500">
                <span>
                  {fin.currency ? `Amounts in ${fin.currency} (reporting currency), shown in compact form. Hover a number for the full value.` : "Amounts shown in compact form. Hover a number for the full value."}
                </span>
                {canToggle && (
                  <button onClick={() => setShowAll(!showAll)} className="font-medium text-blue-600 hover:underline">
                    {showAll ? "Show key items only" : `Show all ${statement.rows.length} line items`}
                  </button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="border-b text-gray-500">
                    <tr>
                      <th className="py-2 pr-4">Line item</th>
                      {statement.periods.map((p) => (
                        <th key={p} className="py-2 pr-4 text-right font-medium">{p}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {rows.map((r) => (
                      <tr key={r.item}>
                        <td className="py-2 pr-4 font-medium text-gray-900">{r.item}</td>
                        {r.values.map((v, i) => (
                          <td key={i} className="py-2 pr-4 text-right tabular-nums" title={v == null ? "" : v.toLocaleString()}>
                            {v == null ? "-" : compact.format(v)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      )}

      <p className="mt-5 text-xs text-gray-400">Source: Yahoo Finance (unofficial data, may contain gaps).</p>
    </div>
  );
}