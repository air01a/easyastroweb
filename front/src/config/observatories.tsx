import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
//import type { Field } from "../../components/forms/dynamicform.type";
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../components/forms/dynamicform.type';
import { ObservatoryCard } from '../../components/observatory/observatoryCard';
const ObservatoryConfig = () => {
    const [items, setItems] = useState<ConfigItems[]>([]);
    const [layout, setLayout] = useState<Field[]>([]);
    
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
        apiService.setObservatory(items);
        const obs = await apiService.getObservatory();
        setItems(obs);

    };



    return ( <ObservatoryList items={items}  onEdit={handleEdit} formLayout={layout} CardComponent={ObservatoryCard}/>)

}

export default ObservatoryConfig;