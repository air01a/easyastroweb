import { AstroTime } from "astronomy-engine";

export type CatalogItem = {
    index : number;
    dynamic: boolean;
    name : string;
    ngc: string;
    objectType: string;
    season: string;
    magnitude: number;
    constellationEN: string;
    constellationFR: string;
    constellationLatin: string;
    ra: number;
    dec: number;
    distance: number;
    size: number;
    image: string;
    imageCiel: string;
    location: string;
    azimuth?:number;
    altitude?:number;
    zenith?:number;
    sunrise?: Date|null;
    sunset?: Date|null;
    meridian?: Date|null;
    moonAngularDistance?: number;
    status: 'visible' | 'non-visible' | 'partially-visible' | 'masked';
    isSelected?: boolean;
};

//TYPE;NAME;NGC;Object type;Season;Magnitude;Constellation (EN);Constellation (FR);Constellation (Latin);RA;DEC;Distance;Size;Image;Image ciel;Constellation;Location
export type CatalogState = {
  catalog: CatalogItem[] | null;
  loading: boolean;
  error: string | null;
  loadCatalog: () => Promise<void>;
};