import { getAssetFileTxt } from '@/lib/fsutils';
import { CatalogItem, CatalogState } from './catalog.type';
import { Observer, MakeTime, Equator, Horizon, Body, AngleBetween  } from 'astronomy-engine';
import { getMoonCoordinates, angularSeparation, equCoordStringToDecimal, getHoursForObject } from '../astro-utils';


//let cachedCatalog: CatalogItem[] | null = null;
//let catalogIsComputed = false;
interface GlobalCatalog {
  cachedCatalog: CatalogItem[] | null;
  catalogIsComputed: boolean;
}

// Utiliser globalThis pour persister entre les reloads
const globalForCatalog = globalThis as unknown as {
  catalog: GlobalCatalog | undefined;
};

if (!globalForCatalog.catalog) {
  globalForCatalog.catalog = {
    cachedCatalog: null,
    catalogIsComputed: false
  };
}

const catalogStore = globalForCatalog.catalog;
export async function getCatalog(): Promise<CatalogItem[]> {
  if (catalogStore.cachedCatalog) {
    console.log("------------ Loading catalog from cache");

    return catalogStore.cachedCatalog;
  }
  catalogStore.catalogIsComputed = false;
  console.log('#############" Loading catalog from CSV file');
  const csvText = await getAssetFileTxt('catalog','catalog.csv');
  const lines = csvText.split('\n').filter((line) => line.trim() !== '');
  const headers = lines[0].split(';').map(h => h.trim());
  const catalog: CatalogItem[] = lines.slice(1).map((line) => {
    const values = line.split(';').map((v) => v.trim());
    const get = (key: string) => values[headers.indexOf(key)] ?? '';
    const ra = equCoordStringToDecimal(get('RA'));
    const dec = equCoordStringToDecimal(get('DEC'));

   
    return {
      dynamic: get('Type')==='1'?true:false, // ou autre logique si tu veux calculer ça
      name: get('Name'),
      ngc: get('NGC'),
      objectType: get('Object type'),
      season: get('Season'),
      magnitude: parseFloat(get('Magnitude')) || 0,
      constellationEN: get('Constellation (EN)'),
      constellationFR: get('Constellation (FR)'),
      constellationLatin: get('Constellation (Latin)'),
      ra: ra || 0,
      dec: dec || 0,
      distance: parseFloat(get('Distance')) || 0,
      size: parseFloat(get('Size')) || 0,
      image: get('Image'),
      imageCiel: get('Image ciel'),
      location: get('Location'),
      status: 'visible',
      isSelected: false
    };
  });

  catalogStore.cachedCatalog = catalog;
  return catalog;
}

export async function computeCatalog(date: Date, latitude: number, longitude:number): Promise<void> {
  catalogStore.catalogIsComputed = true;
  await reloadCatalog();
  console.log('#############" Compute catalog');

  const observer: Observer = new Observer(latitude, longitude, 0);
  const astroTime = MakeTime(date);
  const moonVector = getMoonCoordinates(observer, astroTime);

  catalogStore.cachedCatalog?.forEach((item => {
    if (item.dynamic) {
      const body = Body[item.name as keyof typeof Body];
      if (body) {
        const equ = Equator(Body[item.name as keyof typeof Body], astroTime, observer, true, true);
        item.ra = equ.ra;
        item.dec = equ.dec; 
      }

    }
    if (item.ra!== 0 || item.dec! == 0) {
      const horizontal = Horizon(astroTime, observer, item.ra, item.dec, 'normal');
      const hours = getHoursForObject(observer, astroTime, item.ra, item.dec);
      item.meridian = hours.meridian?.date;
      item.sunrise = hours.sunrise?.date;
      item.sunset = hours.sunset?.date;
      item.azimuth = horizontal.azimuth;
      item.altitude = horizontal.altitude;
      if (item.altitude<0) {
        item.status = 'non-visible';
      } else if (item.altitude<20) {
        item.status = 'partially-visible';
      } else {
        item.status = 'visible';
      }
      item.moonAngularDistance = angularSeparation(moonVector.ra, moonVector.dec, item.ra, item.dec);
    }
  }));
 // console.log(cachedCatalog);
}

export async function reloadCatalog(): Promise<void> {
  console.log('Reloading catalog from CSV file');
  catalogStore.cachedCatalog = null; // Invalidate cache
  await getCatalog(); // Load again
}

export async function filterCatalog(type:string, showInvisible:boolean, showMasked:boolean, showPartial:boolean): Promise<CatalogItem[]> {
  const catalog = await getCatalog();
  return catalog.filter((item) => {
    if (type && item.objectType !== type && type!=='all') return false;
    if (!showMasked && item.status === 'masked') return false;
    if (!showInvisible && item.status === 'non-visible') return false;
    if (!showPartial && item.status === 'partially-visible') return false;

    return true;
  });
}

