'use client';

import Image from 'next/image';
import { CatalogItem } from '@/lib/astro/catalog/catalog.type';

const statusColors: Record<CatalogItem['status'], string> = {
  visible: 'border-green-500 ',
  'non-visible': 'border-red-500 ',
  'partially-visible': 'border-yellow-500 ',
  'masked': 'border-yellow-500 ',
};

export default function AstronomyObjectList({
  objects,
}: {
  objects: CatalogItem[];
}) {
  return (
    <div className="flex flex-wrap gap-4 items-center justify-center">
      {objects.map((obj, index) => (
        <div
          key={index}
          className={`relative w-1/3 min-w-150 border-4 rounded-lg p-2 ${statusColors[obj.status]}`}
        >
          {/* Status centered on top */}
          <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-black px-3 py-1 rounded-full shadow text-sm font-semibold border">
            {obj.status.replace('-', ' ')}
          </div>

          <div className="flex flex-row md:flex-row items-center gap-2">
            <Image
              src={`/api/image/${obj.image}`}
              alt={obj.name}
              width={120}
              height={120}
              className="rounded-full shadow"
            />
            <div className="flex-1">
              <h2 className="text-xl font-bold">{obj.name}</h2>
              <p className="text-sm text-gray-600">{obj.objectType}</p>
              <p className="text-sm">Magnitude : {obj.magnitude}</p>
              <p className="text-sm">Lever/Coucher : {obj.sunrise?.toLocaleString().split(' ')[1]} / {obj.sunset?.toLocaleString().split(' ')[1]} </p>
              <p className="text-sm">Méridien : {obj.meridian?.toLocaleString().split(' ')[1]}  </p>
              
              <p className="text-sm">Azimuth : {obj.azimuth?.toFixed(0)}°</p>
              <p className="text-sm">Altitude :{obj.altitude?.toFixed(0)}°</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
