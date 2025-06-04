"use server";
import { filterCatalog as fC, computeCatalog as cC } from "@/lib/astro/catalog/catalog";
import { CatalogItem } from '@/lib/astro/catalog/catalog.type';

export async function filterCatalog(catalog: CatalogItem[], type:string, showInvisible:boolean, showMasked:boolean, showPartial:boolean) {
    return await fC(catalog, type, showInvisible, showMasked, showPartial);
}

export async function computeCatalog(catalog: CatalogItem[], latitude: number, longitude: number, date: Date) {
    return await cC(catalog, latitude, longitude, date);
}