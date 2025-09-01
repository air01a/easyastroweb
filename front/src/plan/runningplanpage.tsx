import { useEffect, useState } from "react";
import { apiService } from "../../api/api";
import Button from "../../design-system/buttons/main";
import Swal from "sweetalert2";
import { X, LoaderCircle,  Focus } from "lucide-react";
import { useWebSocketStore } from "../../store/store";
import ImageBox from "../../design-system/box/imagebox";
import History from "../../components/history/history"
import { useTranslation } from 'react-i18next';
import ImageSettingsSliders from "../../components/image-settings/image-sliders"
import FwhmChart from "../../components/focus/focus-graph";
import type  { FwhmResults } from "../../types/api.type";

export default function RunningPlanPage({ refresh }: { refresh: () => void }) {
  const [image1, setImage1] = useState<string | null>(null);
  const [image2, setImage2] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const [modalImageType, setModalImageType] = useState<'image1' | 'image2' | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("En attente d'instructions...");
  const { t } = useTranslation();

  const connect = useWebSocketStore((state) => state.connect);
  const messages = useWebSocketStore((state) => state.messages);
  const isConnected = useWebSocketStore((state) => state.isConnected);
  const [isFocusing, setIsFocusing] = useState<boolean>(false);
  const [forceShowFocus, setforceShowFocus] = useState<boolean>(false);

  const [isStacking, setIsStacking] = useState<boolean>(false);
  const [fwhmResults, setFwhmResults] = useState<FwhmResults|null>(null)

  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const fetchImages = async () => {
    const baseUrl = apiService.getBaseUrl();
    const timestamp = Date.now();


    fetch(`${baseUrl}/observation/last_stacked_image?t=${timestamp}`)
      .then((res) => res.blob())
      .then((blob) => {
        const newImageUrl = URL.createObjectURL(blob);
        setImage1(newImageUrl);
        // Mettre à jour la modal si elle affiche image1
        if (modalImageType === 'image1') {
          setModalImage(newImageUrl);
        }
      });

    fetch(`${baseUrl}/observation/last_image?t=${timestamp}`)
      .then((res) => res.blob())
      .then((blob) => {
        const newImageUrl = URL.createObjectURL(blob);
        setImage2(newImageUrl);
        // Mettre à jour la modal si elle affiche image2
        if (modalImageType === 'image2') {
          setModalImage(newImageUrl);
        }
      });
    if (isFocusing) {
        const results = await apiService.getFocus();
        setFwhmResults(results);
    }
  };

  useEffect(() => {
    const getStatus = async() => {
      const status = await apiService.getOperationStatus();
      if (status===1) setIsFocusing(true);
      if (status===4) setIsStacking(true);
    }

    getStatus();
    fetchImages();
    if (!isConnected) connect();
  }, []);

  useEffect(() => {
    const newMessage = messages[messages.length - 1];
    if (!newMessage) return;
    if (newMessage.sender === "SCHEDULER" || newMessage.sender === "FOCUSER") {
      if (newMessage.sender==="FOCUSER") { 
        setIsFocusing(true);
      } else {
        if (isFocusing) setIsFocusing(false);
      }
      if (newMessage.message === "NEWIMAGE") {
        fetchImages();
        if (newMessage.sender=="SCHEDULER") {
          setIsStacking(true);
        }
        setHistoryRefreshKey((prev) => prev + 1);
      } else if (newMessage.message === "STATUS") {
        setJobStatus((newMessage.data as string) || t("plan.unknown_status"));
      } else if (newMessage.message==="REFRESHINFO") {
        setHistoryRefreshKey((prev) => prev + 1);
      } else if (newMessage.message === "TEMPERATURE") {
        setJobStatus(`${t("plan.temperature")} [${newMessage.data}]`);
      }
    }
  }, [messages]);

  const handleClick = () => {
    Swal.fire({
      title: t("plan.stop_plan"),
      text: `${t("plan.confirm_stop")}?`,
      icon: "warning",
      showCancelButton: true,
      confirmButtonText: t("plan.yes"),
      cancelButtonText: t("plan.cancel"),
    }).then((result) => {
      if (result.isConfirmed) {
        apiService.stopPlan();
        refresh();
      }
    });
  };

  const openModal = (imageUrl: string, imageType: 'image1' | 'image2') => {
    setModalImage(imageUrl);
    setModalImageType(imageType);
  };

  const closeModal = () => {
    setModalImage(null);
    setModalImageType(null);
  };

  const imgCount =
  (isStacking && image1 ? 1 : 0) +
  (image2 ? 1 : 0);


  return (
    <div className="flex flex-col items-center justify-center p-4 space-y-6">
      {/* STATUT */}
      <div className="w-full max-w-4xl bg-blue-50 text-blue-800 border border-blue-200 rounded-md px-4 py-3 flex items-center gap-3 shadow-sm">
        {jobStatus!="finished" && (<LoaderCircle className="animate-spin w-5 h-5" />)}
        <p className="text-sm font-medium">{jobStatus}</p>
      </div>

      {/* IMAGES EN COURS */}
      <div className="flex items-center justify-center">
        <div className="flex flex-wrap justify-center gap-6 max-w-8xl w-full">
          {isStacking && image1 && (
            <div className={imgCount === 1 ? "w-full md:w-1/2 mx-auto" : "w-full md:basis-[48%]"}>
              <ImageBox
                src={image1}
                label="Last stacked image"
                onClick={() => openModal(image1, 'image1')}
                className="w-full h-auto object-contain max-h-[70vh]"
              />
            </div>
          )}

          {image2 && (
            <div className={imgCount === 1 ? "w-full md:w-1/2 mx-auto" : "w-full md:basis-[48%]"}>
              <ImageBox
                src={image2}
                label="Last taken"
                onClick={() => openModal(image2, 'image2')}
                className="w-full h-auto object-contain max-h-[70vh]"
              />
            </div>
          )}
        </div>
      </div>
      {isStacking &&  <ImageSettingsSliders onUpdate={fetchImages}/>}
      {((isFocusing||forceShowFocus) && fwhmResults) && ( <div className="w-60%"><FwhmChart data={fwhmResults}/></div>)}
            {(!isFocusing && fwhmResults) && (
        <div><Button onClick={()=> {setforceShowFocus(!forceShowFocus)}} >
            {forceShowFocus ? <div className="flex flex-col justify-center items-center text-red-500">{t('focuser.hideFocus')}<Focus className="color-red-500" /> </div>: <div className="flex flex-col justify-center items-center">{t('focuser.showFocus')}<Focus /></div>}
          </Button></div>
      )}

      <History refreshKey={historyRefreshKey} />
      <Button onClick={handleClick}>{t('plan.stop_plan')}</Button>

      {/* MODAL IMAGE */}
      {modalImage && (
        <div
          className="fixed inset-0 z-50 bg-black bg-opacity-80 flex items-center justify-center"
          onClick={closeModal}
        >
          <div className="relative max-w-6xl w-full px-4" onClick={(e) => e.stopPropagation()}>
            <button
              onClick={closeModal}
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