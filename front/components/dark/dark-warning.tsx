import { useEffect, useState } from "react";
import {apiService} from '../../api/api';
import type {DarkLibraryType} from '../../types/api.type';
import {  useObserverStore } from "../../store/store";
import { useTranslation } from 'react-i18next';



export default function DarkInfoPanel() {
  const [darkItems, setDarkItems] = useState<DarkLibraryType[]>([]);
  const [loading, setLoading] = useState(true);
  const {camera} = useObserverStore();
  const { t } = useTranslation();

  useEffect(() => {
    const fetchDarks = async () => {
      try {
        const data = await apiService.getDarkForCamera(camera.id as string);
        setDarkItems(data);
      } catch (error) {
        console.error("Erreur lors du chargement des darks :", error);
      } finally {
        setLoading(false);
      }
    };

    fetchDarks();
  }, []);


  const hasMatchingTemperature = darkItems.some(
    (dark) => dark.temperature === camera.temperature
  );

  // Tri par exposition puis gain
  const sortedDarks = [...darkItems].sort((a, b) => {
    if (a.exposition !== b.exposition) {
      return a.exposition - b.exposition;
    }
    return a.gain - b.gain;
  });

  // Extraction des couples uniques exposition/gain triés
  const exposureGainPairs = Array.from(
    new Set(sortedDarks.map((d) => `${d.exposition}s / Gain ${d.gain}`))
  );

  return (
    <div className="bg-gray-800 rounded-xl p-4 shadow-md mt-4 max-w-xl mb-4">
      <h2 className="text-lg font-semibold mb-2">📦 {t('dark.library')}</h2>

      {loading ? (
        <p className="text-gray-100">{t('dark.loading')}</p>
      ) : (
        <>
          {camera.isCooled && !hasMatchingTemperature && (
            <div className="bg-yellow-100 border-l-4 border-yellow-500 text-gray-100 p-3 rounded mb-4">
              ⚠️ {t('dark.noTemp')}
              ({camera.temperature}°C).
            </div>
          )}

          {exposureGainPairs.length > 0 ? (
            <div>
              <p className="text-gray-100 mb-2">
                💡 {t('dark.couples')}
              </p>
              <ul className="list-disc list-inside text-sm text-gray-200">
                {exposureGainPairs.map((pair, index) => (
                  <li key={index}>{pair}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-gray-500 italic">
              {t('dark.noDark')}
            </p>
          )}
        </>
      )}
    </div>
  );
}
