import  DynamicForm  from "../../components/forms/dynamicform";
import type { Field } from "../../components/forms/dynamicform.type";
import CircularButtonSelection from "../../components/forms/circularbutton";
import { useEffect, useState } from "react";
import { useConfigStore, useCatalogStore} from "../../store/store";
import {loadCatalog} from "../../lib/astro/catalog/catalog";
import { FlashMessage } from "../../design-system/messages/flashmessages";
import { ApiService } from '../../api/api';

export default function Configurator() {
    const [formDefinition, setFormDefinition] = useState<Field[]>([]);
    const [initialValues, setInitialValues] = useState({});
    const updateCatalog = useCatalogStore((state) => state.updateCatalog);
    const [message, setMessage] = useState<string>("");
    const { config, setConfig, setAzimuth, getAzimuth } = useConfigStore();

    const apiService = new ApiService();

    const init=config;
    useEffect(() => {
        const  fetchData =async () => {
            const data = await fetch('/configschema.json');
            const formDefinition = data?.body ? await data.json():[];
            setFormDefinition(formDefinition);
            setInitialValues(config);
        }
        fetchData();
    },[])

    const [compassSelection, setCompassSelection] = useState<boolean[]>(
        getAzimuth()
    );

    const handleCallback = (name: string, values: boolean[]) => {
        setCompassSelection(values);
    };

    const  onSave = async () => {
        setConfig(initialValues)
        apiService.sendConfig(initialValues)
        setAzimuth(compassSelection);
        updateCatalog(await loadCatalog(compassSelection));
        setMessage("Configuration saved")
    }

    return (<div>
        <DynamicForm formDefinition={formDefinition } initialValues={init}
            onChange={(values) => setInitialValues(values)}
        />
        <CircularButtonSelection
            name="compass"
            callBack={handleCallback}
            selectedButtons={compassSelection}
      /> 
              
              
    <div className="flex flex-col justify-center  items-center">
        <button
          type="submit"
          className="bg-white text-black px-4 py-2 rounded"
          onClick={()=> {onSave()}}
        >
          Enregistrer
        </button>
        {message.length>1 && (
        
                <FlashMessage
                    type="success"
                    message="Configuration sauvegardée avec succès !"
                    onClose={() => setMessage("")}
                    duration={3000} 
                />

      )}
      </div>
        </div>

        
    )
}