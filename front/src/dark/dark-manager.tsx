import { useEffect, useState, useRef } from "react";
import DarkEditor from "./dark-editor";
import type { DarkLibraryProcessType } from "../../types/api.type";
import { apiService } from "../../api/api";
import DarkProcessStatus from './dark-waiting';

export default function DarkManager() {
  const [isProcessing, setIsProcessing] = useState<DarkLibraryProcessType[]>([]);
  const intervalRef = useRef<NodeJS.Timeout | null>(null); // pour garder une référence claire au setInterval

  const refreshProcessing = async () => {
    const data = await apiService.getDarkProcessing();
    setIsProcessing(data);
  };

  // Initial fetch
  useEffect(() => {
    refreshProcessing();
  }, []);

  // Gère l’intervalle de rafraîchissement si processing actif
  useEffect(() => {
    // Si des tâches sont en cours, démarrer un intervalle
    if (isProcessing.length > 0 && intervalRef.current === null) {
      intervalRef.current = setInterval(() => {
        refreshProcessing();
      }, 10000);
    }

    // Si plus rien à traiter, arrêter l’intervalle
    if (isProcessing.length === 0 && intervalRef.current !== null) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Nettoyage à la destruction
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isProcessing]);

  return (
    <div>
      {(isProcessing.length === 0) ? (
        <DarkEditor refresh={refreshProcessing} />
      ) : (
        <DarkProcessStatus processList={isProcessing} refresh={refreshProcessing} />
      )}
    </div>
  );
}
