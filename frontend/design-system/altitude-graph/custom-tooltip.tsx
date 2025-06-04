import React from 'react';
import { TooltipProps } from 'recharts';

interface DataPoint {
  time: string;       // ISO date string
  altitude: number;
  azimuth: number;
  index: number;
}

const CustomTooltip: React.FC<TooltipProps<number, string>> = ({ active, payload, label }) => {
  if (active && payload && payload.length > 0) {
    const point = payload[0].payload as DataPoint;



    return (
      <div style={{ background: 'black', border: '1px solid #ccc', padding: '8px' }}>
        <strong>{`${point.time}`}</strong>
        <br />
        Altitude : {Math.round(point.altitude)}°
        <br />
        Azimuth : {Math.round(point.azimuth)}°
      </div>
    );
  }

  return null;
};

export default CustomTooltip;
