"use client";
import AstronomyObjectList from "@/design-system/box/objectbox";
import { useEffect, useState } from "react";
import CatalogFilters from "@/design-system/filters/catalogfilters";
import { filterCatalog } from "@/actions/catalog/catalog";
import { CatalogItem} from '@/lib/astro/catalog/catalog.type';

export default function CatalogPage() {

    const [filters, setFilters] = useState({
        invisible: true,
        hidden: false,
        partial: true,
      });

    const [catalog, setCatalog] = useState<null|CatalogItem[]>(null);


    useEffect(() => {
        const getCatalog = async () => {
            const catalog = await filterCatalog('all', filters.invisible, filters.hidden, filters.partial);
            console.log(catalog);
            setCatalog(catalog);
        }
        getCatalog();
    }, [filters]);



    return (
        <div>
            <h1>Catalog</h1>
            <CatalogFilters filters={filters} setFilters={setFilters} />
            { catalog && (
                <AstronomyObjectList objects={catalog} />
            )}
        </div>
    )
}

