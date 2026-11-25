import { useEffect, useRef, useState } from "react";
import Plotly from "plotly.js-dist-min";

const UP = "#00b386";
const DOWN = "#eb5b3c";
const BRAND = "#00b386";

export default function PlotChart({ rows, mode, onHover }) {
  const ref = useRef(null);
  const [failure, setFailure] = useState("");

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!rows.length) {
      Plotly.purge(el);
      return;
    }
    const x = rows.map((r) => r.date);
    const lo = Math.min(...rows.map((r) => r.low));
    const hi = Math.max(...rows.map((r) => r.high));
    const pad = (hi - lo) * 0.06 || hi * 0.02;

    const price =
      mode === "candles"
        ? {
            type: "candlestick", x,
            open: rows.map((r) => r.open), high: rows.map((r) => r.high),
            low: rows.map((r) => r.low), close: rows.map((r) => r.close),
            increasing: { line: { color: UP } }, decreasing: { line: { color: DOWN } },
            hoverinfo: "none", yaxis: "y",
          }
        : {
            type: "scatter", mode: "lines", x, y: rows.map((r) => r.close),
            line: { color: BRAND, width: 2 }, fill: "tozeroy", fillcolor: "rgba(0,179,134,0.10)",
            hoverinfo: "none", yaxis: "y",
          };

    const volume = {
      type: "bar", x, y: rows.map((r) => r.volume), yaxis: "y2",
      marker: { color: rows.map((r) => (r.close >= r.open ? "rgba(0,179,134,0.35)" : "rgba(235,91,60,0.35)")) },
      hoverinfo: "none",
    };

    const axis = { gridcolor: "rgba(28,28,40,0.07)", zeroline: false, linecolor: "#e8e8ed", tickfont: { color: "#7c7e8c" } };
    const layout = {
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
      margin: { l: 8, r: 56, t: 8, b: 28 },
      font: { family: "Inter, system-ui, sans-serif", size: 11, color: "#7c7e8c" },
      showlegend: false, hovermode: "x",
      xaxis: { ...axis, type: "date", anchor: "y2", rangeslider: { visible: false }, showgrid: false, showspikes: true, spikemode: "across", spikethickness: 1, spikecolor: "#9ca0ae", spikedash: "dot" },
      yaxis: { ...axis, domain: [0.26, 1], side: "right", range: [lo - pad, hi + pad] },
      yaxis2: { ...axis, domain: [0, 0.2], side: "right", showticklabels: false },
    };

    try {
      setFailure("");
      Promise.resolve(Plotly.react(el, [price, volume], layout, { displayModeBar: false, responsive: true }))
        .then(() => {
          el.removeAllListeners?.("plotly_hover");
          el.removeAllListeners?.("plotly_unhover");
          el.on?.("plotly_hover", (e) => onHover(e.points[0].pointIndex));
          el.on?.("plotly_unhover", () => onHover(null));
        })
        .catch((e) => setFailure(String(e?.message || e)));
    } catch (e) {
      setFailure(String(e?.message || e));
    }
  }, [rows, mode, onHover]);

  useEffect(() => {
    const el = ref.current;
    return () => el && Plotly.purge(el);
  }, []);

  return (
    <>
      {failure && <div className="notice notice-warn">The chart could not be drawn: {failure}</div>}
      <div ref={ref} className="plot" />
    </>
  );
}
