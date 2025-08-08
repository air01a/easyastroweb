// AltitudeChart.tsx
import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';
import type { Shape } from 'plotly.js';

import type { AltitudeGraphType } from "../../lib/astro/astro-utils.type"
import {AltitudeGraphStep} from '../../lib/astro/astro-utils';
export interface SelectedRange {
  start: number;
  end: number;
  color?: string;
}

interface AltitudeChartProps {
  data: AltitudeGraphType;
  selectedRanges?: SelectedRange[];
  sunset : number;
  sunrise : number; 
}

const AltitudeChart: React.FC<AltitudeChartProps> = ({ 
  data, 
  selectedRanges = [] , sunrise, sunset
}: AltitudeChartProps) => {
  const { x, y, minAltitude, maxAltitude, timeLabels } = useMemo(() => {
    const baseHour = data[0]?.time || 0;
    const orderedData = data.map((d, index) => ({ ...d, index:(index*AltitudeGraphStep+baseHour) }));
    const altitudes = orderedData.map((d) => d.altitude);
    const min = Math.min(...altitudes);
    const max = Math.max(...altitudes);
    const x = orderedData.map((d) => d.index);
    const y = orderedData.map((d) => d.altitude);
    const timeLabels = data.map((d) => `${Math.floor(d.time)} h ${Math.floor((d.time % 1) * 60).toString().padStart(2, '0')}`);

    return {
      x,
      y,
      minAltitude: Math.floor(min - 5),
      maxAltitude: Math.ceil(max + 5),
      timeLabels,
    };
  }, [data]);

  const [xRange, setXRange] = useState<[number, number]>([data[0]?.time, (data[0]?.time+data.length*AltitudeGraphStep - 1)]);

  // Génération des rectangles pour les selectedRanges
  const selectedRangeShapes = useMemo(() => {
    data.forEach((element) => console.log(element.visibility))
    data.forEach((element, index)=> {
      if (element.visibility && element.visibility=='masked') {
        if ((index*AltitudeGraphStep+data[0]?.time>sunset) && ((index*AltitudeGraphStep+data[0]?.time)<sunrise+24)) {
          let start = (index*AltitudeGraphStep+data[0]?.time);
          let shift=AltitudeGraphStep;
          if (start<sunset+AltitudeGraphStep) {
            shift+= start - sunset ;
            start=sunset;
          }
          start %= 24;
          let end = (start+shift)%24;
          if (end<15 && end>sunrise) end=sunrise;

          selectedRanges.push({
            start,
            end,
            color: "violet"
          });
        }
      }
    })



     return selectedRanges.map((range) => ({
      type: 'rect',
      x0: range.start<14?range.start+24:range.start,
      x1: range.end<14?range.end+24:range.end,
      y0: minAltitude,
      y1: maxAltitude,
      fillcolor: range.color || 'blue',
      opacity: 0.2,
      line: { width: 0 },
    }));
  }, [selectedRanges, minAltitude, maxAltitude]);

  return (
    <Plot
      data={[
        {
          x,
          y,
          type: 'scatter',
          mode: 'lines+markers',
          marker: { color: '#8884d8' },
          name: 'Altitude',
          customdata: data.map((d) => [d.azimuth]),
          hovertemplate:
            'Heure: %{x}<br>' +
            'Altitude: %{y}°<br>' +
            'Azimuth: %{customdata[0]}°<extra></extra>',
        },
      ]}
      onRelayout={(event: unknown) => {
        const layout = event as Record<string, number | string | boolean>;

        if (layout['xaxis.range[0]'] && layout['xaxis.range[1]']) {
          setXRange([data[0]?.time, (data[0]?.time+data.length*AltitudeGraphStep - 1)]);
        }
      }}
      layout={{
        autosize: true,
        paper_bgcolor: '#a4a4a8',
        plot_bgcolor: '#a4a4a8',
        dragmode: 'select',
        margin: { l: 60, r: 20, t: 20, b: 50 },
        xaxis: {
          tickvals: x,
          dtick: 2,
          rangeslider: { visible: false },
          showgrid: false,
          ticktext: timeLabels,
          title: { text: 'Temps' },
          range: xRange,
        },
        yaxis: {
          range: [minAltitude, maxAltitude],
          showgrid: false,
          title: { text: 'Altitude (°)' },
          fixedrange: true,
        },
        shapes: [
          // Lignes de référence
          {
            type: 'line',
            x0: x[0],
            x1: x[x.length - 1],
            y0: 0,
            y1: 0,
            line: { color: 'red', width: 2, dash: 'dot' },
          },
          {
            type: 'line',
            x0: x[0],
            x1: x[x.length - 1],
            y0: 20,
            y1: 20,
            line: { color: 'orange', width: 2, dash: 'dot' },
          },
          // Zones de couleur pour les altitudes
          {
            type: 'rect',
            xref: 'paper',
            x0: 0,
            x1: 1,
            y0: minAltitude,
            y1: 0,
            fillcolor: 'red',
            opacity: 0.1,
            line: { width: 0 },
          },
          {
            type: 'rect',
            xref: 'paper',
            x0: 0,
            x1: 1,
            y0: 0,
            y1: 20,
            fillcolor: 'yellow',
            opacity: 0.1,
            line: { width: 0 },
          },
          // Rectangles pour les selectedRanges
          ...selectedRangeShapes,
        ] as Partial<Shape>[],
        hovermode: 'closest',
      }}
      config={{
        responsive: true,
        displayModeBar: false,
        scrollZoom: false,
        displaylogo: false,
        staticPlot: false,
        modeBarButtonsToRemove: [
          'zoom2d',
          'zoomIn2d',
          'zoomOut2d',
          'autoScale2d',
          'resetScale2d',
          'pan2d',
          'select2d',
          'lasso2d',
        ],
      }}
      style={{ width: '100%', height: '100%' }}
    />
  );
};

export default AltitudeChart;