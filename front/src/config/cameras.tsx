import ObservatoryList from '../../components/observatory/observatory';
import { apiService } from '../../api/api';
import { useEffect, useState } from 'react';
import type {  ConfigItems } from '../../store/config.type';
import type { Field } from '../../types/dynamicform.type';
import { CameraCard} from '../../components/observatory/cameraCard';

import { useObserverStore } from "../../store/store";

const  CamerasConfig =  () => {
    const [cameras, setCameras] = useState<ConfigItems[]>([]);
    const [cameraLayout, setCameraLayout] = useState<Field[]>([]);

    const {camera, setCamera } = useObserverStore();

    useEffect(() => {
        const loadCamera = async () => {
            const cameraLayout = await apiService.getCamerasSchema();
            const cameras = await apiService.getCameras();
            console.log(cameras)
            setCameraLayout(cameraLayout);
            setCameras(cameras);
        }

        loadCamera();
    },[])




    const handleEditCameras = async (items: ConfigItems[]) => {
        await apiService.setCameras(items);
        const cameras = await apiService.getCameras();
        setCameras(cameras)
        
        setCamera(await apiService.getCurrentCamera());

    };

    const changeCamera = async (camera : ConfigItems) =>{
        apiService.setCurrentCamera(camera.name as string);
        setCamera(camera);
        
        
    }

    return ( <div>

                <div className="flex items-center justify-center mt-4">
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