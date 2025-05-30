export type CatalogItem = {
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
};

//TYPE;NAME;NGC;Object type;Season;Magnitude;Constellation (EN);Constellation (FR);Constellation (Latin);RA;DEC;Distance;Size;Image;Image ciel;Constellation;Location
export type CatalogState = {
  catalogue: CatalogItem[] | null;
  loading: boolean;
  error: string | null;
  loadCatalog: () => Promise<void>;
};