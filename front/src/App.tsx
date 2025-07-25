
//import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./home/home";
import  Layout  from "./Layout";
import { useCatalogStore, useObserverStore, useConfigStore } from "../store/store"
import {loadCatalog} from "../lib/astro/catalog/catalog";
import {  Suspense, useEffect } from "react";
import CatalogPage from "./catalog/catalog";
import { getNextSunriseDate, getNextSunsetDate } from "../lib/astro/astro-utils";
import Plan from "./plan/plan";
import DarkManager from "./dark/dark-manager";
import ToolsDashboard from './tools/tools';
import ObservatoryConfig from "./config/observatories";
import TelescopeConfig from "./config/telescopes";
import { useLanguage } from '../i18n/hook';
import '../i18n/i18n'; // 
import { apiService } from '../api/api';
import GeneralConfig from "./config/general";
function App() {  
  
  const isLoaded = useCatalogStore((state) => state.isLoaded);
  const updateCatalog = useCatalogStore((state) => state.updateCatalog);
  const isObserverLoaded = useObserverStore((state) => state.isLoaded);
  const setCamera = useObserverStore((state)=> state.setCamera)
  const setFilterWheel = useObserverStore((state)=> state.setFilterWheel)
  const initializeObserver = useObserverStore((state) => state.initializeObserver);
  const setConfig = useConfigStore((state) => state.setConfig);
  const setConfigScheme = useConfigStore((state) => state.setConfigScheme);
  const { currentLanguage } = useLanguage();

  useEffect(() => {
    document.documentElement.lang = currentLanguage;
  }, [currentLanguage]);


  useEffect(() => {
    const fetchCatalog = async () => {
      try {

        // Get last telescope and observatory config
        const telescope = await apiService.getCurrentTelescope();
        const observatory = await apiService.getCurrentObservatory();
        const camera = await apiService.getCurrentCamera();
        const filterWheel = await apiService.getCurrentFilterWheel();

        const dateSunset = getNextSunsetDate(observatory.latitude as number,observatory.longitude as number,true)?.date||new Date();
        const dateSunrise =getNextSunriseDate(observatory.latitude as number,observatory.longitude as number,false)?.date||new Date();
        initializeObserver(telescope, observatory, dateSunset, dateSunset, dateSunrise);
        setCamera(camera);
        setFilterWheel(filterWheel);

        // Calculate catalog
        updateCatalog(await loadCatalog(observatory.visibility as boolean[]));
        const initial = await apiService.getConfig();
        const initialData = initial ? initial:{};
        setConfig(initialData);

        // Get config from remote server
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
          <Route path="plan" element={<Plan />} />
          <Route path="tools" element={<ToolsDashboard />} />
          <Route path="config/observatories" element={ <ObservatoryConfig/> }/>
          <Route path="config/telescopes" element={ <TelescopeConfig/> }/>
          <Route path="config/general" element={<GeneralConfig />} />
          <Route path="dark/config" element={<DarkManager />} />
        </Route>
        
      </Routes>
    </BrowserRouter>
  )
}


const AppWithSuspense: React.FC = () => (
  <Suspense fallback={<div>Loading translations...</div>}>
    <App />
  </Suspense>
);
export default AppWithSuspense
