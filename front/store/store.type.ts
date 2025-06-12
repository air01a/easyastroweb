import type { CatalogItem } from "../lib/astro/catalog/catalog.type"

export type CatalogStore = {
  catalog: CatalogItem[]
  isLoaded: boolean
  error: string | null
  setSelected: (index: number, selected: boolean) => void
  updateCatalog: (catalog: CatalogItem[]) => void
}


export type ObserverStore = {
  latitude: number
  longitude: number
  date: Date
  sunSet: Date
  sunRise: Date
  isLoaded: boolean

  initializeObserver: (latitude: number, longitude: number, date: Date, sunSet: Date, sunRise: Date) =>void,


  resetObserver: () => void
  
}