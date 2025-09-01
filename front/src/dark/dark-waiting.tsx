import type { DarkLibraryProcessType } from "../../types/api.type";
import Button from "../../design-system/buttons/main";
import Swal from "sweetalert2";
import { useTranslation } from 'react-i18next';
import { apiService } from "../../api/api";
import { useWebSocketStore } from "../../store/store";
import { useEffect, useRef, useState } from "react";
import { LoaderCircle } from "lucide-react";

type Props = {
  processList: DarkLibraryProcessType[];
  refresh: () => void;
};

export default  function DarkProcessStatus({ processList, refresh }: Props) {
    const { t } = useTranslation();
    const connect = useWebSocketStore((state) => state.connect);
    const messages = useWebSocketStore((state) => state.messages);
    const isConnected = useWebSocketStore((state) => state.isConnected);
    const [jobStatus, setJobStatus] = useState<string>("En attente d’instructions...");
    const lastMessageRef = useRef<number | null>(null);

    useEffect(() => {
        if (!isConnected) connect();
      }, [isConnected, connect]);


    useEffect(() => {

       if (messages.length === lastMessageRef.current)  return;

        lastMessageRef.current = messages.length;
        const newMessage = messages[messages.length - 1];
        if (!newMessage) return;
        if (newMessage.sender === "SCHEDULER") {
          if (newMessage.message === "NEWIMAGE") {
            refresh();
          } else if (newMessage.message === "STATUS") {
            setJobStatus((newMessage.data as string) || t("plan.unknown_status"));
          } else if (newMessage.message === "TEMPERATURE") {
            setJobStatus(`${t("plan.temperature")} [${newMessage.data}]`);
          }
        }
      }, [messages, refresh, setJobStatus, t]);
    
    const  handleStop= async () => {
        Swal.fire({
              title: t('form.confirm'),
              showCancelButton: true,
              confirmButtonText: t('form.stop'),
              denyButtonText: t('form.dontstop')
            }).then((result) => {
              if (result.isConfirmed){
                apiService.stopDarkProcessing().then(()=> {
                refresh();
                });

              }
            });
    }

  return (
    <div className="p-4 space-y-4 mx-auto max-w-2xl w-[90%] bg-gray-800 rounded-xl shadow">
      <h2 className="text-lg font-bold text-center">Résumé du traitement Dark</h2>

      {processList.length === 0 && (
        <p className="text-center text-gray-900">Aucune tâche en cours.</p>
      )}

        <div className="w-full max-w-4xl bg-blue-50 text-blue-800 border border-blue-200 rounded-md px-4 py-3 flex items-center gap-3 shadow-sm">
        {jobStatus!="finished" && (<LoaderCircle className="animate-spin w-5 h-5" />)}
        <p className="text-sm font-medium">{jobStatus}</p>
      </div>

      {processList.map((item, index) => {
        let status = "En attente ⬜️";
        if (item.done) status = "Terminé ✅";
        else if (item.in_progress) status = "En cours ⏳";

        return (
          <div
            key={index}
            className="flex justify-between items-center bg-gray-800 rounded-lg px-4 py-2"
          >
            <div className="text-sm">
              <div>
                <span className="font-semibold">Temp:</span> {item.temperature}°C
              </div>
              <div>
                <span className="font-semibold">Expo:</span> {item.exposition}s
              </div>
              <div>
                <span className="font-semibold">Gain:</span> {item.gain}
              </div>
              <div>
                <span className="font-semibold">Captures:</span> {item.progress} / {item.count}
              </div>
            </div>

            <div className="text-right text-sm">
              <div className="font-semibold">{status}</div>
              {item.in_progress && (
                <div className="text-xs text-gray-600">Temps restant : {item.eta}s</div>
              )}
            </div>
          </div>
        );
      })}
      <Button onClick={handleStop}>Stop</Button>
    </div>
  );
}
