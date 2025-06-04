import { CatalogItem } from '@/lib/astro/catalog/catalog.type'
import { create } from 'zustand'
import { CatalogStore, ObserverStore } from './store.type';
import { loadCatalogFromCSV } from '@/lib/astro/catalog/loadcatalog';
let hasLoaded = false

export const useCatalogStore = create<CatalogStore>((set) => ({
  catalog: [],
  isLoading: false,
  error: null,
  

  loadCatalog: async () => {
    try {
        if (hasLoaded) return
        hasLoaded = true
        set({ isLoading: true, error: null })      
        const data: CatalogItem[] = await loadCatalogFromCSV();
        set({ catalog: data, isLoading: false })
    } catch (err: any) {
      set({ error: err.message, isLoading: false })
    }
  },

  setSelected: (index: number, selected: boolean) => {
    set((state) => ({
      catalog: state.catalog.map((item) =>
        item.index === index ? { ...item, isSelected: selected } : item
      )
    }))
  },

  updateCatalog: (catalog: CatalogItem[]) => {
    console.log('updateCatalog', catalog);
    set({ catalog });
  }
}));

export const useObserverStore = create<ObserverStore>((set) => ({
  latitude: 0,
  longitude: 0,
  isLoaded: false,
  date: new Date(),

  setLatitude: (latitude: number) => {set({ latitude , isLoaded:true});},
  setLongitude: (longitude: number) => set({ longitude , isLoaded:true}),
  setDate: (date: Date) => set({ date }),
  
  resetObserver: () => set({ latitude: 0, longitude: 0, date: new Date() })
}));