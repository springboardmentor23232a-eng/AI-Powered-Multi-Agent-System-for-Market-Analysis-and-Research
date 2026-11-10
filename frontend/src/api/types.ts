export type Signal = "bullish" | "bearish" | "neutral";
export type TaskStatus = "queued" | "running" | "completed" | "partial" | "failed";
export type AgentName = "fundamental" | "technical" | "news" | "risk";

export interface TaskSummary {
  task_id: string;
  ticker: string;
  company_name?: string | null;
  market: string;
  requested_period?: string;
  status: TaskStatus;
  created_at: string;
  completed_at: string | null;
}

export interface TaskDetail extends TaskSummary {
  period: string;
  as_of: string | null;
  latency_ms: number | null;
  tokens_used: number | null;
  error: string | null;
  agents: { agent: AgentName; status: string; attempts: number; latency_ms: number | null; error: string | null }[];
  evidence: { total: number; verified: number; percent: number };
}

export interface FundamentalData {
  metrics: Record<string, number | null>;
  trend: Record<string, number[]>;
  signal: Signal;
  summary: string;
}

export interface ChartSeries {
  dates: string[];
  close: number[];
  sma50: (number | null)[];
  sma200: (number | null)[];
  rsi14: (number | null)[];
  macd: (number | null)[];
  macd_signal: (number | null)[];
}

export interface TechnicalData {
  indicators: Record<string, number | null>;
  conditions: string[];
  signal: Signal;
  summary: string;
  chart: ChartSeries;
}

export interface NewsItem {
  title: string;
  url: string;
  published_at: string | null;
  sentiment: "positive" | "negative" | "neutral";
  event_type: string | null;
}

export interface NewsData {
  items: NewsItem[];
  signal: Signal;
  summary: string;
}

export interface Contradiction {
  agent_a: string;
  agent_b: string;
  severity: string;
  description: string;
}

export interface RiskData {
  volatility_annualized: number | null;
  max_drawdown: number | null;
  risks: string[];
  scenarios: string[];
  stale_or_missing: string[];
  contradictions: Contradiction[];
  summary: string;
}

export interface AgentOutput<T> {
  agent: AgentName;
  status: string;
  attempts: number;
  error: string | null;
  data: T;
  limitations: string[];
}

export interface Claim {
  claim_id: string;
  agent: AgentName;
  type: "FACT" | "CALCULATED" | "INTERPRETATION";
  text: string;
  evidence: Record<string, unknown>;
  verified: boolean;
  note: string | null;
}

export interface SearchHit {
  ticker: string;
  name: string;
  market: string;
}

export interface WatchItem {
  ticker: string;
  name: string | null;
}

export interface Preferences {
  market: string;
  analysis_period: string;
}
