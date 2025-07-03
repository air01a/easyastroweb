import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../types/dynamicform.type';
import { TelescopeCard} from '../../components/observatory/telescopeCard';
import { H2 } from '../../design-system/text/titles';
import CamerasConfig from './cameras';
import { useObserverStore } from "../../store/store";

const  ObservatoryConfig =  () => {
    const [items, setItems] = useState<ConfigItems[]>([]);
    const [layout, setLayout] = useState<Field[]>([]);

    const {observatory, telescope, initializeObserver, camera, sunRise, sunSet, date } = useObserverStore();

    useEffect(() => {
        const loadTelescope = async () => {
            const obs = await apiService.getTelescope();
            const layout = await apiService.getTelescopeSchema();
            setLayout(layout);
            setItems(obs);
        }

        loadTelescope();
    },[])

    const handleEdit = async (items: ConfigItems[]) => {
        await apiService.setTelescope(items);
        const obs = await apiService.getTelescope();
        setItems(obs);

    };

    const changeTelescope = async (telescope : ConfigItems) =>{
        apiService.setCurrentTelescope(telescope.name as string);
        initializeObserver(telescope, observatory, camera, date, sunSet, sunRise);
        
        
    }

    return ( <div>
                <div className="flex items-center justify-center">
                    <H2>Téléscope</H2>
                </div>
                    <ObservatoryList 
                        items={items} 
                        onSelect={changeTelescope} 
                        selectedName={telescope.name as string} 
                        onEdit={handleEdit} 
                        formLayout={layout} 
                        CardComponent={TelescopeCard}
                    />
 
                    <CamerasConfig />

                </div>
            )

}

export default ObservatoryConfig;