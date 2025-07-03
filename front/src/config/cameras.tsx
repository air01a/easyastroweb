import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../types/dynamicform.type';
import { CameraCard} from '../../components/observatory/cameraCard';
import { H2 } from '../../design-system/text/titles';

import { useObserverStore } from "../../store/store";

const  CamerasConfig =  () => {
    const [cameras, setCameras] = useState<ConfigItems[]>([]);
    const [cameraLayout, setCameraLayout] = useState<Field[]>([]);

    const {observatory, telescope, initializeObserver, camera, sunRise, sunSet, date } = useObserverStore();

    useEffect(() => {
        const loadTelescope = async () => {
            const cameraLayout = await apiService.getCamerasSchema();
            const cameras = await apiService.getCameras();
            console.log(cameras)
            setCameraLayout(cameraLayout);
            setCameras(cameras);
        }

        loadTelescope();
    },[])




    const handleEditCameras = async (items: ConfigItems[]) => {
        await apiService.setCameras(items);
        const cameras = await apiService.getCameras();
        setCameras(cameras);

    };

    const changeCamera = async (camera : ConfigItems) =>{
        apiService.setCurrentCamera(camera.name as string);
        initializeObserver(telescope, observatory, camera,  date, sunSet, sunRise);
        
        
    }

    return ( <div>

                <div className="flex items-center justify-center mt-4">
                    <H2>Caméra</H2>
                </div>
                    <ObservatoryList 
                        items={cameras} 
                        onSelect={changeCamera} 
                        selectedName={camera.name as string} 
                        onEdit={handleEditCameras} 
                        formLayout={cameraLayout} 
                        CardComponent={CameraCard}
                    />

                </div>
            )

}

export default CamerasConfig;