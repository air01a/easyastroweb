"use server";
import { getAssetFileTxt } from "@/lib/fsutils";
import { CatalogItem } from "./catalog.type";
import { equCoordStringToDecimal } from "../astro-utils";

export async function loadCatalogFromCSV() {
    const csvText = await getAssetFileTxt('catalog','catalog.csv');
    const lines = csvText.split('\n').filter((line) => line.trim() !== '');
    const headers = lines[0].split(';').map(h => h.trim());
    let index = 0;
    const catalog: CatalogItem[] = lines.slice(1).map((line) => {
        const values = line.split(';').map((v) => v.trim());
        const get = (key: string) => values[headers.indexOf(key)] ?? '';
        const ra = equCoordStringToDecimal(get('RA'));
        const dec = equCoordStringToDecimal(get('DEC'));

    
        return {
        index : index++,
        dynamic: get('Type')==='1'?true:false, // ou autre logique si tu veux calculer ça
        name: get('Name'),
        ngc: get('NGC'),
        objectType: get('Object type'),
        season: get('Season'),
        magnitude: parseFloat(get('Magnitude')) || 0,
        constellationEN: get('Constellation (EN)'),
        constellationFR: get('Constellation (FR)'),
        constellationLatin: get('Constellation (Latin)'),
        ra: ra || 0,
        dec: dec || 0,
        distance: parseFloat(get('Distance')) || 0,
        size: parseFloat(get('Size')) || 0,
        image: get('Image'),
        imageCiel: get('Image ciel'),
        location: get('Location'),
        status: 'visible',
        isSelected: false
        };
    });
    return catalog;
}