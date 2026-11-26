import Plotly from "plotly.js-finance-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import { useMemo } from "react";
import { plotlyTheme } from "../plotlyTheme.js";
import { useTheme } from "../ThemeContext.jsx";

const Plot = createPlotlyComponent(Plotly);

// Three stacked panels: price + SMA20/50 + EMA12/26, RSI(14) with 30/70 lines, MACD + signal + histogram.
// All series come from the Technical agent (computed on the server); nothing is recalculated here.
export default function TechnicalChart({ chart, currency }) {
  const { theme } = useTheme();
  const t = useMemo(() => plotlyTheme(theme), [theme]);
  const x = chart.dates;
  const line = (y, name, color, extra = {}) => ({ type: "scatter", mode: "lines", x, y, name, line: { color, width: 1.6, ...extra }, connectgaps: false });
  const dark = theme === "dark";
  const data = [
    { type: "candlestick", x, open: chart.open, high: chart.high, low: chart.low, close: chart.close, name: "Price",
      increasing: { line: { color: t.up } }, decreasing: { line: { color: t.down } } },
    line(chart.sma20, "SMA 20", t.line), line(chart.sma50, "SMA 50", t.accent),
    line(chart.ema12, "EMA 12", dark ? "#c4a1ff" : "#7c3aed", { dash: "dot" }), line(chart.ema26, "EMA 26", dark ? "#67e8f9" : "#0e7490", { dash: "dot" }),
    { ...line(chart.rsi14, "RSI 14", dark ? "#c4a1ff" : "#7c3aed", { dash: "solid" }), xaxis: "x", yaxis: "y2" },
    { ...line(chart.macd, "MACD", dark ? "#67e8f9" : "#0e7490"), yaxis: "y3" }, { ...line(chart.macd_signal, "Signal", t.accent), yaxis: "y3" },
    { type: "bar", x, y: chart.macd_hist, name: "Histogram", yaxis: "y3", marker: { color: chart.macd_hist.map((v) => (v == null || v >= 0 ? t.up : t.down)) }, opacity: 0.6 },
  ];
  const guide = (y) => ({ type: "line", xref: "paper", x0: 0, x1: 1, yref: "y2", y0: y, y1: y, line: { color: t.muted, width: 1, dash: "dash" } });
  const layout = {
    autosize: true, height: 640, margin: { t: 10, r: 10, b: 40, l: 55 }, paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor, font: t.font,
    legend: { orientation: "h", y: 1.06 }, hoverlabel: { bgcolor: dark ? "#172238" : "#ffffff", font: { color: t.font.color } },
    xaxis: { rangeslider: { visible: false }, type: "date", gridcolor: t.gridcolor },
    yaxis: { title: { text: `Price (${currency || ""})` }, domain: [0.42, 1], gridcolor: t.gridcolor },
    yaxis2: { title: { text: "RSI" }, domain: [0.22, 0.38], range: [0, 100], tickvals: [30, 50, 70], gridcolor: t.gridcolor },
    yaxis3: { title: { text: "MACD" }, domain: [0, 0.18], gridcolor: t.gridcolor },
    shapes: [guide(30), guide(70)],
  };
  return <Plot data={data} layout={layout} config={{ displaylogo: false, responsive: true }} style={{ width: "100%" }} useResizeHandler />;
}
