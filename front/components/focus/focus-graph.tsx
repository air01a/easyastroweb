// FwhmChart.tsx
import React, { useMemo } from "react";
import Plot from "react-plotly.js";
import type { Data, Layout } from "plotly.js";
import type { AutofocusResult, FwhmPoint, FwhmResults } from "../../types/api.type";



/**
 * L'API renvoie un tuple:
 * - [0] = liste de mesures
 * - [1] = {} avec best_position & stats quand terminé, ou [] pendant la prise de données
 */


interface FwhmChartProps {
  data: FwhmResults;
  title?: string;
  height?: number;
}

const FwhmChart: React.FC<FwhmChartProps> = ({ data, height = 420 }) => {
  // Normalisation du second élément (peut être [] ou un objet)
  const meta: AutofocusResult | null = useMemo(() => {
    const second = data[1];
    return second && second?.fwhm_max ?  (second as AutofocusResult): null;
  }, [data]);

  // Filtre des mesures valides
  const points: FwhmPoint[] = useMemo(
    () => data[0].filter((p) => p.valid),
    [data]
  );

  // Axes
  const x: number[] = useMemo(() => points.map((p) => p.focus_position), [points]);
  const y: number[] = useMemo(() => points.map((p) => p.fwhm), [points]);

  const xMin: number = useMemo(() => (x.length ? Math.min(...x) : 0), [x]);
  const xMax: number = useMemo(() => (x.length ? Math.max(...x) : 1), [x]);
  const yMin: number = useMemo(() => (y.length ? Math.min(...y) : 0), [y]);
  const yMax: number = useMemo(() => (y.length ? Math.max(...y) : 1), [y]);

  // Trace des points
  const scatter: Data = {
    type: "scatter",
    mode: "markers",
    x,
    y,
    name: "Mesures",
    hovertemplate:
      "Position: %{x}<br>FWHM: %{y:.2f}<extra></extra>",
    marker: { size: 8 },
  };

  /*const shapes: Layout["shapes"] = meta
  ? [
      {
        type: "line",
        x0: meta.best_position,
        x1: meta.best_position,
        y0: yMin,
        y1: yMax,
        line: { width: 2, dash: "dash", color: "red" },
      },
    ]
  : undefined;   // 👈 au lieu de []*/

 const layout: Partial<Layout> = {
  title: { text: "Autofocus" },
  height,
  margin: { l: 60, r: 20, t: 50, b: 50 },
  xaxis: {
    title: {text:"Focus position"},
    zeroline: false,
    range: [xMin - 100, xMax + 100],
  },
  yaxis: {
    title: {text:"FWHM"},
  },
  showlegend: false,

  // 👇 N'ajoute "shapes" que si meta existe
  ...(meta && {
    shapes: [
      {
        type: "line",
        x0: meta.best_position,
        x1: meta.best_position, // même x => ligne verticale (pas de diagonale)
        y0: yMin,
        y1: yMax,
        line: { width: 2, dash: "dash" },
      },
    ] as NonNullable<Layout["shapes"]>,
  }),
};
  const dataTraces: Data[] = [scatter];

  return (
    <Plot
      data={dataTraces}
      layout={layout}
      config={{ displayModeBar: true, responsive: true }}
      style={{ width: "100%", height }}
    />
  );
};

export default FwhmChart; 