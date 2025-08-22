'use client';

import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import { CirclePlus, CircleMinus } from 'lucide-react'; // ou une autre lib d’icônes
import { useTranslation } from 'react-i18next';

const statusColors: Record<CatalogItem['status'], string> = {
  'visible': 'border-green-500 ',
  'non-visible': 'border-red-500 ',
  'partially-visible': 'border-yellow-500 ',
  'masked': 'border-yellow-500 ',
};

export default function AstronomyObjectList({
  objects, onToggle, onClick, 
}: {
  objects: CatalogItem[];
  onToggle: (index: number) => void;
  onClick: (index: number) => void;
}) {
  const { t } = useTranslation();

  return (
    <div className="flex flex-wrap gap-4 items-center justify-center">
      {objects.map((obj, index) => (
        <div
          key={index}
          className={`relative flex-grow min-w-[300px] max-w-sm border-4 rounded-lg p-2  ${obj.isSelected?"bg-gray-700 border-red-100":statusColors[obj.status]}`}
          onClick={() => onClick(index)}
        >
          {/* Status centered on top */}
          <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-black px-3 py-1 rounded-full shadow text-sm font-semibold border">
            {t(`catalog.${obj.status.replace('-', ' ')}`)}
          </div>

          <div className="flex flex-row md:flex-row items-center gap-2">
            <button
              onClick={(e:React.MouseEvent<HTMLButtonElement>) => { e.stopPropagation(); onToggle(obj.index); }}
              className="absolute top-2 z-150 right-2 text-yellow-400"
              aria-label="Sélectionner"
            >
            {obj.isSelected ? <CircleMinus className="text-red-500" /> : <CirclePlus />}
          </button>
            <img
              src={`/catalog/${obj.image}`}
              alt={obj.name}
              width={120}
              height={120}
              className="rounded-full shadow"
            />
            <div className="flex-1 mt-4">

              <h2 className="text-xl font-bold">{obj.name}</h2>
              <p className="text-sm text-gray-600">{t(`catalog.${obj.objectType}`)}</p>
              <p className="text-sm">{t('catalog.magnitude')} : {obj.magnitude}</p>
              { obj.illumination && <p className="text-sm">{t('catalog.illumination')} : {obj.illumination}%</p> }
              <p className="text-sm">
                {obj.sunrise
                  ? `${t('catalog.riseSet')} : ${obj.sunrise.toLocaleString().split(' ')[1]} / ${obj.sunset?.toLocaleString().split(' ')[1]}`
                  : 'Circumpolaire'}
              </p>
              <p className="text-sm">{t('global.meridian')}  : {obj.meridian?.toLocaleString().split(' ')[1]}  </p>
              
              <p className="text-sm">{t('global.azimuth')}  : {obj.azimuth?.toFixed(0)}°</p>
              <p className="text-sm">{t('global.altitude')}  :{obj.altitude?.toFixed(0)}°</p>
              <p className="text-sm">{t('catalog.visibleHour')}  : {obj.nbHoursVisible} h</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
