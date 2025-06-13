import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import AltitudeChart from "../../design-system/altitude-graph/altitude-graph";
import ImageSettings from '../../components/plan/imagesettings';
import { dateToNumber } from "../../lib/astro/astro-utils";
import { useEffect, useState } from 'react';
import type { ImageConfig } from './plan.type';

export function ObjectPlanificator({index, sunrise, sunset, startDate, item, onUpdate}: { index:number,  sunrise: Date, sunset:Date, startDate: number, item:CatalogItem, onUpdate : (index:number, config: ImageConfig[]) => void}) {
    const sunsetNum = dateToNumber(sunset);
    const sunriseNum = dateToNumber(sunrise);

    const selectedRangesForNight = [
            { start: sunsetNum, end: startDate, color: 'red'},
            { start: 15, end: sunsetNum, color: 'blue' },
            { start: sunriseNum, end: 100, color: 'blue' },
            ];
    const [settings, setSettings]=useState<ImageConfig[]>([]);
    const [selectedRange, setSelectedRange]=useState(selectedRangesForNight);
    const [maxDuration, setMaxDuration]=useState<number>(0);


     useEffect(() => {
        setMaxDuration(sunriseNum - startDate % 24)
        let newDuration=0;
        settings.forEach((item)=>newDuration+=item.exposureTime*item.imageCount)
        newDuration/=3600;
        const newConfig = [...selectedRangesForNight, {start:startDate, end:startDate+newDuration, color:'green'}];
        setSelectedRange(newConfig)
        onUpdate(index, settings)
     }, [settings, startDate]);


    return (
                <div key={index} className="border p-4 mb-4 rounded-lg">
                    <div className="flex items-center space-x-4 mb-4">
                        <img src={`/catalog/${item.image}`} alt={item.name} className="w-32 h-32 rounded-full shadow" />

                        <h2 className="text-xl font-bold">{item.name}</h2>
                        <p className="text-sm">Type: {item.objectType}</p>
                        <p className="text-sm">Magnitude: {item.magnitude}</p>
                        <p className="text-sm">Status: {item.status.replace('-', ' ')}</p>
                        <p className="text-sm">Visibility: {item.nbHoursVisible} hours</p>
                    </div>
                    <div className="flex items-center w-100 h-[250px] bg-gray-800 rounded-lg shadow-lg">
                    <AltitudeChart data={item.altitudeData||[]}  selectedRanges={selectedRange}/>
                    </div>
                <div className="flex items-centerflex justify-center"><ImageSettings onUpdate={setSettings} maxDuration={maxDuration} /></div>
                </div>
            );

}