import { lazy, Suspense } from "react";
import type { ChartSeries } from "../api/types";

const PlotlyChart = lazy(() => import("./PlotlyChart"));
const fallback = <div className="h-64 animate-pulse rounded bg-slate-100" />;

export function TechnicalCharts({ chart }: { chart: ChartSeries }) {
  const x = chart.dates;
  return (
    <div className="space-y-4">
      <Suspense fallback={fallback}>
        <Block title="Price and moving averages">
          <PlotlyChart height={320} data={[
            { x, y: chart.close, type: "scatter", mode: "lines", name: "Close", line: { color: "#0f172a", width: 1.5 } },
            { x, y: chart.sma50, type: "scatter", mode: "lines", name: "SMA 50", line: { color: "#2563eb", width: 1 } },
            { x, y: chart.sma200, type: "scatter", mode: "lines", name: "SMA 200", line: { color: "#dc2626", width: 1 } },
          ]} />
        </Block>
        <Block title="RSI (14)">
          <PlotlyChart height={200} layout={{ yaxis: { range: [0, 100], gridcolor: "#e2e8f0" }, shapes: [
            { type: "line", xref: "paper", x0: 0, x1: 1, y0: 70, y1: 70, line: { color: "#dc2626", dash: "dot", width: 1 } },
            { type: "line", xref: "paper", x0: 0, x1: 1, y0: 30, y1: 30, line: { color: "#059669", dash: "dot", width: 1 } },
          ] }} data={[{ x, y: chart.rsi14, type: "scatter", mode: "lines", name: "RSI", line: { color: "#7c3aed", width: 1.5 } }]} />
        </Block>
        <Block title="MACD (12, 26, 9)">
          <PlotlyChart height={220} data={[
            { x, y: chart.macd, type: "scatter", mode: "lines", name: "MACD", line: { color: "#2563eb", width: 1.2 } },
            { x, y: chart.macd_signal, type: "scatter", mode: "lines", name: "Signal", line: { color: "#f59e0b", width: 1.2 } },
          ]} />
        </Block>
      </Suspense>
      <p className="text-xs text-slate-500">Indicators describe historical conditions and are not predictions.</p>
    </div>
  );
}

export function TrendChart({ trend }: { trend: Record<string, number[]> }) {
  const labels = (trend.revenue ?? []).map((_, i) => `Y${i + 1}`);
  return (
    <Suspense fallback={fallback}>
      <PlotlyChart height={240} data={[
        { x: labels, y: trend.revenue ?? [], type: "bar", name: "Revenue", marker: { color: "#2563eb" } },
        { x: labels, y: trend.net_income ?? [], type: "bar", name: "Net income", marker: { color: "#059669" } },
      ]} layout={{ barmode: "group" }} />
    </Suspense>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h4>
      {children}
    </div>
  );
}
