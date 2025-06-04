import { CatalogItem } from './catalog.type';
import { Observer, MakeTime, Equator, Horizon, Body  } from 'astronomy-engine';
import { getMoonCoordinates, angularSeparation,  getHoursForObject } from '../astro-utils';



export async function computeCatalog(
  catalog: CatalogItem[],
  latitude: number,
  longitude: number,
  date: Date
): Promise<CatalogItem[]> {
  const observer: Observer = new Observer(latitude, longitude, 0);
  const astroTime = MakeTime(date);
  const moonVector = getMoonCoordinates(observer, astroTime);

  const updatedCatalog = catalog.map((item) => {
    const newItem = { ...item }; // ← Cloner l'objet pour éviter la mutation

    if (newItem.dynamic) {
      const body = Body[newItem.name as keyof typeof Body];
      if (body) {
        const equ = Equator(body, astroTime, observer, true, true);
        newItem.ra = equ.ra;
        newItem.dec = equ.dec;
      }
    }

    if (newItem.ra !== 0 || newItem.dec !== 0) {
      const horizontal = Horizon(astroTime, observer, newItem.ra, newItem.dec, 'normal');
      const hours = getHoursForObject(observer, astroTime, newItem.ra, newItem.dec);
      newItem.meridian = hours.meridian?.date;
      newItem.sunrise = hours.sunrise?.date;
      newItem.sunset = hours.sunset?.date;
      newItem.azimuth = horizontal.azimuth;
      newItem.altitude = horizontal.altitude;

      if (newItem.altitude < 0) {
        newItem.status = 'non-visible';
      } else if (newItem.altitude < 20) {
        newItem.status = 'partially-visible';
      } else {
        newItem.status = 'visible';
      }

      newItem.moonAngularDistance = angularSeparation(
        moonVector.ra,
        moonVector.dec,
        newItem.ra,
        newItem.dec
      );
    }

    return newItem;
  });

  return updatedCatalog;
}


export async function filterCatalog(catalog : CatalogItem[], type:string, showInvisible:boolean, showMasked:boolean, showPartial:boolean): Promise<CatalogItem[]> {
  return catalog.filter((item) => {
    if (type && item.objectType !== type && type!=='all') return false;
    if (!showMasked && item.status === 'masked') return false;
    if (!showInvisible && item.status === 'non-visible') return false;
    if (!showPartial && item.status === 'partially-visible') return false;

    return true;
  });

}


