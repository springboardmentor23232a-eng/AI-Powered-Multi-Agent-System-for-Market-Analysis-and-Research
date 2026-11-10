import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { api, downloadReport } from "../api/client";
import type {
  AgentName, AgentOutput, Claim, Contradiction, FundamentalData, NewsData, RiskData, TaskDetail, TechnicalData,
} from "../api/types";
import { ClaimTag, EvidenceBadge, SignalPill, StatusPill } from "../components/Badges";
import { TechnicalCharts } from "../components/Charts";
import { ContradictionMatrix } from "../components/ContradictionMatrix";
import { ClaimsTable, FundamentalsPanel, NewsPanel, RiskPanel } from "../components/Panels";
import { isTerminal } from "../lib/format";
import type { MatrixAgent } from "../lib/matrix";

interface Loaded {
  report: string;
  claims: Claim[];
  contradictions: Contradiction[];
  fundamental: AgentOutput<FundamentalData> | null;
  technical: AgentOutput<TechnicalData> | null;
  news: AgentOutput<NewsData> | null;
  risk: AgentOutput<RiskData> | null;
}

const TABS = ["Summary", "Charts", "Fundamentals", "News", "Risk", "Claims"] as const;
type Tab = (typeof TABS)[number];

const optional = <T,>(p: Promise<T>): Promise<T | null> => p.catch(() => null);

export default function ResearchPage() {
  const { id = "" } = useParams();
  const [detail, setDetail] = useState<TaskDetail | null>(null);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [tab, setTab] = useState<Tab>("Summary");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const d = await api.detail(id);
        if (stop) return;
        setDetail(d);
        if (!isTerminal(d.status)) timer = setTimeout(tick, 2000);
      } catch {
        if (!stop) setError("Could not load this research task");
      }
    };
    tick();
    return () => { stop = true; clearTimeout(timer); };
  }, [id]);

  const status = detail?.status;
  useEffect(() => {
    if (!status || !isTerminal(status) || status === "failed") return;
    let stop = false;
    Promise.all([
      api.report(id), api.claims(id), api.contradictions(id),
      optional(api.agent<FundamentalData>(id, "fundamental")), optional(api.agent<TechnicalData>(id, "technical")),
      optional(api.agent<NewsData>(id, "news")), optional(api.agent<RiskData>(id, "risk")),
    ]).then(([r, claims, contradictions, fundamental, technical, news, risk]) => {
      if (!stop) setLoaded({ report: r.content, claims, contradictions, fundamental, technical, news, risk });
    }).catch(() => !stop && setError("Could not load the report"));
    return () => { stop = true; };
  }, [id, status]);

  if (error) return <p role="alert" className="text-red-700">{error}</p>;
  if (!detail) return <p className="text-slate-500">Loading…</p>;

  const running = !isTerminal(detail.status);
  const ok = (a: AgentOutput<{ signal?: never }> | AgentOutput<unknown> | null) => a?.status === "success";
  const signals: Record<MatrixAgent, FundamentalData["signal"] | null> = {
    fundamental: loaded && ok(loaded.fundamental) ? loaded.fundamental!.data.signal : null,
    technical: loaded && ok(loaded.technical) ? loaded.technical!.data.signal : null,
    news: loaded && ok(loaded.news) ? loaded.news!.data.signal : null,
  };

  return (
    <div className="space-y-4">
      <Link to="/" className="text-sm text-slate-600 underline">← Back</Link>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{detail.ticker} <span className="text-base font-normal text-slate-500">{detail.market} · {detail.period}{detail.as_of ? ` · replay as of ${detail.as_of}` : ""}</span></h1>
          <div className="mt-1 flex items-center gap-2"><StatusPill status={detail.status} />
            {detail.latency_ms !== null && <span className="text-xs text-slate-500">{(detail.latency_ms / 1000).toFixed(1)}s</span>}</div>
        </div>
        <div className="flex items-center gap-3">
          {detail.evidence.total > 0 && <EvidenceBadge {...detail.evidence} />}
          {loaded && <button onClick={() => downloadReport(id, detail.ticker)} className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm">Download Markdown</button>}
        </div>
      </div>

      <div className="flex flex-wrap gap-2" aria-label="Agent status">
        {["fundamental", "technical", "news", "risk"].map((name) => {
          const a = detail.agents.find((x) => x.agent === (name as AgentName));
          return <span key={name} className="flex items-center gap-1 text-xs capitalize text-slate-600">{name} {a ? <StatusPill status={a.status} /> : running ? <StatusPill status="running" /> : null}{a && a.attempts > 1 && <span className="text-slate-400">({a.attempts} attempts)</span>}</span>;
        })}
      </div>

      {running && <p className="rounded border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">Agents are working. This page updates automatically.</p>}
      {detail.status === "failed" && <p role="alert" className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">{detail.error ?? "Research failed."}</p>}

      {loaded && (
        <>
          <nav className="flex gap-1 overflow-x-auto border-b border-slate-200" role="tablist">
            {TABS.map((t) => (
              <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
                className={`whitespace-nowrap px-3 py-2 text-sm ${tab === t ? "border-b-2 border-slate-900 font-medium" : "text-slate-500"}`}>{t}</button>
            ))}
          </nav>

          {tab === "Summary" && (
            <div className="space-y-6">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap gap-3 text-sm">
                  {(["fundamental", "technical", "news"] as MatrixAgent[]).map((a) => <span key={a} className="capitalize">{a}: <SignalPill signal={signals[a]} /></span>)}
                </div>
                <ContradictionMatrix signals={signals} contradictions={loaded.contradictions} />
              </div>
              <article className="report rounded-lg border border-slate-200 bg-white p-4">
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
                  code: ({ children }) => {
                    const m = /^\[(FACT|CALC|AI) · (.+)\]$/.exec(String(children));
                    if (!m) return <code>{children}</code>;
                    const type = m[1] === "CALC" ? "CALCULATED" : m[1] === "AI" ? "INTERPRETATION" : "FACT";
                    return <span className="ml-1 whitespace-nowrap"><ClaimTag type={type} /> <span className="font-mono text-[11px] text-slate-400">{m[2]}</span></span>;
                  },
                }}>{loaded.report}</ReactMarkdown>
              </article>
            </div>
          )}
          {tab === "Charts" && (loaded.technical && ok(loaded.technical) ? <TechnicalCharts chart={loaded.technical.data.chart} /> : <Unavailable agent={loaded.technical} name="Technical analysis" />)}
          {tab === "Fundamentals" && (loaded.fundamental && ok(loaded.fundamental) ? <FundamentalsPanel data={loaded.fundamental.data} limitations={loaded.fundamental.limitations} /> : <Unavailable agent={loaded.fundamental} name="Fundamental analysis" />)}
          {tab === "News" && (loaded.news && ok(loaded.news) ? <NewsPanel data={loaded.news.data} limitations={loaded.news.limitations} /> : <Unavailable agent={loaded.news} name="News analysis" />)}
          {tab === "Risk" && (loaded.risk && ok(loaded.risk) ? <RiskPanel data={loaded.risk.data} limitations={loaded.risk.limitations} /> : <Unavailable agent={loaded.risk} name="Risk analysis" />)}
          {tab === "Claims" && <ClaimsTable claims={loaded.claims} />}
        </>
      )}
    </div>
  );
}

function Unavailable({ agent, name }: { agent: AgentOutput<unknown> | null; name: string }) {
  const why = agent?.error ?? agent?.limitations?.join("; ") ?? "This analysis was not run.";
  return <p className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900"><strong>{name} unavailable.</strong> {why}</p>;
}
