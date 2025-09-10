import { useEffect, useState } from "react";
import  SkyMap,  { type Star, type Constellation, type ConstellationLine, type DSO} from "../../components/map/skymap"
import  {SkyMapFilters } from "../../components/map/skymap-filter"
import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import { useObserverStore, useCatalogStore } from "../../store/store";
import {getCoordinatesForDynamicObject} from "../../lib/astro/catalog/catalog";

export default function Celestial() {
    const {observatory, sunSet }= useObserverStore();
    const { catalog } = useCatalogStore()

    const [filters, setFilters] = useState({
      showConstellations: true,
      showStarNames: true,
      showDeepSky: true,
      minMagnitude: 4,
      dateTime: sunSet, // "YYYY-MM-DDTHH:MM"
    });

  const [stars, setStars] = useState<Star[] | null>(null);
  const [constellations, setConstellations] = useState<Constellation[] | null>(null);
  const [lines, setLines] = useState<ConstellationLine[] | null>(null);
  const [dso, setDso] = useState<DSO[]|null>(null);

  useEffect(() => {
    (async () => {
      const [starsRes, constRes, lineRes] = await Promise.all([
        fetch("/skymap/stars.json"),
        fetch("/skymap//constellations.json"),
        fetch("/skymap/constellationlines.json"),
        fetch("/skymap/planets.json"),
      ])
      const starsJson = (await starsRes.json()) as Star[];
      const constellationsJson = (await constRes.json()) as Constellation[];
      const linesJson = (await lineRes.json()) as ConstellationLine[];
      const dso: DSO[] = catalog.map((item: CatalogItem) => ({
        name: item.name,
        category: item.objectType,
        pos : !item.dynamic?{ra: item.ra, dec: item.dec}:getCoordinatesForDynamicObject(item.name, filters.dateTime, observatory.latitude as number, observatory.longitude as number)||{ra: item.ra, dec: item.dec},
        radius:item.dynamic?4:1,
        color:item.dynamic?"#db1d1dff":"rgba(216, 216, 19, 0.8)"
      }));

      setDso(dso);
      setStars(starsJson);
      setConstellations(constellationsJson);
      setLines(linesJson);
    })();
  },[filters.dateTime ]);

  const vw = typeof window !== "undefined" ? window.innerWidth : 800;
  const vh = typeof window !== "undefined" ? window.innerHeight : 600;
  const size = Math.min(vw, vh)*0.9;

  return (<div className="flex flex-wrap items-center justify-center">
      <div>
      <SkyMap
          width={size}
          height={size}
          lonDeg={observatory.longitude as number}    
          latDeg={observatory.latitude as number}   
          starsCatalog={stars||[]}
          linesCatalog={lines||[]}
          constellationsCatalog={constellations||[]}
          backgroundImageUrl="/skymap/horizon.png"
          minMagnitude={filters.minMagnitude}
          date={filters.dateTime}
          showConstellations={filters.showConstellations}
          showDSO={filters.showDeepSky}
          showStarsName={filters.showStarNames}
          dsoCatalog={dso||[]}
        />
      </div>
      <div className="w-80"> {/* largeur fixe pour les filtres */}
        <SkyMapFilters {...filters} onChange={setFilters} />
      </div>

      </div>
  );
}
