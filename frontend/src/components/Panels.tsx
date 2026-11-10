import type { Claim, FundamentalData, NewsData, RiskData } from "../api/types";
import { num, pct, shortDate } from "../lib/format";
import { ClaimTag, SignalPill } from "./Badges";
import { TrendChart } from "./Charts";

const Card = ({ title, children, aside }: { title: string; children: React.ReactNode; aside?: React.ReactNode }) => (
  <section className="rounded-lg border border-slate-200 bg-white p-4">
    <div className="mb-2 flex items-center justify-between"><h3 className="text-sm font-semibold text-slate-700">{title}</h3>{aside}</div>
    {children}
  </section>
);

const Limits = ({ items }: { items: string[] }) =>
  items.length ? (
    <ul className="mt-3 list-disc space-y-0.5 pl-5 text-xs text-slate-500">{items.map((l, i) => <li key={i}>{l}</li>)}</ul>
  ) : null;

const METRICS: [string, string, (x: number | null) => string][] = [
  ["revenue_growth", "Revenue growth", pct], ["net_margin", "Net margin", pct], ["operating_margin", "Operating margin", pct],
  ["debt_to_equity", "Debt to equity", num], ["roe", "Return on equity", pct], ["pe", "P/E", num], ["pb", "P/B", num],
];

export function FundamentalsPanel({ data, limitations }: { data: FundamentalData; limitations: string[] }) {
  return (
    <div className="space-y-4">
      <Card title="Key metrics" aside={<SignalPill signal={data.signal} />}>
        <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {METRICS.map(([key, label, fmt]) => (
            <div key={key} className="rounded border border-slate-100 p-2">
              <dt className="text-xs text-slate-500">{label}</dt>
              <dd className="text-lg font-semibold">{fmt(data.metrics[key] ?? null)}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-3 text-sm">{data.summary}</p>
        <Limits items={limitations} />
      </Card>
      {(data.trend.revenue?.length ?? 0) > 0 && <Card title="Revenue and net income by year (oldest to newest)"><TrendChart trend={data.trend} /></Card>}
    </div>
  );
}

const SENT = { positive: "text-emerald-700", negative: "text-red-700", neutral: "text-slate-600" } as const;

export function NewsPanel({ data, limitations }: { data: NewsData; limitations: string[] }) {
  return (
    <Card title="News and sentiment" aside={<SignalPill signal={data.signal} />}>
      <p className="mb-3 text-sm">{data.summary}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-slate-500"><th className="py-1 pr-3">Date</th><th className="pr-3">Sentiment</th><th className="pr-3">Event</th><th>Headline</th></tr></thead>
          <tbody>
            {data.items.map((n) => (
              <tr key={n.url} className="border-t border-slate-100 align-top">
                <td className="py-1.5 pr-3 whitespace-nowrap">{shortDate(n.published_at)}</td>
                <td className={`pr-3 font-medium ${SENT[n.sentiment]}`}>{n.sentiment}</td>
                <td className="pr-3">{n.event_type}</td>
                <td><a className="text-blue-700 underline" href={n.url} target="_blank" rel="noreferrer">{n.title}</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Limits items={limitations} />
    </Card>
  );
}

export function RiskPanel({ data, limitations }: { data: RiskData; limitations: string[] }) {
  return (
    <div className="space-y-4">
      <Card title="Risk metrics">
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded border border-slate-100 p-2"><div className="text-xs text-slate-500">Annualised volatility</div><div className="text-lg font-semibold">{pct(data.volatility_annualized)}</div></div>
          <div className="rounded border border-slate-100 p-2"><div className="text-xs text-slate-500">Maximum drawdown</div><div className="text-lg font-semibold">{pct(data.max_drawdown)}</div></div>
        </div>
        <p className="mt-3 text-sm">{data.summary}</p>
      </Card>
      <Card title="Risk flags">
        {data.risks.length ? <ul className="list-disc space-y-1 pl-5 text-sm">{data.risks.map((r, i) => <li key={i}>{r}</li>)}</ul> : <p className="text-sm text-slate-500">No rule-based risk flags triggered.</p>}
      </Card>
      <Card title="Alternative scenarios (AI-written, qualitative)">
        <ul className="list-disc space-y-1 pl-5 text-sm">{data.scenarios.map((s, i) => <li key={i}>{s}</li>)}</ul>
      </Card>
      {data.stale_or_missing.length > 0 && <Card title="Missing or stale information"><Limits items={data.stale_or_missing} /></Card>}
      <Limits items={limitations} />
    </div>
  );
}

export function ClaimsTable({ claims }: { claims: Claim[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs text-slate-500">
          <tr><th className="px-3 py-2">ID</th><th>Type</th><th>Claim</th><th>Verified</th><th className="pr-3">Evidence</th></tr>
        </thead>
        <tbody>
          {claims.map((c) => (
            <tr key={c.claim_id} className="border-t border-slate-100 align-top">
              <td className="px-3 py-2 font-mono text-xs">{c.claim_id}</td>
              <td className="py-2"><ClaimTag type={c.type} /></td>
              <td className="py-2 pr-3">{c.text}</td>
              <td className="py-2">{c.verified ? <span className="text-emerald-700">verified</span> : <span className="text-red-700" title={c.note ?? ""}>blocked</span>}</td>
              <td className="py-2 pr-3"><details><summary className="cursor-pointer text-xs text-blue-700">view</summary>
                <pre className="mt-1 max-w-md overflow-x-auto whitespace-pre-wrap rounded bg-slate-50 p-2 text-[11px]">{JSON.stringify(c.evidence, null, 2).slice(0, 1200)}</pre></details></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
