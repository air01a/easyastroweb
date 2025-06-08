'use client';

import { Range } from 'react-range';
import { useState } from 'react';

export default function DoubleSlider({
  min = 0,
  max = 360,
  step = 1,
  initial = [60, 120],
  unit = '°',
  label = 'Plage'
}: {
  min?: number;
  max?: number;
  step?: number;
  initial?: [number, number];
  unit?: string;
  label?: string;
}) {
const [values, setValues] = useState<number[]>(initial);

  return (
    <div className="w-full">
      <div className="text-center mb-2 text-sm font-medium text-gray-700">
        {label} : <span className="font-bold">{values[0]}{unit} – {values[1]}{unit}</span>
      </div>

      <Range
        values={values}
        step={step}
        min={min}
        max={max}
        onChange={setValues}
        renderTrack={({ props, children }) => (
          <div
            {...props}
            className="h-2 bg-gray-200 rounded-lg w-full"
          >
            <div className="h-full bg-blue-500 rounded-lg" style={{
              marginLeft: `${((values[0] - min) / (max - min)) * 100}%`,
              width: `${((values[1] - values[0]) / (max - min)) * 100}%`,
            }} />
            {children}
          </div>
        )}
        renderThumb={({ props }) => (
          <div
            {...props}
            className="w-5 h-5 bg-white border border-blue-500 rounded-lg shadow cursor-pointer"
          />
        )}
      />
    </div>
  );
}
