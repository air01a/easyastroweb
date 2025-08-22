import { useObserverStore } from "../../store/store";
import AltitudeChart from "../../design-system/altitude-graph/altitude-graph";
import type { CatalogItem } from "../../lib/astro/catalog/catalog.type";
import { dateToNumber, raToHour, decToAngle } from "../../lib/astro/astro-utils";
import { useTranslation } from 'react-i18next';
export default function ObjectDetails({ item }: { item: CatalogItem }) {
  const { sunRise, sunSet } = useObserverStore();
  const { t } = useTranslation();

  const selectedRanges = [
    { start: 15, end: dateToNumber(sunSet), color: "blue" },
    { start: dateToNumber(sunRise), end: 100, color: "blue" },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto p-4 space-y-6 text-white">
      <h2 className="text-3xl font-bold text-center">{item.name}</h2>

      <div className="flex flex-col md:flex-row gap-6 items-center justify-center">
        <img
          src={`/catalog/${item.image}`}
          alt={item.name}
          width={300}
          height={300}
          className="rounded-full shadow-lg border-4 border-gray-700"
        />
        <div className="flex-1 space-y-2 text-sm bg-gray-800 p-4 rounded-lg shadow">
          <p><span className="font-semibold">{t('global.name')} :</span> {item.name}</p>
          <p><span className="font-semibold">{t('details.ra')} :</span> {raToHour(item.ra)}</p>
          <p><span className="font-semibold">{t('details.dec')} :</span> {decToAngle(item.dec)}</p>
          <p><span className="font-semibold">{t('details.size')} :</span> {item.size}</p>
          <p><span className="font-semibold">{t('details.visibleHours')} :</span> {item.nbHoursVisible}</p>
          <p><span className="font-semibold">{t('details.angularDistance')} :</span> {Math.floor(item.moonAngularDistance||0)}</p>
        </div>
      </div>

      <div className="bg-gray-900 p-4 rounded-lg shadow space-y-2">
        <h3 className="text-xl font-semibold mb-2">{t('details.description')}</h3>
        <p className="text-gray-300">{item.description}</p>
      </div>

      <div className="bg-gray-900 p-4 rounded-lg shadow space-y-2">
        <h3 className="text-xl font-semibold mb-2">{t('details.skyAltitude')}</h3>
        <AltitudeChart
          data={item.altitudeData || []}
          selectedRanges={selectedRanges}
          sunrise={dateToNumber(sunRise)}
          sunset={dateToNumber(sunSet)}
        />
      </div>

      {!item.dynamic && (
        <div className="bg-gray-900 mt-4 p-4 rounded-lg shadow space-y-2">
          <h3 className="text-xl font-semibold">{t('details.position')}</h3>
          <img
            src={`/catalog/location/${item.name}.jpg`}
            alt={`Localisation de ${item.name}`}
            className="rounded-lg max-w-full mx-auto"
          />
        </div>
      )}
    </div>
  );
}
