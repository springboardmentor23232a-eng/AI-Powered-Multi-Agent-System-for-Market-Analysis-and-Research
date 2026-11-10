import Plotly from "plotly.js-basic-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { Data, Layout } from "plotly.js";

const Plot = createPlotlyComponent(Plotly);

export default function PlotlyChart({ data, layout, height = 280 }: { data: Data[]; layout?: Partial<Layout>; height?: number }) {
  return (
    <Plot
      data={data}
      layout={{
        autosize: true, height, margin: { l: 50, r: 20, t: 20, b: 40 }, legend: { orientation: "h", y: 1.12 },
        paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", xaxis: { gridcolor: "#e2e8f0" },
        yaxis: { gridcolor: "#e2e8f0" }, ...layout,
      }}
      config={{ displayModeBar: false, responsive: true }}
      useResizeHandler
      style={{ width: "100%" }}
    />
  );
}
