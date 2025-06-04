// components/AltitudeChart.tsx
import { AltitudeGraphType } from '@/lib/astro/astro-utils.type';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, ReferenceArea, ReferenceLine } from 'recharts';
import CustomTooltip from './custom-tooltip';


export default function AltitudeChart({data}:{data:AltitudeGraphType}) {
  const orderedData = data.map((d, index) => ({ ...d, index }));
  const selectedRange = orderedData.length > 0 ? [orderedData[5].index, orderedData[6].index] : null;
  const altitudes = orderedData.map(d => d.altitude);
  const minAltitude = Math.min(...altitudes);
  const maxAltitude = Math.max(...altitudes);
  const yDomain = [Math.floor(minAltitude - 5), Math.ceil(maxAltitude + 5)];

  return (
    <div style={{ width: '90vw', height: '400px' }}>
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={orderedData}>
            <XAxis
              dataKey="index"
              tickFormatter={(i) => {
                const d = orderedData[i];
                  if (!d) return '';
                console.log(d);
                
                return d.time;
              }}
            />
            <YAxis domain={yDomain} tickFormatter={(value) => Math.round(value).toString()} label={{ value: 'Altitude (°)', angle: -90, position: 'insideLeft' }} />
            <Line type="monotone" dataKey="altitude" stroke="#8884d8" />
            <Tooltip
                content={<CustomTooltip />}
                cursor={{ stroke: 'red', strokeWidth: 1 }}
                wrapperStyle={{ outline: 'none' }}
            />
            {selectedRange && (
                <ReferenceArea x1={selectedRange[0]} x2={selectedRange[1]} strokeOpacity={0.3} />
            )}
                <ReferenceLine y={0} stroke="red" strokeWidth={2} strokeDasharray="3 3" />
                <ReferenceLine y={20} stroke="orange" strokeWidth={2} strokeDasharray="3 3" />

                <ReferenceArea y1={yDomain[0]} y2={0} fill="red" fillOpacity={0.1} />
                <ReferenceArea y1={0} y2={20} fill="yellow" fillOpacity={0.1} />

            </LineChart>
        </ResponsiveContainer>
    </div>
  );
}
