import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../types/dynamicform.type';
import { FilterWheelsCard} from '../../components/observatory/filterwheelCard';

import { useObserverStore } from "../../store/store";

const  FilterWheelsConfig =  () => {
    const [wheels, setWheels] = useState<ConfigItems[]>([]);
    const [wheelsLayout, setWheelsLayout] = useState<Field[]>([]);

    const {filterWheel, setFilterWheel } = useObserverStore();

    useEffect(() => {
        const loadFilterWheel = async () => {
            const wheelLayout = await apiService.getFilterWheelsSchema();
            const wheels = await apiService.getFilterWheels();
            console.log(wheels)
            setWheelsLayout(wheelLayout);
            setWheels(wheels);
        }

        loadFilterWheel();
    },[])




    const handleEditFilterWheel = async (items: ConfigItems[]) => {
        await apiService.setFilterWheels(items);
        const wheels = await apiService.getFilterWheels();
        setWheels(wheels);
    };  

    const onChangeFilterWheel = async (filterwheel : ConfigItems) =>{
        apiService.setCurrentFilterWheel(filterwheel.name as string);
        setFilterWheel(filterwheel);
        
        
    }

    return ( <div>

                <div className="flex items-center justify-center mt-4">
                </div>
                    <ObservatoryList 
                        items={wheels} 
                        onSelect={onChangeFilterWheel} 
                        selectedName={filterWheel.name as string} 
                        onEdit={handleEditFilterWheel} 
                        formLayout={wheelsLayout} 
                        CardComponent={FilterWheelsCard}
                    />

                </div>
            )

}

export default FilterWheelsConfig;