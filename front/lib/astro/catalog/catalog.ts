import type { CatalogItem } from './catalog.type';
import { Observer, MakeTime, Equator, Horizon, Body, MoonPhase  } from 'astronomy-engine';
import { equCoordStringToDecimal, getMoonCoordinates, angularSeparation,  getHoursForObject, toRadians } from '../astro-utils';




export async function computeCatalog(
  catalog: CatalogItem[],
  latitude: number,
  longitude: number,
  date: Date
  
): Promise<CatalogItem[]> {
  const observer: Observer = new Observer(latitude, longitude, 0);
  const astroTime = MakeTime(date);
  const moonVector = getMoonCoordinates(observer, astroTime);

  let descriptions=[]
  const descriptionFile = (await fetch('/catalog/objects.fr.json'));
  if (descriptionFile.ok) {
    descriptions = await descriptionFile.json();
    console.log('descriptions', descriptions);
  }
  const updatedCatalog = catalog.map((item) => {
    const newItem = { ...item }; // ← Cloner l'objet pour éviter la mutation

    if (newItem.dynamic) {
      const body = Body[newItem.name as keyof typeof Body];
      if (body) {
        const equ = Equator(body, astroTime, observer, true, true);
        newItem.ra = equ.ra;
        newItem.dec = equ.dec;
      }
      if (newItem.name === 'Moon') {
        // calculate moon phase and convert to int  
        const moonPhase = MoonPhase(astroTime);      
        const phase = Math.floor(moonPhase/360*24).toString();
        newItem.image = `moon${phase}.png`;
        newItem.illumination = Math.floor(0.5*(1-Math.cos(toRadians(moonPhase)))*100);
      }
    }

    if (newItem.ra !== 0 || newItem.dec !== 0) {
      const horizontal = Horizon(astroTime, observer, newItem.ra, newItem.dec, 'normal');
      const hours = getHoursForObject(observer, astroTime, newItem.ra, newItem.dec);
      newItem.meridian = hours.meridian?.date;
      newItem.sunrise = hours.sunrise?.date;
      newItem.sunset = hours.sunset?.date;
      newItem.azimuth = horizontal.azimuth;
      newItem.altitude = horizontal.altitude||-100;

      if (!newItem.altitude || newItem.altitude < 0) {
        newItem.status = 'non-visible';
      } else if (newItem?.altitude < 20) {
        newItem.status = 'partially-visible';
      } else {
        newItem.status = 'visible';
      }
      newItem.description = descriptions[newItem.name] || '';
      newItem.moonAngularDistance = angularSeparation(
        moonVector.ra,
        moonVector.dec,
        newItem.ra,
        newItem.dec
      );
      //newItem.description = t(`_${newItem.name}`);
    }

    return newItem;
  });

  return updatedCatalog;
}


export async function filterCatalog(catalog : CatalogItem[], type:string, keyword:string, showInvisible:boolean, showMasked:boolean, showPartial:boolean): Promise<CatalogItem[]> {
  return catalog.filter((item) => {
    if (keyword && !item.name.toLowerCase().includes(keyword.toLowerCase()) && !item.description?.toLowerCase().includes(keyword.toLowerCase())) return false;
    if (type && item.objectType !== type && type!=='all') return false;
    if (!showMasked && item.status === 'masked') return false;
    if (!showInvisible && item.status === 'non-visible') return false;
    if (!showPartial && item.status === 'partially-visible') return false;

    return true;
  });

}



export async function loadCatalogFromCSV(csvText:string): Promise<CatalogItem[]> {
    const lines = csvText.split('\n').filter((line) => line.trim() !== '');
    const headers = lines[0].split(';').map(h => h.trim());
    let index = 0;
    const catalog: CatalogItem[] = lines.slice(1).map((line) => {
        const values = line.split(';').map((v) => v.trim());
        const get = (key: string) => values[headers.indexOf(key)] ?? '';
        const ra = equCoordStringToDecimal(get('RA'));
        const dec = equCoordStringToDecimal(get('DEC'));

    
        return {
        index : index++,
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
    return catalog;
}