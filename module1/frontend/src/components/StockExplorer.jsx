import { lazy, Suspense, useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import { Banner, PANELS } from "./AgentPanels.jsx";

const PriceChart = lazy(() => import("./PriceChart.jsx"));

const money = (n, cur = "") => (n == null ? "—" : `${Number(n).toLocaleString(undefined, { maximumFractionDigits: 2 })} ${cur}`.trim());
const compact = (n) => (n == null ? "—" : new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 2 }).format(n));
const label = (k) => k.replace(/_/g, " ").replace(/^./, (c) => c.toUpperCase());
const AGENT_TABS = [["technical", "Technical"], ["fundamental", "Fundamentals"], ["news", "News"], ["risk", "Risk"]];
const STATEMENTS = [["income_statement", "Income statement"], ["balance_sheet", "Balance sheet"], ["cash_flow", "Cash flow"]];

function SourceLine({ source }) {
  return (
    <p className="text-xs text-slate-500">
      Source: {source.url ? <a className="text-brand-600 underline" href={source.url} target="_blank" rel="noreferrer">{source.name}</a> : source.name}
      {" · retrieved "}{new Date(source.retrieved_at).toLocaleString()}
    </p>
  );
}

function Quality({ v }) {
  const bad = v.issues.filter((i) => i.severity !== "info");
  return (
    <div className={`rounded-lg border p-3 text-sm ${bad.length ? "border-amber-200 bg-amber-50 text-amber-900" : "border-green-200 bg-green-50 text-green-800"}`}>
      <b>Data check: </b>
      {v.rows_valid} of {v.rows_received} rows valid ({v.first_date} → {v.last_date}).
      {v.issues.length === 0 && " No missing values, duplicate dates or inconsistent prices found."}
      {v.issues.length > 0 && (
        <ul className="mt-1 list-disc pl-5 text-xs">
          {v.issues.map((i) => <li key={i.type}>{i.message} <i>({i.action}{i.example_dates.length ? `; e.g. ${i.example_dates.slice(0, 3).join(", ")}` : ""})</i></li>)}
        </ul>
      )}
    </div>
  );
}

function Profile({ data }) {
  const p = data.profile;
  return (
    <div className="space-y-3">
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {Object.entries(p).map(([k, v]) => (
          <div key={k} className="rounded-lg bg-slate-50 p-3">
            <dt className="text-xs text-slate-500">{label(k)}</dt>
            <dd className="break-words font-semibold">{v == null ? <span className="font-normal text-slate-400">Not available</span> : typeof v === "number" ? money(v) : String(v)}</dd>
          </div>
        ))}
      </dl>
      {data.warning && <p className="text-xs text-amber-700">⚠ {data.warning} Missing: {data.missing_fields.map(label).join(", ")}.</p>}
      <SourceLine source={data.source} />
    </div>
  );
}

function Financials({ data }) {
  const f = data.financials;
  return (
    <div className="space-y-4">
      {STATEMENTS.map(([key, title]) => (
        <div key={key} className="overflow-x-auto">
          <h4 className="mb-1 text-sm font-semibold">{title} <span className="font-normal text-slate-500">({f.currency})</span></h4>
          <table className="w-full text-sm">
            <thead><tr className="border-b text-left text-xs text-slate-500"><th className="py-1 pr-3">Metric</th>{f.periods.map((p) => <th key={p} className="px-2 py-1 text-right">{p.slice(0, 4)}</th>)}</tr></thead>
            <tbody>
              {Object.entries(f[key]).map(([m, vals]) => (
                <tr key={m} className="border-b last:border-0"><td className="py-1 pr-3">{label(m)}</td>{vals.map((v, i) => <td key={i} className="px-2 py-1 text-right tabular-nums">{compact(v)}</td>)}</tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      {f.missing_metrics.length > 0 && <p className="text-xs text-amber-700">⚠ Some figures are not available from the provider ("—"): {f.missing_metrics.length} gap(s). Nothing is estimated.</p>}
      <SourceLine source={data.source} />
    </div>
  );
}

export default function StockExplorer({ options, prefs }) {
  const [q, setQ] = useState("");
  const [market, setMarket] = useState("");            // "" = all markets
  const [hits, setHits] = useState([]);
  const [stock, setStock] = useState(null);
  const [period, setPeriod] = useState(prefs.analysis_period);
  const [tab, setTab] = useState("chart");
  const [state, setState] = useState({});              // { history, profile, financials, error, loading }
  const [analysis, setAnalysis] = useState({});    // { key, data, error, loading } - the four agents, fetched once per stock+period
  const seq = useRef(0);
  const aseq = useRef(0);

  // debounced search by company name or ticker
  useEffect(() => {
    if (!q.trim() || (stock && q === `${stock.ticker} – ${stock.name}`)) { setHits([]); return; }
    const t = setTimeout(() => {
      api(`/stocks/search?q=${encodeURIComponent(q.trim())}${market ? `&market=${market}` : ""}&limit=8`).then(setHits).catch(() => setHits([]));
    }, 250);
    return () => clearTimeout(t);
  }, [q, market, stock]);

  // load price history + profile + financials for the chosen stock
  useEffect(() => {
    if (!stock) return;
    const id = ++seq.current;
    const base = `/stocks/${stock.market}/${stock.ticker}`;
    setState({ loading: true });
    const settle = (p) => p.then((v) => ({ v })).catch((e) => ({ e: e.message }));
    Promise.all([settle(api(`${base}/history?period=${period}`)), settle(api(`${base}/profile`)), settle(api(`${base}/financials`))])
      .then(([h, p, f]) => { if (id === seq.current) setState({ history: h.v, profile: p.v, financials: f.v, errors: { history: h.e, profile: p.e, financials: f.e } }); });
  }, [stock, period]);

  // Milestone 2 agents: fetched lazily, once, when the first agent tab is opened (not on every tab switch)
  const isAgentTab = AGENT_TABS.some(([k]) => k === tab);
  useEffect(() => {
    if (!stock || !isAgentTab) return;
    const key = `${stock.market}:${stock.ticker}:${period}`;
    if (analysis.key === key) return;
    const id = ++aseq.current;
    setAnalysis({ key, loading: true });
    api(`/analysis/${stock.market}/${stock.ticker}/all?period=${period}`)
      .then((d) => id === aseq.current && setAnalysis({ key, data: d.agents }))
      .catch((e) => id === aseq.current && setAnalysis({ key, error: e.message }));
  }, [stock, period, tab]); // eslint-disable-line react-hooks/exhaustive-deps

  function pick(s) { setStock(s); setQ(`${s.ticker} – ${s.name}`); setHits([]); setTab("chart"); }

  const h = state.history;
  const first = h?.rows[0], last = h?.rows[h.rows.length - 1];
  const change = first && last ? ((last.close / first.close - 1) * 100) : null;

  return (
    <section className="card mb-6" aria-labelledby="explorer-h">
      <h2 id="explorer-h" className="mb-3 text-lg font-semibold">Stock search &amp; market data</h2>
      <div className="grid gap-3 sm:grid-cols-[1fr_9rem_9rem]">
        <div className="relative">
          <label className="label" htmlFor="ex-q">Company name or ticker</label>
          <input id="ex-q" className="input" placeholder="e.g. Apple, RELIANCE, TCS" value={q} autoComplete="off"
                 onChange={(e) => { setQ(e.target.value); setStock(null); }} />
          {hits.length > 0 && (
            <ul className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded-lg border border-slate-200 bg-white shadow-lg" role="listbox">
              {hits.map((s) => (
                <li key={`${s.market}:${s.ticker}`}>
                  <button type="button" className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50" onClick={() => pick(s)}>
                    <span><b>{s.ticker}</b> · {s.name}</span><span className="text-xs text-slate-500">{s.market}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <div>
          <label className="label" htmlFor="ex-m">Market</label>
          <select id="ex-m" className="input" value={market} onChange={(e) => setMarket(e.target.value)}>
            <option value="">All</option>{options.markets.map((m) => <option key={m.code} value={m.code}>{m.code}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="ex-p">Period</label>
          <select id="ex-p" className="input" value={period} onChange={(e) => setPeriod(e.target.value)}>
            {options.periods.map((p) => <option key={p.code} value={p.code}>{p.label}</option>)}
          </select>
        </div>
      </div>

      {!stock && <p className="mt-4 text-sm text-slate-500">Search for a company to see its price history, profile, financial statements, and the Technical, Fundamentals, News and Risk analysis.</p>}

      {stock && (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-base font-semibold">{stock.name} <span className="font-normal text-slate-500">({stock.ticker} · {stock.market})</span></h3>
            {h && last && <p className="text-sm">Last close <b>{money(last.close, h.currency)}</b>{" "}
              <span className={change >= 0 ? "text-green-700" : "text-red-700"}>({change >= 0 ? "+" : ""}{change.toFixed(2)}% over period)</span></p>}
          </div>
          <div role="tablist" className="flex gap-1 border-b border-slate-200">
            {[["chart", "Price chart"], ["profile", "Company profile"], ["financials", "Financials"], ...AGENT_TABS].map(([k, t]) => (
              <button key={k} role="tab" aria-selected={tab === k} onClick={() => setTab(k)}
                      className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${tab === k ? "border-brand-600 text-brand-700" : "border-transparent text-slate-500 hover:text-slate-800"}`}>{t}</button>
            ))}
          </div>
          {state.loading && <p className="text-sm text-slate-500">Loading market data…</p>}
          {!state.loading && tab === "chart" && (
            state.errors?.history ? <p role="alert" className="text-sm text-red-600">{state.errors.history}</p> : h && (
              <div className="space-y-3">
                {h.source.synthetic && <p className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">These prices are <b>synthetic demo data</b>, not real market prices. Set MARKET_DATA_PROVIDER=yahoo for real data.</p>}
                <Suspense fallback={<p className="text-sm text-slate-500">Loading chart…</p>}><PriceChart rows={h.rows} currency={h.currency} /></Suspense>
                <Quality v={h.validation} />
                <SourceLine source={h.source} />
              </div>
            )
          )}
          {!state.loading && tab === "profile" && (state.errors?.profile ? <p role="alert" className="text-sm text-red-600">{state.errors.profile}</p> : state.profile && <Profile data={state.profile} />)}
          {isAgentTab && (
            <div key={tab} className="reveal" role="tabpanel">
              {analysis.loading && <div role="status" className="space-y-3"><p className="text-sm text-slate-500">Running the research agents on {stock.ticker}…</p><div className="skeleton h-24" /><div className="skeleton h-40" /></div>}
              {analysis.error && <Banner tone="red">{analysis.error}</Banner>}
              {analysis.data && (() => { const Panel = PANELS[tab]; return <Panel a={analysis.data[tab]} />; })()}
            </div>
          )}
          {!state.loading && tab === "financials" && (state.errors?.financials ? <p role="alert" className="text-sm text-red-600">{state.errors.financials}</p> : state.financials && <Financials data={state.financials} />)}
        </div>
      )}
    </section>
  );
}
