'use client';

import { useEffect, useState } from 'react';
import { setLocation } from '@/actions/location/location'; 
import { getConfig } from '@/actions/config/config';


export default function GpsCapture() {

  const [coords, setCoords] = useState<null | { lat: number; lon: number }>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {


    function getLocation() {

    
        if (!navigator.geolocation) {
            setError('La géolocalisation n’est pas supportée par ce navigateur.');
            return;
        }

        navigator.geolocation.getCurrentPosition(
        (position) => {
            const { latitude, longitude } = position.coords;
            setCoords({ lat: latitude, lon: longitude });

            // Exemple : envoie à une server action (si besoin)
            setLocation(latitude, longitude)
            document.cookie = `observerLocation=${latitude},${longitude}; path=/;`;
        },
        (err) => {
            setError(`Erreur : ${err.code} - ${err.message || JSON.stringify(err)}`);
            const config = getConfig().then((config) => {
                // Si l'utilisateur a refusé la géolocalisation, on utilise les coordonnées par défaut
                const latitude = config.defaultLatitude || 0;
                const longitude = config.defaultLongitude || 0;
                setCoords({
                    lat: latitude,  lon: longitude
                });
                setLocation(latitude, longitude);
                document.cookie = `observerLocation=${latitude},${longitude}; path=/;`;

            })
        }
);
    }
    getLocation();
  }, []);

  return (
    <div>
      {coords && (
        <p>
          Latitude : {coords.lat}, Longitude : {coords.lon}
        </p>
      ) }
      
      {error ? (
        <p style={{ color: 'red' }}>{error}</p>
      ) : (
        <p>Obtention des coordonnées GPS…</p>
      )}
    </div>
  );
}
