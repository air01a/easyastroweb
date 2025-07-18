"use client";
import { apiService } from "../../api/api";
import PlanPage from './planpage'
import RunningPlanPage from "./runningplanpage";
import { useEffect, useState } from "react";
import { H1 } from "../../design-system/text/titles";
import LoadingIndicator from "../../design-system/messages/loadingmessage";
export default function Plan() {
    const [planRunning, setPlanRunning] = useState<boolean|null>(null);

    const  isRunning = async () => {
      const activePlan = await apiService.getIsPlanRunning();
      setPlanRunning(activePlan);
    }


    useEffect(()=>{
      isRunning();
    },[]);

    return (
        <div>
            <H1>Plan</H1>
            {planRunning===false && <PlanPage refresh={isRunning}/>}
            {planRunning===true && <RunningPlanPage refresh={isRunning} />}

            {planRunning===null && <LoadingIndicator />}
        </div>
    )
}