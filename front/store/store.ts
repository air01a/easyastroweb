import type { CatalogItem } from '../lib/astro/catalog/catalog.type'
import { persist, createJSONStorage  } from 'zustand/middleware'
import type {Field} from '../components/forms/dynamicform.type'
import { create } from 'zustand'
import type { CatalogStore, ObserverStore, WebSocketState, ConfigStore } from './store.type';
import type { ConfigItem } from './config.type';


export const useCatalogStore = create<CatalogStore>()(
  persist(
    (set) => ({
      catalog: [],
      isLoaded: false,
      error: null,

  
      setSelected: (index: number, selected: boolean) => {
        set((state) => ({
          catalog: state.catalog.map((item) =>
            item.index === index ? { ...item, isSelected: selected } : item
          )
        }))
      },

      updateCatalog: (catalog: CatalogItem[]) => {
        console.log('updateCatalog', catalog)
        set({ catalog })
        set({ isLoaded: true, error: null })
      }
    }),
    {
      name: 'catalog-storage', // clé dans localStorage
      partialize: (state) => ({
        catalog: state.catalog, // ne persiste que le tableau
      }),
    }
  )
)


export const useObserverStore = create<ObserverStore>()(
  persist(
    (set) => ({
      latitude: 0,
      longitude: 0,
      isLoaded: false,
      date: new Date(),
      sunSet: new Date(),
      sunRise: new Date(),

      initializeObserver: (latitude: number, longitude: number, date: Date, sunSet: Date, sunRise: Date) =>
        set({
          latitude,
          longitude,
          date,
          sunSet,
          sunRise,
          isLoaded: true,
        }),

      resetObserver: () =>
        set({ latitude: 0, longitude: 0, date: new Date(), isLoaded: false }),
    }),
    {
      name: 'observer-storage',
      partialize: (state) => ({
        latitude: state.latitude,
        longitude: state.longitude,
        date: state.date,
        isLoaded: state.isLoaded,
        sunRise: state.sunRise,
        sunSet: state.sunSet,
      }),
      // Gestion de la sérialisation/désérialisation des dates
      storage: {
        getItem: (name) => {
          const item = localStorage.getItem(name)
          if (!item) return null
          
          const parsed = JSON.parse(item)
          return {
            ...parsed,
            state: {
              ...parsed.state,
              date: new Date(parsed.state.date),
              sunRise: new Date(parsed.state.sunRise),
              sunSet: new Date(parsed.state.sunSet),
            }
          }
        },
        setItem: (name, value) => {
          const serialized = JSON.stringify({
            ...value,
            state: {
              ...value.state,
              date: value.state.date.toISOString(),
              sunRise: value.state.sunRise.toISOString(),
              sunSet: value.state.sunSet.toISOString(),
            }
          })
          localStorage.setItem(name, serialized)
        },
        removeItem: (name) => localStorage.removeItem(name),
      },
    }
  )
)


export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  
  socket: null,
  messages: [],
  isConnected: false,

  connect: () => {
    const socket = new WebSocket('ws://127.0.0.1:8000/ws/observation');

    socket.onopen = () => {
      set({isConnected: true})
      console.log('WebSocket connecté');
    };

    socket.onmessage = (event) => {
      const data = event.data;//JSON.parse(event.data);
      set((state) => ({ messages: [...state.messages, data] }));
    };

    socket.onerror = (err) => {
      console.error('WebSocket erreur', err);
    };

    socket.onclose = () => {
      console.log('WebSocket fermé');
      set({ socket: null, isConnected: false });
    };

    set({ socket });
  },

  sendMessage: (msg: string) => {
    const socket = get().socket;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(`${msg}\n`);
    } else {
      console.warn('Socket non connectée');
    }
  },
}));


//Record<string, any>


export const useConfigStore = create<ConfigStore>()(
  persist(

    (set, get) => ({
      config: {},
      configScheme: [],
      azimuthSelection: new Array(36).fill(true),
     // defaultConfig: {}
  
      setConfig: (newConfig : Record<string,ConfigItem>) => {
        set({config:newConfig})
      },

      setConfigScheme: (configScheme : Field[]) => {

        set({configScheme})
      },

      setAzimuth: (azimuth: boolean[]) => {
        set ({azimuthSelection: azimuth});
      },

      getAzimuth:() => {
        return get().azimuthSelection;
      },


    getItem: (name:string) => {
      if (name in get().config) {
        return get().config[name];
      }
  
      // Sinon, on cherche le field correspondant dans configScheme
      const field = get().configScheme.find(f => f.fieldName === name);
    
      // Si on trouve le field, on retourne sa defaultValue
      if (field) {
        return field.defaultValue;
      }

    }
  })
 , {
      name: 'config-session-storage',
      storage: createJSONStorage(() => sessionStorage), // utilise sessionStorage
    })
)
