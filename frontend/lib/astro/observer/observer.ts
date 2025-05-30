import { ObserverLocation } from './observer.type';
import { computeCatalog, getCatalog, reloadCatalog } from '../catalog/catalog';
import { getNextSunsetDate } from '../astro-utils';


let observerLocation: ObserverLocation | null = null;
let observerDate: Date | null = null;

export function setObserverLocation(lat: number, lon: number) {
  observerLocation = { latitude: lat, longitude: lon };
  computeCatalog(getDate(), lat, lon);
}

export function getObserverLocation(): ObserverLocation | null {
  return observerLocation;
}


export function setDate(d: Date) {
  observerDate = d;
  computeCatalog(d, observerLocation?.latitude || 0, observerLocation?.longitude || 0);
}

export function getDate(): Date  {
  if (!observerDate) {
    observerDate = new Date();
    const nextSunset = getNextSunsetDate(observerLocation?.latitude||0, observerLocation?.longitude||0);
    if (nextSunset) {
      observerDate = nextSunset.date;
    }
  }
  return observerDate;
}