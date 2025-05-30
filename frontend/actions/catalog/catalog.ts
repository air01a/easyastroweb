"use server";
import { filterCatalog as fC } from "@/lib/astro/catalog/catalog";


export async function filterCatalog(type:string, showInvisible:boolean, showMasked:boolean, showPartial:boolean) {
    return await fC(type, showInvisible, showMasked, showPartial);
}