import { getAssetFileTxt } from '@/lib/fsutils';
import { CatalogItem, CatalogState } from '@/stores/catalog.type';
import { create } from 'zustand';

export async function loadCatalogFromCSV(): Promise<CatalogItem[]> {
  const csvText = await getAssetFileTxt('catalog','catalog.csv');

  const lines = csvText.split('\n').filter((line) => line.trim() !== '');
  const headers = lines[0].split(';').map(h => h.trim());

  const catalog: CatalogItem[] = lines.slice(1).map((line) => {
    const values = line.split(';').map((v) => v.trim());

    const get = (key: string) => values[headers.indexOf(key)] ?? '';

    return {
      dynamic: get('type')==='0'?true:false, // ou autre logique si tu veux calculer ça
      name: get('NAME'),
      ngc: get('NGC'),
      objectType: get('Object type'),
      season: get('Season'),
      magnitude: parseFloat(get('Magnitude')) || 0,
      constellationEN: get('Constellation (EN)'),
      constellationFR: get('Constellation (FR)'),
      constellationLatin: get('Constellation (Latin)'),
      ra: parseFloat(get('RA')) || 0,
      dec: parseFloat(get('DEC')) || 0,
      distance: parseFloat(get('Distance')) || 0,
      size: parseFloat(get('Size')) || 0,
      image: get('Image'),
      imageCiel: get('Image ciel'),
      location: get('Location'),
    };
  });

  return catalog;
}

export const useCatalogueStore = create<CatalogState>((set) => ({
  catalog: null,
  loading: false,
  error: null,
  loadCatalog: async () => {
    set({ loading: true, error: null });

    try {
      data = await loadCatalogFromCSV();
      set({ catalogue: data, loading: false });
    } catch (err: any) {
      set({ error: err.message || 'Erreur inconnue', loading: false });
    }
  }
}));