import Plotly from "plotly.js-finance-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import { useMemo } from "react";
import { plotlyTheme } from "../plotlyTheme.js";
import { useTheme } from "../ThemeContext.jsx";

const Plot = createPlotlyComponent(Plotly);

// Candlestick (OHLC) + volume bars. Loaded lazily from StockExplorer so Plotly stays out of the login bundle.
// Colours come from plotlyTheme(), so the chart re-renders when the user toggles light / dark.
export default function PriceChart({ rows, currency }) {
  const { theme } = useTheme();
  const t = useMemo(() => plotlyTheme(theme), [theme]);
  const x = rows.map((r) => r.date);
  const data = [
    {
      type: "candlestick", x, open: rows.map((r) => r.open), high: rows.map((r) => r.high),
      low: rows.map((r) => r.low), close: rows.map((r) => r.close), name: "Price",
      increasing: { line: { color: t.up } }, decreasing: { line: { color: t.down } },
    },
    { type: "bar", x, y: rows.map((r) => r.volume), name: "Volume", yaxis: "y2", marker: { color: t.muted } },
  ];
  const layout = {
    autosize: true, height: 420, margin: { t: 10, r: 10, b: 40, l: 55 }, showlegend: false,
    paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor, font: t.font,
    hoverlabel: { bgcolor: theme === "dark" ? "#172238" : "#ffffff", font: { color: t.font.color } },
    xaxis: { rangeslider: { visible: false }, type: "date", gridcolor: t.gridcolor },
    yaxis: { title: { text: `Price (${currency})` }, domain: [0.27, 1], gridcolor: t.gridcolor },
    yaxis2: { title: { text: "Volume" }, domain: [0, 0.2], gridcolor: t.gridcolor },
  };
  return <Plot data={data} layout={layout} config={{ displaylogo: false, responsive: true }} style={{ width: "100%" }} useResizeHandler />;
}
