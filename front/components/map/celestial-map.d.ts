import { ComponentType } from 'react';

interface CelestialMapProps {
  width?: number;
  height?: number;
  config?: Record<string, string|number|Record<string,string|number|boolean>>;
}

declare const CelestialMap: ComponentType<CelestialMapProps>;
export default CelestialMap;