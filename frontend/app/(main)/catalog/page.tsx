"use client";
import AstronomyObjectList from "@/design-system/box/objectbox";
import { useEffect, useState } from "react";
import CatalogFilters from "@/design-system/filters/catalogfilters";
import { filterCatalog } from "@/actions/catalog/catalog";
import { useCatalogStore } from "@/store/store";
import { CatalogItem } from '@/lib/astro/catalog/catalog.type';

export default function CatalogPage() {

    const { catalog, setSelected } = useCatalogStore()
    const [localCatalog, setLocalCatalog] = useState<CatalogItem[]>([]);

    const [filters, setFilters] = useState({
        invisible: true,
        hidden: false,
        partial: true,
      });

    const onToggle = async (index:number) =>{
        const catalogTmp = catalog ? [...catalog] : [];
        catalogTmp[index].isSelected = !catalogTmp[index].isSelected;
        setSelected(catalogTmp[index].index, catalogTmp[index].isSelected)
    }

    useEffect(() => {
        const getCatalog = async () => {
            const local = await filterCatalog(catalog, 'all', filters.invisible, filters.hidden, filters.partial);
            setLocalCatalog(local);

        }

        getCatalog();
    }, [catalog, filters]);

    return (
        <div>
            <h1>Catalog</h1>
            <CatalogFilters filters={filters} setFilters={setFilters} />
            { localCatalog   && (
                <AstronomyObjectList objects={localCatalog} onToggle={onToggle} />
            )}
        </div>
    )
}

