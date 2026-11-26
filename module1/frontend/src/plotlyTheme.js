// Shared Plotly colours for light / dark. Usage:  const t = plotlyTheme(theme);  layout = { font: t.font, paper_bgcolor: t.paper_bgcolor, ... }
export function plotlyTheme(theme) {
  const dark = theme === "dark";
  return {
    font: { size: 12, color: dark ? "#cbd5e1" : "#334155" },
    gridcolor: dark ? "#26344f" : "#e2e8f0",
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    up: dark ? "#4ade80" : "#15803d",     // rising candles / positive
    down: dark ? "#f87171" : "#b91c1c",   // falling candles / negative
    line: dark ? "#93b4ff" : "#244bbd",   // main line series
    accent: dark ? "#fbbf24" : "#b45309", // secondary series
    muted: dark ? "#64748b" : "#94a3b8",  // volume bars, minor series
  };
}
