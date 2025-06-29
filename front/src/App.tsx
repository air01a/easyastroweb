
//import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./home/home";
import  Layout  from "./Layout";
import { useCatalogStore, useObserverStore, useConfigStore } from "../store/store"
import {loadCatalog} from "../lib/astro/catalog/catalog";
import {  useEffect } from "react";
import CatalogPage from "./catalog/catalog";
import { getNextSunriseDate, getNextSunsetDate } from "../lib/astro/astro-utils";
import PlanPage from "./plan/plan";
import Configurator from './config/config';
import ObservatoryConfig from "./config/observatory";
import TelescopeConfig from "./config/telescope";

import { apiService } from '../api/api';
function App() {  
  
const isLoaded = useCatalogStore((state) => state.isLoaded);
const updateCatalog = useCatalogStore((state) => state.updateCatalog);
const isObserverLoaded = useObserverStore((state) => state.isLoaded);
const initializeObserver = useObserverStore((state) => state.initializeObserver);
const setConfig = useConfigStore((state) => state.setConfig);
const getAzimuth = useConfigStore((state) => state.getAzimuth)
const setConfigScheme = useConfigStore((state) => state.setConfigScheme);

  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        if (isLoaded) return;
        updateCatalog(await loadCatalog(getAzimuth()));
        const date = getNextSunsetDate(50.6667,3.15,true)?.date||new Date();

        if (!isObserverLoaded)  {
            initializeObserver(50.6667, 3.15, date, getNextSunsetDate(50.6667,3.15,true)?.date||new Date(), getNextSunriseDate(50.6667,3.15,false)?.date||new Date());
        }
        
        const initial = await apiService.getConfig();
        const initialData = initial ? initial:{};
        setConfig(initialData);

        const configSchema = await apiService.getConfigScheme();
        const formDefinition = configSchema? configSchema:[];
        setConfigScheme(formDefinition);

      } catch (error) {
        console.error("Failed to fetch catalog:", error);
      }
    }
      if (!isLoaded) fetchCatalog(); 
  }, [isLoaded, updateCatalog, isObserverLoaded, initializeObserver]);


   
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="catalog" element={<CatalogPage />} />
          <Route path="plan" element={<PlanPage />} />
          <Route path="config" element={<Configurator />} />
          <Route path="config/observatory" element={ <ObservatoryConfig/> }/>
          <Route path="config/telescope" element={ <TelescopeConfig/> }/>

        </Route>
        
      </Routes>
    </BrowserRouter>
  )
}

export default App
