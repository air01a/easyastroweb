import { useEffect, useRef, useState } from "react";
import type {  PlanHistory} from "../../types/api.type";
import { apiService } from "../../api/api";
import { X } from "lucide-react";
import { useTranslation } from 'react-i18next';

export default function History({ refreshKey }: { refreshKey: number }) {
  const [history, setHistory] = useState<PlanHistory[]>([]);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const randomRef = useRef(Math.random());

  const { t } = useTranslation();
  const fetchHistory = async () => {
    const data: PlanHistory[] = await apiService.getPlanHistory();
    setHistory(data);
  };

  useEffect(() => {
    fetchHistory();
  }, [refreshKey]); // 🔁 relance fetch à chaque changement de clé

  return (
    <div>
      <div className="w-full  mt-10">
        <h2 className="text-xl font-bold mb-4 text-left">{t('plan.history')}</h2>
        <div className="space-y-2 flex flex-col  items-center justify-center">
          {history.map((plan: PlanHistory, index:number) => {
            const isRunning = !!plan.real_start && !plan.end;
            return (
              <div
                key={index}
                className={`flex flex-col md:flex-row w-full items-center justify-between border-gray-200 text-black border rounded p-3 shadow ${
                  isRunning ? "bg-green-500" : "bg-white"
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-center md:gap-6 text-sm w-full">
                  <div>
                    <span className="font-semibold">{t('plan.target')} :</span> {plan.object}
                  </div>
                  <div>
                    <span className="font-semibold">{t('plan.start')} :</span>{" "}
                    {plan.real_start || "—"}
                  </div>
                  <div>
                    <span className="font-semibold">{t('plan.end')} :</span>{" "}
                    {plan.end || (isRunning ? "En cours" : "—")}
                  </div>
                  <div>
                    <span className="font-semibold">{t('plan.images')} :</span> {plan.images} / {plan.number}
                  </div>
                  <div>
                    <span className="font-semibold">{t('plan.expo')} :</span> {plan.expo}
                  </div>
                  <div>
                    <span className="font-semibold">{t('plan.filter')} :</span> {plan.filter}
                  </div>

                </div>
                {plan.jpg && plan.end &&(
                  <img
                    src={apiService.getBaseUrl() + `/observation/history/${index}?t=${index}`}
                    alt="Miniature"
                    className="w-32 h-20 object-cover rounded border mt-2 md:mt-0 cursor-pointer"
                    onClick={() => setModalImage(apiService.getBaseUrl() + `/observation/history/${index}?t=${randomRef}i=${index}`)}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {modalImage && (
        <div
          className="fixed inset-0 z-50 bg-black bg-opacity-80 flex items-center justify-center"
          onClick={() => setModalImage(null)}
        >
          <div className="relative max-w-6xl w-full px-4" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={() => setModalImage(null)}
              className="absolute top-2 right-2 text-white bg-black/60 rounded-full p-1 hover:bg-black/80"
            >
              <X className="w-6 h-6" />
            </button>
            <img
              src={modalImage}
              alt="Full size"
              className="w-full max-h-[90vh] object-contain mx-auto rounded"
            />
          </div>
        </div>
      )}
    </div>

  );
}
