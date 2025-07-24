import type { CatalogItem } from "../lib/astro/catalog/catalog.type"
import type {Field} from '../types/dynamicform.type'
import type { ConfigItem, ConfigItems } from "./config.type"
export type CatalogStore = {
  catalog: CatalogItem[]
  isLoaded: boolean
  error: string | null
  setSelected: (index: number, selected: boolean) => void
  updateCatalog: (catalog: CatalogItem[]) => void
}


export type ObserverStore = {
  date: Date
  sunSet: Date
  sunRise: Date
  isLoaded: boolean
  telescope: ConfigItems;
  observatory : ConfigItems;
  camera: ConfigItems;
  filterWheel : ConfigItems;
  setFilterWheel : (filterWheel : ConfigItems)=> void;
  setCamera : (camera : ConfigItems)=> void;
  initializeObserver: (telescope: ConfigItems, observatory: ConfigItems, date: Date, sunSet: Date, sunRise: Date) =>void,


  resetObserver: () => void
  
}


export type WebSocketState = {
  socket: WebSocket | null;
  isConnected: boolean;
  messages: Record<string,string|number|number[]>[];
  connect: () => void;
  sendMessage: (msg: string) => void;
};


export type ConfigStore = {
  config: Record<string, ConfigItem>
  configScheme : Field[]
  setConfig: (config:Record<string,ConfigItem>) => void,
  setConfigScheme: (configScheme:Field[]) => void,

  getItem:(name:string) => ConfigItem | undefined
  
}
