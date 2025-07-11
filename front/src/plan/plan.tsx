"use client";
import { apiService } from "../../api/api";
import PlanPage from './planpage'
import RunningPlanPage from "./runningplanpage";
import { useEffect, useState } from "react";

export default function Plan() {
    const [planRunning, setPlanRunning] = useState<boolean|null>(null);
    useEffect(()=>{
      const  isRunning = async () => {
        const activePlan = await apiService.getIsPlanRunning();
        setPlanRunning(activePlan);
        
      }

      isRunning();
    },[]);

    return (
        <div>
            <h1>Plan</h1>
            {planRunning===false && <PlanPage />}
            {planRunning===true && <RunningPlanPage />}

            {planRunning===null && <div>Loading</div>}
        </div>
    )
}