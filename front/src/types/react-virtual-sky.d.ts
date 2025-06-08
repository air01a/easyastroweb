// src/types/react-virtual-sky.d.ts

declare module 'react-virtual-sky' {
  import * as React from 'react';

  export interface SkyConfig {
    width?: number;
    height?: number;
    azOff?: number;
    lat?: number;
    lon?: number;
    latitude?: number;
    longitude?: number;
    time?: Date;
    skyColors?: [string, string];
    gridAzColor?: string;
    gridEqColor?: string;
    gridGalColor?: string;
    language?: string;
    visibility?: {
      starMag?: number;
      showStarLabels?: boolean;
      showPlanets?: boolean;
      showPlanetsOrbit?: boolean;
      showPlanetsLabels?: boolean;
      showSunMoon?: boolean;
      showConstellations?: boolean;
      showConstellationBoundaries?: boolean;
      showConstellationLabels?: boolean;
      showAzLabels?: boolean;
      showAzGrid?: boolean;
      showEqGrid?: boolean;
      showGalGrid?: boolean;
      showGalaxy?: boolean;
      showInfo?: boolean;
    };
  }

  export interface VirtualSkyProps {
    id?: string;
    config: SkyConfig;
    className?: string;
    style?: React.CSSProperties;
  }

  export default class VirtualSky extends React.PureComponent<VirtualSkyProps> {}
}
