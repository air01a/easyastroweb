import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
//import type { Field } from "../../components/forms/dynamicform.type";
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../components/forms/dynamicform.type';

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

    const handleEdit = (item: ConfigItems[]) => {
        alert(`Éditer: ${item}`);
    };



    return ( <ObservatoryList items={items}  onEdit={handleEdit} formLayout={layout}/>)

}

export default ObservatoryConfig;