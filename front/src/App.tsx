
//import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./home/home";
import  Layout  from "./Layout";
import { useCatalogStore, useObserverStore } from "../store/store"
import type { CatalogItem } from "../lib/astro/catalog/catalog.type";
import {computeCatalog, loadCatalogFromCSV} from "../lib/astro/catalog/catalog";
import {  useEffect } from "react";
import CatalogPage from "./catalog/catalog";
import { getNextSunriseDate, getNextSunsetDate } from "../lib/astro/astro-utils";

function App() {  
  
const isLoaded = useCatalogStore((state) => state.isLoaded);
const updateCatalog = useCatalogStore((state) => state.updateCatalog);
const isObserverLoaded = useObserverStore((state) => state.isLoaded);
const initializeObserver = useObserverStore((state) => state.initializeObserver);

  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        if (isLoaded) return;
        const response = await fetch("/catalog/catalog.csv");
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const data: CatalogItem[] = await loadCatalogFromCSV(await response.text());
        const date = getNextSunsetDate(50.6667,3.15,true)?.date||new Date();
       
        const catalog = await computeCatalog(data, 50.6667,3.15, date);
        updateCatalog(catalog);
        if (!isObserverLoaded)  {
            initializeObserver(50.6667, 3.15, date, getNextSunsetDate(50.6667,3.15,true)?.date||new Date(), getNextSunriseDate(50.6667,3.15,false)?.date||new Date());
        }


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
        </Route>
        
      </Routes>
    </BrowserRouter>
  )
}

export default App
