"use client";
import { useCatalogStore, useObserverStore } from "@/store/store";
import { getAltitudeData } from "@/lib/astro/astro-utils";
import { useEffect } from "react";
import AltitudeChart from "@/design-system/altitude-graph/altitude-graph";

export default function DetailsPage() {
    const { catalog, setSelected } = useCatalogStore();
    const { latitude, longitude, date } = useObserverStore();
    const item = catalog[10];
    useEffect(() => {
        const data = getAltitudeData(latitude, longitude, date, item.ra, item.dec); 
        console.log(data)
    }, []);

    return (
        <div>
            <h1>Details</h1>
            <div></div>
            {item ? (
                <div>
                    <h2>{item.name} {date.toLocaleString()}</h2>
                    <button onClick={() => setSelected(item.index, !item.isSelected)}>
                        {item.isSelected ? "Deselect" : "Select"}
                    </button>
                </div>
            ) : (
                <p>No item selected.</p>
            )}
                        <AltitudeChart data={getAltitudeData(latitude, longitude, date, item.ra, item.dec)} />

        </div>
        
    );


}
