"use client";
import { useEffect, useState } from "react";
import {  getSelectedFromCatalog } from "../../lib/astro/catalog/catalog";
import { useCatalogStore, useObserverStore } from "../../store/store";
import type { CatalogItem } from '../../lib/astro/catalog/catalog.type';
import { ObjectPlanificator } from '../../components/plan/objectplanificator';
import type { ImageConfig } from "../../components/plan/plan.type";
import { dateToNumber } from "../../lib/astro/astro-utils";

export default function PlanPage() {

    const { catalog } = useCatalogStore()
    const [localCatalog, setLocalCatalog] = useState<CatalogItem[]>([]);
    const { sunRise, sunSet } = useObserverStore();
    const [settings, setSettings]=useState<ImageConfig[][]>([]);
    const [startDates, setStartDates] = useState<{startDate:number, endDate:number}[]>([]);

    const updateSettings = (index:number, config:ImageConfig[]) =>{
        const newSettings = [...settings];
        newSettings[index]=config;
        setSettings(newSettings);
    }

    const getDuration = (settings : ImageConfig[]) => {
        if(!settings) return 0;
        let newDuration=0;
        settings.forEach((item)=>newDuration+=item.exposureTime*item.imageCount)
        return newDuration/=3600;
    }

    useEffect(() => {
        const getCatalog = async () => {
            const local = (await getSelectedFromCatalog(catalog)).sort((a, b) => {
                if (a.meridian && b.meridian) {
                    return (b.meridian.getHours()*60+b.meridian.getMinutes()-(a.meridian.getHours()*60+a.meridian.getMinutes()));
                } else return 0;
            });
            setLocalCatalog(local);

        }

        getCatalog();
    }, [catalog]);

    useEffect(()=> {
        let startDate=dateToNumber(sunSet);
        const newStartDates : {startDate:number, endDate:number}[] = [];

        for (let i=0;i<settings.length;i++) {
            const duration = getDuration(settings[i]);
            newStartDates[i]={startDate:startDate%24, endDate:(startDate+duration)%24}

            startDate+=duration%24;
       }
       setStartDates(newStartDates);
    },[settings])
 

    return (
        <div>
            <h1>Plan</h1>
            {localCatalog.map((item, index) => (
                    <ObjectPlanificator index={index} item={item} sunrise={sunRise} sunset={sunSet} startDate={startDates[index]?startDates[index].startDate:14}  onUpdate={updateSettings}/>
                ))}
        </div>
    )
}

