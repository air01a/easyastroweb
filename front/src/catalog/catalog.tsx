"use client";
import AstronomyObjectList from "../../design-system/box/objectbox";
import { useEffect, useState } from "react";
import CatalogFilters from "../../components/filters/catalogfilters";
import { filterCatalog } from "../../lib/astro/catalog/catalog";
import { useCatalogStore } from "../../store/store";
import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import ResizableSidePanel from "../../design-system/panels/sidepanel";
import ObjectDetails from "../../components/object-details/objectdetails";

interface FilterInteface {
    invisible: boolean;
    hidden: boolean;
    partial: boolean;
    keywords: string;
    type : string;
}

export default function CatalogPage() {
    const [selectedDSO, setSelectedDSO] = useState<CatalogItem | null>(null);

    const { catalog, setSelected } = useCatalogStore()
    const [localCatalog, setLocalCatalog] = useState<CatalogItem[]>([]);

    const [filters, setFilters] = useState<FilterInteface>({
        invisible: false,
        hidden: false,
        partial: true,
        keywords: '',
        type: 'all'
      });

    const onToggle = async (index:number) =>{
        const catalogTmp = catalog ? [...catalog] : [];
        catalogTmp[index].isSelected = !catalogTmp[index].isSelected;
        setSelected(catalogTmp[index].index, catalogTmp[index].isSelected)
    }


    useEffect(() => {
        const getCatalog = async () => {
            const local = await filterCatalog(catalog, filters.type, filters.keywords, filters.invisible, filters.hidden, filters.partial);
            setLocalCatalog(local);

        }

        getCatalog();
    }, [catalog, filters]);


    useEffect(() => {
        if (selectedDSO) {
            document.body.style.overflow = "hidden";
        } else {
            document.body.style.overflow = "";
        }
        // Nettoyage au démontage
        return () => {
            document.body.style.overflow = "";
        };
    }, [selectedDSO]); 

    const onSelect = (index: number) => {
        const selected = localCatalog[index];
        setSelectedDSO(selected);
    }

    return (
        <div>
            <h1>Catalog</h1>
            <CatalogFilters filters={filters} setFilters={setFilters} />
            { localCatalog   && (
                <AstronomyObjectList onClick={onSelect} objects={localCatalog} onToggle={onToggle} />
            )}
             <ResizableSidePanel isOpen={!!selectedDSO} onClose={() => setSelectedDSO(null)} >
                {selectedDSO && (
                <div>

                    <ObjectDetails item={selectedDSO} />

                </div>
                )}
            </ResizableSidePanel>
        </div>
    )
}

