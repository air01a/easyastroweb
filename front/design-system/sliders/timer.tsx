'use client';

import { useState } from 'react';

export default function RangeSlider({
  min = 0,
  max = 360,
  step = 1,
  initial = 180,
  label = 'Valeur',
  unit = '°',
}: {
  min?: number;
  max?: number;
  step?: number;
  initial?: number;
  label?: string;
  unit?: string;
}) {
  const [value, setValue] = useState(initial);

  return (
    <div className="w-full max-w-md mx-auto p-4">
      <label className="block mb-2 text-center text-sm font-medium text-gray-700">
        {label}: <span className="font-bold">{value}{unit}</span>
      </label>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => setValue(Number(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
      />
    </div>
  );
}
