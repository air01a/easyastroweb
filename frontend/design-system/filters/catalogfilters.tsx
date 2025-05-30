import { useState } from 'react';

export default function CatalogFilters({ filters, setFilters }: {
  filters: { invisible: boolean; hidden: boolean; partial: boolean },
  setFilters: (f: typeof filters) => void
}) {
  function toggle(key: keyof typeof filters) {
    setFilters({ ...filters, [key]: !filters[key] });
  }

  return (
    <div className="flex flex-wrap gap-2 p-2 items-center justify-center mb-2">
      <button
        onClick={() => toggle('invisible')}
        className={`px-3 py-1 rounded-full text-sm font-medium border transition ${
          filters.invisible ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border-gray-300'
        }`}
      >
        Objets invisibles
      </button>
      <button
        onClick={() => toggle('hidden')}
        className={`px-3 py-1 rounded-full text-sm font-medium border transition ${
          filters.hidden ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border-gray-300'
        }`}
      >
        Objets masqués
      </button>
      <button
        onClick={() => toggle('partial')}
        className={`px-3 py-1 rounded-full text-sm font-medium border transition ${
          filters.partial ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border-gray-300'
        }`}
      >
        Partiellement visibles
      </button>
    </div>
  );
}
