import { CatalogItem } from "@/lib/astro/catalog/catalog.type"

export type CatalogStore = {
  catalog: CatalogItem[]
  isLoading: boolean
  error: string | null
  loadCatalog: () => Promise<void>
  setSelected: (index: number, selected: boolean) => void
  updateCatalog: (catalog: CatalogItem[]) => void
}


export type ObserverStore = {
  latitude: number
  longitude: number
  date: Date
  isLoaded: boolean
  setLatitude: (latitude: number) => void
  setLongitude: (longitude: number) => void
  setDate: (date: Date) => void
  resetObserver: () => void
}