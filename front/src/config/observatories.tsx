import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../components/forms/dynamicform.type';
import { ObservatoryCard } from '../../components/observatory/observatoryCard';
import { useObserverStore, useCatalogStore } from "../../store/store";
import { getNextSunriseDate, getNextSunsetDate } from "../../lib/astro/astro-utils";
import {loadCatalog} from "../../lib/astro/catalog/catalog";


const ObservatoryConfig = () => {
    const [items, setItems] = useState<ConfigItems[]>([]);
    const [layout, setLayout] = useState<Field[]>([]);
    const {observatory, telescope }= useObserverStore();
    const updateCatalog = useCatalogStore((state) => state.updateCatalog);
    const initializeObserver = useObserverStore((state) => state.initializeObserver);
    

    useEffect(() => {
        const loadObservatory = async () => {
            const obs = await apiService.getObservatory();
            const layout = await apiService.getObservatoryScheme();
            setItems(obs);
            setLayout(layout);
        }

        loadObservatory();
    },[])

    const handleEdit = async (items: ConfigItems[]) => {
        await apiService.setObservatory(items);
        const obs = await apiService.getObservatory();
        setItems(obs);

    };


    const changeObservatory = async (observatory : ConfigItems) =>{
        apiService.setCurrentObservatory(observatory.name as string);
        const dateSunset= getNextSunsetDate(observatory.latitude as number,observatory.longitude as number,true)?.date||new Date();
        const dateSunrise= getNextSunriseDate(observatory.latitude as number,observatory.longitude as number,false)?.date||new Date();
        initializeObserver(telescope, observatory, dateSunset, dateSunset, dateSunrise);
        updateCatalog(await loadCatalog(observatory.visibility as boolean[]));
    }
    return ( 
    <div>
        <ObservatoryList 
            items={items}  
            editable={true} 
            onSelect={changeObservatory} 
            onEdit={handleEdit} 
            formLayout={layout} 
            selectedName={observatory.name as string} 
            CardComponent={ObservatoryCard}
        />
    </div>
    )

}

export default ObservatoryConfig;