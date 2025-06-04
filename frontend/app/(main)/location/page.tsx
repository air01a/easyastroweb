'use client';

import { use, useEffect, useState } from 'react';
import { getConfig } from '@/actions/config/config';
import { useObserverStore } from "@/store/store";
import { getInitialDate } from '@/lib/astro/astro-utils';
import { useCatalogStore } from "@/store/store";
import { computeCatalog } from '@/actions/catalog/catalog';

export default function GpsCapture() {

  const [coords, setCoords] = useState<null | { lat: number; lon: number }>(null);
  const [error, setError] = useState<string | null>(null);
  const setLatitude = useObserverStore((s) => s.setLatitude)
  const setLongitude = useObserverStore((s) => s.setLongitude)
  const setDate = useObserverStore((s) => s.setDate)
  const { catalog, updateCatalog, isLoading  } = useCatalogStore()

  const updateStore = async (latitude : number, longitude: number) => {
      setLatitude(latitude);
      setLongitude(longitude);
      const date = getInitialDate(latitude, longitude);
      setDate(date);
      console.log('updateStore', latitude, longitude, date);
      const cat = await computeCatalog(catalog, latitude, longitude, date);
      updateCatalog([...cat]);
      document.cookie = `observerLocation=${latitude},${longitude}; path=/;`;
  }


    useEffect(() => {
      async function getLocation() {
        if (!navigator.geolocation) {
            setError('La géolocalisation n’est pas supportée par ce navigateur.');
            return;
        }

        navigator.geolocation.getCurrentPosition(
        async (position) => {
            const { latitude, longitude } = position.coords;
            setCoords({ lat: latitude, lon: longitude });
            // Exemple : envoie à une server action (si besoin)
            updateStore(latitude, longitude);


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
                  updateStore(latitude, longitude);
              })
          }
      );
      }
      if (catalog.length>1) getLocation();
    }, [isLoading]);

  return (
    <div>
      {isLoading && <p>Chargement des données…</p>}
      {!isLoading && coords && (
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
