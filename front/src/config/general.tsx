import  DynamicForm  from "../../components/forms/dynamicform";
import type { Field } from "../../types/dynamicform.type";
import { useEffect, useState } from "react";
import { useConfigStore} from "../../store/store";
import { FlashMessage } from "../../design-system/messages/flashmessages";
import { apiService } from '../../api/api';

export default function GeneralConfig() {
    const [formDefinition, setFormDefinition] = useState<Field[]>([]);
    const [initialValues, setInitialValues] = useState({});
    //const updateCatalog = useCatalogStore((state) => state.updateCatalog);
    const [message, setMessage] = useState<string>("");
    const { config, setConfig } = useConfigStore();
    const [error, setError] = useState<boolean>(false);

    const init=config;
    useEffect(() => {
        const  fetchData =async () => {
            const data = await apiService.getConfigScheme()
            const config = await apiService.getConfig();
            const formDefinition = data ? await data :[];
            setFormDefinition(formDefinition);
            setInitialValues(config);
            setConfig(config);
        }
        fetchData();
    },[])




    const  onSave = async () => {
        if (error) return;
        setConfig(initialValues)
        apiService.sendConfig(initialValues)
        //setAzimuth(compassSelection);
        //updateCatalog(await loadCatalog(compassSelection));
        setMessage("Configuration saved")
    }

    return (<div>
        <DynamicForm formDefinition={formDefinition } initialValues={init}
            onChange={(values, error) => { setInitialValues(values); setError(error)}}
        />
        
              
              
    <div className="flex flex-col justify-center  items-center">
        <button
          type="submit"
          disabled={error}
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