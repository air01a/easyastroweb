"use client";
import {  useObserverStore } from "../../store/store";
import AltitudeChart from "../../design-system/altitude-graph/altitude-graph";
import type { CatalogItem } from "../../lib/astro/catalog/catalog.type";
import { dateToNumber } from "../../lib/astro/astro-utils";


export default function ObjectDetails({item}:{item : CatalogItem}) {
    const { latitude, longitude, date, sunRise, sunSet } = useObserverStore();

    const selectedRanges = [
        { start: 15, end: dateToNumber(sunSet), color: 'blue' },
        { start: dateToNumber(sunRise), end: 100, color: 'blue' },
        ];
    return (
        <div className="w-full h-full min-w-[90%]" >
            <h2 className="text-xl font-bold mb-2 mt-2 ">{item.name}</h2>

            <div className="flex flex-col items-center justify-center mb-4">
                        <img
                          src={`/catalog/${item.image}`}
                          alt={item.name}
                          width={400}
                          height={400}
                          className="rounded-full shadow"
                        />
            </div>
            <p className="w-full">Détails de l’objet {item.description}</p>
            {item ? (
                <div>
                    <h2 className="w-full">{item.name} {date.toLocaleString()}</h2>
                    
                </div>
            ) : (
                <p>No item selected.</p>
            )}
            <div className="w-full h-100  bg-gray-800 rounded-lg shadow-lg">
                <AltitudeChart data={item.altitudeData||[]} selectedRanges={selectedRanges} />
            </div>
            { (!item.dynamic)&& (
            <div className="w-full h-100  bg-gray-800 rounded-lg shadow-lg">
                <p className="w-full">Localisation {item.description}</p>

               <img src={`/catalog/location/${item.name}.jpg`} />
            </div>
            )}
        </div>
        
    );


}
