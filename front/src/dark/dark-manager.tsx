import { useEffect, useState } from "react";
import DarkEditor from "./dark-editor";
import type { DarkLibraryProcessType } from "../../types/api.type";
import { apiService } from "../../api/api";
import DarkProcessStatus from './dark-waiting';

export default function DarkManager() {

    const [isProcessing, setIsProcessing] = useState<DarkLibraryProcessType[]>([]);


    const refreshProcessing = async () => {
        const data = await apiService.getDarkProcessing();
        setIsProcessing(data);
    };
    useEffect(()=>{
        refreshProcessing();
    },[])
    return (
        <div>
        { (isProcessing.length===0) ? (
            <DarkEditor refresh={refreshProcessing}/>
        ) :
            (
                <DarkProcessStatus processList={isProcessing} refresh={refreshProcessing} />

            ) 
        }
        </div>
    )
}
