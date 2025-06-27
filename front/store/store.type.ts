import type { CatalogItem } from "../lib/astro/catalog/catalog.type"
import type {Field} from '../components/forms/dynamicform.type'
import type { ConfigItem } from "./config.type"
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


export type WebSocketState = {
  socket: WebSocket | null;
  isConnected: boolean;
  messages: string[];
  connect: () => void;
  sendMessage: (msg: string) => void;
};


export type ConfigStore = {
  config: Record<string, ConfigItem>
  configScheme : Field[]
  azimuthSelection: boolean[]
  setConfig: (config:Record<string,ConfigItem>) => void,
  setConfigScheme: (configScheme:Field[]) => void,
  setAzimuth: (azimuth: boolean[]) =>void,
  getAzimuth: () =>boolean[],
  getItem:(name:string) => ConfigItem | undefined
  
}
