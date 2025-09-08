import { BrowserRouter, Routes, Route } from "react-router-dom";
import { lazy, Suspense, useEffect } from "react";
import Home from "./home/home";
import Layout from "./Layout";

import { useCatalogStore, useObserverStore, useConfigStore } from "../store/store";
import { loadCatalog } from "../lib/astro/catalog/catalog";
import { getNextSunriseDate, getNextSunsetDate } from "../lib/astro/astro-utils";
import { useLanguage } from '../i18n/hook';
import '../i18n/i18n';
import { apiService } from '../api/api';

// Lazy-loaded components
const CatalogPage = lazy(() => import("./catalog/catalog"));
const Plan = lazy(() => import("./plan/plan"));
const DarkManager = lazy(() => import("./dark/dark-manager"));
const ToolsDashboard = lazy(() => import("./tools/tools"));
const ObservatoryConfig = lazy(() => import("./config/observatories"));
const TelescopeConfig = lazy(() => import("./config/telescopes"));
const GeneralConfig = lazy(() => import("./config/general"));
const FocusHelper = lazy(()=>import("./focus/focus-helper"));
const Map = lazy(()=>import("./map/celestial"));

function App() {
  const isLoaded = useCatalogStore((state) => state.isLoaded);
  const updateCatalog = useCatalogStore((state) => state.updateCatalog);
  const isObserverLoaded = useObserverStore((state) => state.isLoaded);
  const setCamera = useObserverStore((state) => state.setCamera);
  const setFilterWheel = useObserverStore((state) => state.setFilterWheel);
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
        const telescope = await apiService.getCurrentTelescope();
        const observatory = await apiService.getCurrentObservatory();
        const camera = await apiService.getCurrentCamera();
        const filterWheel = await apiService.getCurrentFilterWheel();

        const dateSunset = getNextSunsetDate(observatory.latitude as number, observatory.longitude as number, true)?.date || new Date();
        const dateSunrise = getNextSunriseDate(observatory.latitude as number, observatory.longitude as number, false)?.date || new Date();

        initializeObserver(telescope, observatory, dateSunset, dateSunset, dateSunrise);
        setCamera(camera);
        setFilterWheel(filterWheel);

        updateCatalog(await loadCatalog(observatory.visibility as boolean[]));

        const initial = await apiService.getConfig();
        setConfig(initial || {});

        const configSchema = await apiService.getConfigScheme();
        setConfigScheme(configSchema || []);
      } catch (error) {
        console.error("Failed to fetch catalog:", error);
      }
    };

    if (!isLoaded) fetchCatalog();
  }, [isLoaded, updateCatalog, isObserverLoaded, initializeObserver]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route
            path="catalog"
            element={
              <Suspense fallback={<div>Chargement du catalogue...</div>}>
                <CatalogPage />
              </Suspense>
            }
          />
          <Route
            path="plan"
            element={
              <Suspense fallback={<div>Chargement du plan...</div>}>
                <Plan />
              </Suspense>
            }
          />
          <Route
            path="tools"
            element={
              <Suspense fallback={<div>Chargement des outils...</div>}>
                <ToolsDashboard />
              </Suspense>
            }
          />
          <Route
            path="tools/observatories"
            element={
              <Suspense fallback={<div>Chargement des observatoires...</div>}>
                <ObservatoryConfig />
              </Suspense>
            }
          />
          <Route
            path="tools/telescopes"
            element={
              <Suspense fallback={<div>Chargement des télescopes...</div>}>
                <TelescopeConfig />
              </Suspense>
            }
          />
          <Route
            path="tools/config"
            element={
              <Suspense fallback={<div>Chargement de la configuration générale...</div>}>
                <GeneralConfig />
              </Suspense>
            }
          />
          <Route
            path="tools/dark"
            element={
              <Suspense fallback={<div>Chargement du gestionnaire de darks...</div>}>
                <DarkManager />
              </Suspense>
            }
          />
          <Route
            path="tools/focus"
            element={
              <Suspense fallback={<div>Chargement de l'aide au focus...</div>}>
                <FocusHelper />
              </Suspense>
            }
          />
        
          <Route
            path="tools/map"
            element={
              <Suspense fallback={<div>Chargement de l'aide au focus...</div>}>
                <Map />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

const AppWithSuspense: React.FC = () => (
  <Suspense fallback={<div>Chargement des traductions...</div>}>
    <App />
  </Suspense>
);

export default AppWithSuspense;
