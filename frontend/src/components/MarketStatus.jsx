import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { currencyLabel } from "../format";

export default function MarketStatus({ preferred }) {
  const [markets, setMarkets] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = () =>
      api
        .get("/markets")
        .then((res) => !cancelled && setMarkets(res.data))
        .catch((err) => !cancelled && setError(errorMessage(err)));
    load();
    const timer = setInterval(load, 60000); // refresh every minute
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="rounded-xl bg-white p-6 shadow">
      <h3 className="font-semibold text-gray-900">Supported markets</h3>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {markets.map((m) => (
          <div
            key={m.market}
            className={`rounded-lg border p-4 ${
              m.market === preferred ? "border-blue-500 ring-1 ring-blue-500" : "border-gray-200"
            }`}
          >
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-gray-900">{m.market}</h4>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  m.status === "open" ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"
                }`}
              >
                {m.status === "open" ? "Open" : "Closed"}
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500">
              {m.name} · {m.country}
            </p>
            {m.market === preferred && (
              <p className="mt-1 text-xs font-medium text-blue-600">Your selected market</p>
            )}

            <dl className="mt-3 space-y-1 text-sm">
              <div className="flex justify-between gap-2">
                <dt className="text-gray-500">Local time</dt>
                <dd className="text-right text-gray-900">{m.local_time} {m.tz_label}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-gray-500">Hours</dt>
                <dd className="text-gray-900">{m.hours}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-gray-500">Currency</dt>
                <dd className="text-gray-900">{currencyLabel(m.currency)}</dd>
              </div>
              <div className="flex justify-between gap-2">
                <dt className="text-gray-500">Ticker format</dt>
                <dd className="text-gray-900">{m.ticker_example}</dd>
              </div>
            </dl>

            <p className="mt-3 text-xs text-gray-500">
              {m.reason}
              {m.next_open ? ` · next open ${m.next_open}` : ""}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-4 text-xs text-gray-400">
        Status uses regular weekday trading hours. Exchange holidays are not included, so on a
        holiday a market may show Open while it is actually closed.
      </p>
    </div>
  );
}