import  DynamicForm  from "../../components/forms/dynamicform";
import type { Field } from "../../components/forms/dynamicform.type";
import CircularButtonSelection from "../../components/forms/circularbutton";
import { useEffect, useState } from "react";
import { useConfigStore } from "../../store/store";

export default function Configurator() {
    const [formDefinition, setFormDefinition] = useState<Field[]>([]);
    const [initialValues, setInitialValues] = useState({});

    const { config, setConfig, setAzimuth, getAzimuth } = useConfigStore();


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

    const onSave = () => {
        setConfig(initialValues)
        setAzimuth(compassSelection);

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
              
              
    <div className="flex justify-center  items-center">
        <button
          type="submit"
          className="bg-white text-black px-4 py-2 rounded"
          onClick={()=> {onSave()}}
        >
          Enregistrer
        </button>
      </div>
        </div>

        
    )
}