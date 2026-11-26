import { lazy, Suspense } from "react";

const TechnicalChart = lazy(() => import("./TechnicalChart.jsx"));

const label = (k) => k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const PEER_LABEL = { net_margin: "Net profit margin", roe: "ROE (on year-end equity)", debt_to_equity: "Debt-to-equity (reported)" };
const num = (n, d = 2) => (n == null ? "—" : Number(n).toLocaleString(undefined, { maximumFractionDigits: d }));
const when = (s) => (s ? new Date(s).toLocaleString() : "date not given");
const ratioText = (r) => (r.value == null ? "Not available" : r.unit === "%" ? `${num(r.value * 100, 1)}%` : `${num(r.value, 2)}×`);

const KIND = {
  fact: ["Fact", "bg-slate-100 text-slate-700"],
  calculated: ["Calculated", "bg-green-100 text-green-800"],
  interpretation: ["Interpretation", "bg-amber-100 text-amber-800"],
};
const TONE = { positive: "text-green-700", negative: "text-red-700", caution: "text-amber-700", neutral: "" };

export function Banner({ children, tone = "amber" }) {
  const c = tone === "red" ? "border-red-200 bg-red-50 text-red-700" : "border-amber-200 bg-amber-50 text-amber-800";
  return <p role={tone === "red" ? "alert" : undefined} className={`rounded-lg border p-2 text-xs ${c}`}>{children}</p>;
}

export function Findings({ items }) {
  if (!items?.length) return null;
  return (
    <ul className="space-y-1.5">
      {items.map((f, i) => {
        const [k, cls] = KIND[f.kind] || KIND.interpretation;
        return (
          <li key={i} className="flex items-start gap-2 text-sm">
            <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls}`}>{k}</span>
            <span className={TONE[f.tone]}>{f.text}</span>
          </li>
        );
      })}
    </ul>
  );
}

function Foot({ a }) {
  return (
    <div className="space-y-1 border-t border-slate-200 pt-2 text-xs text-slate-500">
      {a.limitations?.length > 0 && <ul className="list-disc pl-5">{a.limitations.map((l, i) => <li key={i}>{l}</li>)}</ul>}
      {a.sources?.map((s, i) => (
        <p key={i}>Source: {s.url ? <a className="text-brand-600 underline" href={s.url} target="_blank" rel="noreferrer">{s.name}</a> : s.name}
          {s.synthetic && <b> (synthetic)</b>}{s.retrieved_at && ` · retrieved ${when(s.retrieved_at)}`}</p>
      ))}
      <p>Rule-based analysis for study purposes. Not investment advice, not a prediction.</p>
    </div>
  );
}

// An agent that did not complete says so plainly - no placeholder numbers.
function NotDone({ a, name }) {
  return (
    <div className="space-y-2">
      <Banner tone="red">{name} analysis is {a.status.toLowerCase()}. {a.summary}</Banner>
      {a.error && <p className="text-xs text-slate-500">Reason: {a.error}</p>}
      <Foot a={a} />
    </div>
  );
}

function Head({ a }) {
  return <p className="text-sm font-medium">{a.summary}</p>;
}

// ------------------------------------------------------------------------------------------ Technical
export function TechnicalPanel({ a }) {
  if (a.status !== "Completed") return <NotDone a={a} name="Technical" />;
  const ind = a.indicators;
  const cards = [["Last close", num(ind.last_close)], ["SMA 20", num(ind.sma_20)], ["SMA 50", num(ind.sma_50)], ["SMA 200", num(ind.sma_200)],
    ["EMA 12", num(ind.ema_12)], ["EMA 26", num(ind.ema_26)], ["RSI 14", num(ind.rsi_14, 1)], ["MACD", num(ind.macd, 3)],
    ["MACD signal", num(ind.macd_signal, 3)], ["Histogram", num(ind.macd_histogram, 3)]];
  return (
    <div className="space-y-3">
      <Head a={a} />
      <Suspense fallback={<div className="skeleton h-80" />}><TechnicalChart chart={a.chart} currency={a.currency} /></Suspense>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5">
        {cards.map(([k, v]) => <div key={k} className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">{k}</div><div className="font-semibold tabular-nums">{v}</div></div>)}
      </div>
      <h4 className="text-sm font-semibold">What the indicators show</h4>
      <ul className="space-y-1 text-sm">
        {a.conditions.map((c) => (
          <li key={c.code}><span className={`mr-2 text-xs font-semibold uppercase ${c.bias === "bullish" ? "text-green-700" : c.bias === "bearish" ? "text-red-700" : "text-slate-500"}`}>{c.bias}</span>{c.text}</li>
        ))}
      </ul>
      <Findings items={a.findings.filter((f) => !a.conditions.some((c) => c.text === f.text))} />
      <Foot a={a} />
    </div>
  );
}

// ---------------------------------------------------------------------------------------- Fundamental
export function FundamentalPanel({ a }) {
  if (a.status !== "Completed") return <NotDone a={a} name="Fundamental" />;
  const hist = a.history?.periods?.length ? a.history : null;
  const fmtHist = (k, v) => (v == null ? "—" : k === "net_margin" ? `${num(v * 100, 1)}%` : num(v, 2).length > 9 ? new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 2 }).format(v) : num(v, 2));
  return (
    <div className="space-y-3">
      <Head a={a} />
      {a.sources?.some((s) => s.synthetic) && <Banner>This analysis uses <b>synthetic demo financials</b>. Valuation ratios are not computed on synthetic data.</Banner>}
      <p className="text-xs text-slate-500">Basis: {a.basis || "—"}{a.latest_period && ` · latest period ${a.latest_period.slice(0, 4)}`}{a.currency && ` · ${a.currency}`}</p>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {a.ratios.map((r) => (
          <div key={r.key} className="rounded-lg bg-slate-50 p-3" title={`${r.formula}\n${Object.entries(r.inputs || {}).map(([k, v]) => `${k} = ${v}`).join(", ")}`}>
            <div className="flex items-center justify-between text-xs text-slate-500"><span>{r.name}</span><span>{r.kind}</span></div>
            <div className={`text-lg font-semibold tabular-nums ${r.value == null ? "text-slate-400" : ""}`}>{ratioText(r)}</div>
            <div className="text-[11px] text-slate-500">{r.value == null ? r.reason_unavailable : r.formula}</div>
          </div>
        ))}
      </div>
      {hist && (
        <div className="overflow-x-auto">
          <h4 className="mb-1 text-sm font-semibold">History</h4>
          <table className="w-full text-sm">
            <thead><tr className="border-b text-left text-xs text-slate-500"><th className="py-1 pr-3">Metric</th>{hist.periods.map((p) => <th key={p} className="px-2 py-1 text-right">{String(p).slice(0, 4)}</th>)}</tr></thead>
            <tbody>{Object.entries(hist.series).map(([k, vals]) => (
              <tr key={k} className="border-b last:border-0"><td className="py-1 pr-3">{label(k)}</td>{vals.map((v, i) => <td key={i} className="px-2 py-1 text-right tabular-nums">{fmtHist(k, v)}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {a.peers && (
        <div className="rounded-lg bg-slate-50 p-3 text-sm">
          <h4 className="mb-1 font-semibold">Peers: {a.peers.category}, {a.peers.year} ({a.peers.count} companies in the reference dataset)</h4>
          <table className="w-full text-xs">
            <thead><tr className="text-left text-slate-500"><th className="py-1">Ratio</th><th className="text-right">This company</th><th className="text-right">Peer median</th></tr></thead>
            <tbody>{Object.entries(a.peers.median || {}).map(([k, m]) => (
              <tr key={k}><td className="py-0.5">{PEER_LABEL[k] || label(k)}</td><td className="text-right tabular-nums">{ratioText({ value: a.peers.company?.[k], unit: k === "debt_to_equity" ? "x" : "%" })}</td><td className="text-right tabular-nums">{ratioText({ value: m, unit: k === "debt_to_equity" ? "x" : "%" })}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {a.data_issues.length > 0 && <Banner>Data issues found: {a.data_issues.join(" ")}</Banner>}
      <Findings items={a.findings} />
      <Foot a={a} />
    </div>
  );
}

// -------------------------------------------------------------------------------------------- News
const SENT = { Positive: "bg-green-100 text-green-800", Negative: "bg-red-100 text-red-700", Neutral: "bg-slate-100 text-slate-700" };

export function NewsPanel({ a }) {
  if (a.status !== "Completed") return <NotDone a={a} name="News" />;
  const synthetic = a.articles.some((x) => x.synthetic);
  return (
    <div className="space-y-3">
      <Head a={a} />
      {synthetic && <Banner>These headlines are <b>SAMPLE text, not real news</b>. Set NEWS_PROVIDER=yahoo (no key needed) or newsapi for real headlines.</Banner>}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        {["Positive", "Negative", "Neutral"].map((k) => <span key={k} className={`rounded-full px-2 py-1 font-semibold ${SENT[k]}`}>{k}: {a.counts[k] ?? 0}</span>)}
        {a.tone && <span className="text-slate-500">Overall tone: <b>{a.tone}</b>{a.net_score != null && ` (net score ${num(a.net_score, 2)})`}</span>}
      </div>
      {a.conflicts.map((c, i) => <Banner key={i}>Conflicting signals: {c}</Banner>)}
      <ul className="divide-y divide-slate-100">
        {a.articles.map((x, i) => (
          <li key={i} className="space-y-1 py-2">
            <div className="flex items-start gap-2">
              <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase ${SENT[x.sentiment]}`}>{x.sentiment}</span>
              <div className="text-sm">
                {x.url ? <a className="font-medium text-brand-600 underline" href={x.url} target="_blank" rel="noreferrer">{x.title}</a> : <span className="font-medium">{x.title}</span>}
                <div className="text-xs text-slate-500">{x.source || "Unknown source"} · {when(x.published_at)}
                  {x.events.length > 0 && ` · events: ${x.events.join(", ")}`}{x.uncertain && " · uncertain wording (may, could, reportedly…)"}</div>
              </div>
            </div>
          </li>
        ))}
      </ul>
      <Findings items={a.findings} />
      <Foot a={a} />
    </div>
  );
}

// -------------------------------------------------------------------------------------------- Risk
const LEVEL = { Low: "border-green-200 bg-green-50 text-green-800", Moderate: "border-amber-200 bg-amber-50 text-amber-800", High: "border-red-200 bg-red-50 text-red-700" };
const METRICS = [["annualised_volatility_pct", "Annualised volatility", "%"], ["max_drawdown_pct", "Max drawdown", "%"], ["var_95_1d_pct", "1-day VaR (95%)", "%"],
  ["worst_day_pct", "Worst day", "%"], ["best_day_pct", "Best day", "%"], ["down_days_pct", "Down days", "%"]];

export function RiskPanel({ a }) {
  if (a.status !== "Completed") return <NotDone a={a} name="Risk" />;
  return (
    <div className="space-y-3">
      <Head a={a} />
      <div className={`rounded-lg border p-3 ${LEVEL[a.level] || ""}`}>
        <div className="text-xs">Overall risk level (rule-based)</div>
        <div className="text-xl font-bold">{a.level}</div>
        <ul className="mt-1 list-disc pl-5 text-xs">{a.level_basis.map((b, i) => <li key={i}>{b}</li>)}</ul>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {METRICS.map(([k, t, u]) => <div key={k} className="rounded-lg bg-slate-50 p-2"><div className="text-xs text-slate-500">{t}</div><div className="font-semibold tabular-nums">{a.metrics[k] == null ? "—" : `${num(a.metrics[k])}${u}`}</div></div>)}
      </div>
      {a.drawdown?.peak_date && <p className="text-xs text-slate-500">Largest drawdown: peak {a.drawdown.peak_date} → trough {a.drawdown.trough_date} ({a.drawdown.recovered ? "recovered" : "not yet recovered"}).</p>}
      {a.scenarios.length > 0 && (
        <div>
          <h4 className="mb-1 text-sm font-semibold">Scenarios from historical returns <span className="font-normal text-slate-500">(not forecasts)</span></h4>
          <div className="grid gap-2 sm:grid-cols-3">
            {a.scenarios.map((s) => (
              <div key={s.name} className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">{s.name}</div>
                <div className={`text-lg font-semibold ${s.return_pct >= 0 ? "text-green-700" : "text-red-700"}`}>{s.return_pct >= 0 ? "+" : ""}{num(s.return_pct, 1)}%</div>
                <div className="text-xs text-slate-500">≈ {num(s.price)} {a.currency}</div>
                <div className="mt-1 text-[11px] text-slate-500">{s.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {a.conflicts.map((c, i) => <Banner key={i}>Conflict {c.between.length > 1 ? `between ${c.between.join(" and ")} analysis` : `within ${c.between[0]} analysis`}: {c.description}</Banner>)}
      {[["Financial risks", a.financial_risks], ["Sector risks", a.sector_risks], ["Data gaps", a.data_gaps]].map(([t, items]) => items.length > 0 && (
        <div key={t}><h4 className="text-sm font-semibold">{t}</h4><ul className="list-disc pl-5 text-sm">{items.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
      ))}
      <Findings items={a.findings.filter((f) => ![...a.financial_risks, ...a.sector_risks, ...a.data_gaps, ...a.conflicts.map((c) => `Conflict: ${c.description}`)].includes(f.text))} />
      <Foot a={a} />
    </div>
  );
}

export const PANELS = { technical: TechnicalPanel, fundamental: FundamentalPanel, news: NewsPanel, risk: RiskPanel };
