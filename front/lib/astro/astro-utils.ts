import { Observer, MakeTime, Equator, Horizon, Body, AstroTime, DefineStar, SearchAltitude,SearchHourAngle } from 'astronomy-engine';
import type { AltitudeGraphType, VisibilityStatus } from './astro-utils.type';


export const getMoonCoordinates = (observer : Observer, astroTime: AstroTime ): { ra: number; dec: number } => {

  const moon = Body.Moon;
  const equ = Equator(moon, astroTime, observer, true, true);
  return equ;
}


export function toRadians(deg: number): number {
  return deg * Math.PI / 180;
}


export function todeg(rad: number): number {
  return rad * Math.PI / 180;
}

export function angularSeparation(ra1: number, dec1: number, ra2: number, dec2: number): number {
  const ra1Rad = toRadians(ra1);
  const dec1Rad = toRadians(dec1);
  const ra2Rad = toRadians(ra2);
  const dec2Rad = toRadians(dec2);

  const cosTheta = Math.sin(dec1Rad) * Math.sin(dec2Rad) +
                   Math.cos(dec1Rad) * Math.cos(dec2Rad) * Math.cos(ra1Rad - ra2Rad);

  const thetaRad = Math.acos(Math.min(Math.max(cosTheta, -1), 1)); // Clamp to avoid NaN
  return todeg(thetaRad); // Convert back to degrees
}

export function equCoordStringToDecimal(equ: string): number|null {

    let factor=1;
    let decimal=0;
    let coord = equ.trim();

    if (coord.startsWith('+')) {
        coord = coord.slice(1); // Remove the positive sign for processing
    } else if (coord.startsWith('-')) {
        coord = coord.slice(1); // Remove the negative sign for processing
        factor = -1; // Set factor to -1 for negative DEC
    }

    if (coord.includes('.')) {
        // Handle decimal format
        const parts = coord.split('.');
        if (parts.length !== 2) {
            return null; 
        }
        decimal = (parseInt(parts[1]) / 3600) / 100;
        // Keep only the integer part for further processing
        coord = parts[0]; // Update coord to the integer part
    }

    const parts = coord.split(':').map(Number);
    if (parts.length !== 3) {
        return null;
    }
    return factor*(parts[0] + parts[1] / 60 + parts[2] / 3600 + decimal); // Convert to decimal degrees
}


export function getNextSunsetDate(lat: number, lon:number, civilDawn:boolean=false): AstroTime | null {
  const now = new Date();
  const altitude = civilDawn ? -6 : 0; // Use -6 for civil dawn, 0 for sunrise

  const observer = new Observer(lat, lon, 0); // Assuming altitude is 0 for horizon calculations
  const result = SearchAltitude(Body.Sun, observer, -1, now,1, altitude);
  return result;
}

export function getNextSunriseDate(lat: number, lon:number, civilDawn:boolean=false): AstroTime | null {
  const now = new Date();
  const altitude = civilDawn ? -6 : 0; // Use -6 for civil dawn, 0 for sunrise
  const observer = new Observer(lat, lon, 0); // Assuming altitude is 0 for horizon calculations
  const result = SearchAltitude(Body.Sun, observer, 1, now,1,altitude);
  return result;
}

export function getHoursForObject(observer: Observer, astroTime: AstroTime, ra: number, dec: number): { sunrise: AstroTime | null; sunset: AstroTime | null, meridian: AstroTime | null } {
  DefineStar(Body.Star1, ra, dec, 1000);
  const sunRise = SearchAltitude(Body.Star1, observer, 1, astroTime, 1,0);
  const sunSet = SearchAltitude(Body.Star1, observer, -1, astroTime, 1,0);
  const meridien = SearchHourAngle(Body.Star1, observer, 0, astroTime, 1);

  return { sunrise: sunRise, sunset: sunSet, meridian: meridien.time };
}

export function getAltitudeData(latitude: number, longitude: number, date: Date, dateEnd: Date, ra: number, dec: number, hoursBA: number): AltitudeGraphType {
  const observer = new Observer(latitude, longitude, 0); // Assuming altitude is 0 for horizon calculations
  const times: AltitudeGraphType = [];
  let day = date.toISOString().split('T')[0]; 
  const tmpDate = new Date(date.getTime()); // Create a copy of the date to avoid modifying the original
  tmpDate.setHours(date.getHours()-hoursBA);
  const startHour = tmpDate.getHours();;
  const diffInMs = Math.abs(dateEnd.getTime() - date.getTime());
  const endHour = Math.ceil(diffInMs / (1000 * 60 * 60));
  for (let hour = startHour; hour < (startHour + endHour+2*hoursBA); hour+=0.5) {
    if (hour == 24) {
      day = new Date(tmpDate.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0]; // Increment day
    }
    console.log(hour);

    try {
      const isoTime = `${day}T${(Math.floor(hour%24)).toString().padStart(2, '0')}:${Math.floor((hour-Math.floor(hour))*60).toString().padStart(2, '0')}:00Z`;
      const astroTime = MakeTime(new Date(isoTime));
      const horizontal = Horizon(astroTime, observer, ra, dec, 'normal');


      times.push({
        time: astroTime.date.getHours()+astroTime.date.getMinutes()/60,
        altitude: Math.round(horizontal.altitude),
        azimuth: Math.round(horizontal.azimuth),
        visibility:null
      });
  } catch (error) {
      console.error('Error calculating horizon for hour', hour, error);
      continue; // Skip this hour if there's an error
    }
  }
  console.log('Altitude data:', times);
  return times;

}

export function getInitialDate(latitude: number, longitude: number): Date {
 
    let date = new Date();
    const nextSunset = getNextSunsetDate( latitude||0,  longitude||0);
    if (nextSunset) {
       date = nextSunset.date;
    }
  return date;
}


function toCartesian(raHours: number, decDegrees: number, distanceAU: number): { x: number, y: number, z: number } {
  const raRad = (raHours / 24) * 2 * Math.PI
  const decRad = (decDegrees * Math.PI) / 180

  const r = distanceAU
  const x = r * Math.cos(decRad) * Math.cos(raRad)
  const y = r * Math.cos(decRad) * Math.sin(raRad)
  const z = r * Math.sin(decRad)

  return { x, y, z }
}

export function getPreciseMoonIllumination(date: Date, observer: Observer): number {

  const moonEqu = Equator(
    Body.Moon,
    date,
    observer,
    true,
    true  
  )

  const sunEqu = Equator(
    Body.Sun,
    date,
    observer,
    true,
    true
  )

  const moonVec = toCartesian(moonEqu.ra, moonEqu.dec, moonEqu.dist)
  const sunVec = toCartesian(sunEqu.ra, sunEqu.dec, sunEqu.dist)

  const dotProduct =
    moonVec.x * sunVec.x + moonVec.y * sunVec.y + moonVec.z * sunVec.z

  const moonMag = Math.sqrt(moonVec.x**2 + moonVec.y**2 + moonVec.z**2)
  const sunMag = Math.sqrt(sunVec.x**2 + sunVec.y**2 + sunVec.z**2)

  const cosAngle = dotProduct / (moonMag * sunMag)
  const phaseAngle = Math.acos(Math.min(Math.max(cosAngle, -1), 1)) // clamp to [-1, 1]

  const illumination = 0.5 * (1 - Math.cos(phaseAngle))
  return illumination * 100
}


export function isObjectVisible(altitude: number, azimuth: number): VisibilityStatus {
  if (altitude < 0) {
    return 'non-visible'; // Object is below the horizon
  } else if (altitude < 20) {
    return 'partially-visible'; // Object is low on the horizon
  } else if (azimuth >= 0 && azimuth <= 360) {
    return 'visible'; // Object is above the horizon and in view
  } else {
    return 'masked'; // Object is obscured or not in view
  }

}

export function dateToNumber(date: Date) {
  return date.getHours()+date.getMinutes()/60;
}