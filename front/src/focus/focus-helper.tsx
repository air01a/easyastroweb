import { useEffect, useRef, useState } from "react";
import { apiService } from "../../api/api";

import { Focus, StopCircleIcon, X  } from "lucide-react";
import ImageBox from "../../design-system/box/imagebox";
import { useTranslation } from 'react-i18next';
import FocusSlider from "../../components/focus/focus-sliders"
import LoadingIndicator from "../../design-system/messages/loadingmessage";
import { useConfigStore, useObserverStore } from "../../store/store";
import ServiceUnavailable from "../../design-system/messages/service-unavailable"
import type  { FwhmResults,  FhwmType } from "../../types/api.type";
import Button from "../../design-system/buttons/main";
import { useWebSocketStore } from "../../store/store";
import FwhmChart from "../../components/focus/focus-graph";
import ExposureTimeInput from "../../components/exposure/expo";

export default function FocusHelper() {
  const [image1, setImage1] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const { isConnected } = useObserverStore(); 
  const  getItem  = useConfigStore((state) => state.getItem);
  const { t } = useTranslation();
  const [loopEnabled, setLoopEnabled] = useState<boolean>(false);
  const [fwhm, setFwhm] = useState<FhwmType>(null);
  const [fwhmLoading, setFwhmLoading] = useState<boolean>(false);
  const [fwhmResults, setFwhmResults] = useState<FwhmResults|null>()
  const [isAutofocusRunning, setIsAutoFocusRunning] = useState<boolean>(false);
  const connect = useWebSocketStore((state) => state.connect);
  const isWebSocketConnected = useWebSocketStore((state) => state.isConnected);
  //const {camera} = useObserverStore();
  const [exposure, setExposure] = useState<number>(getItem("focuser_exposition") as number);

  const messages = useWebSocketStore((state) => state.messages);
  const loopEnabledRef = useRef(loopEnabled);
  useEffect(() => { loopEnabledRef.current = loopEnabled; }, [loopEnabled]);
  const lastMessageRef = useRef<number | null>(null);

    useEffect(() => {
        if (!isWebSocketConnected) connect();
      }, [isWebSocketConnected, connect]);


    useEffect(() => {
       const refreshOnMessage = async () => {
       if (messages.length === lastMessageRef.current)  return;

        lastMessageRef.current = messages.length;
        const newMessage = messages[messages.length - 1];
        if (!newMessage) return;
        if (newMessage.sender === "FOCUSER") {
          if (newMessage.message === "NEWIMAGE") {
            const results = await apiService.getFocus();

            setFwhmResults(results);
            if (results && results[1].best_position) {
              setBinning();
              setIsAutoFocusRunning(false);
            } 
          }
        }
        }
        refreshOnMessage();
      }, [messages, t]);

  const loadFwhm = async() => {
    setFwhmLoading(true);
    apiService.getFhwm()
      .then((result) => {
        setFwhm(result);
        setFwhmLoading(false);
      });
  }


  const fetchImages = async () => {
    const baseUrl = apiService.getBaseUrl();
    const timestamp = Date.now();
    setIsLoading(true);
    fetch(`${baseUrl}/observation/capture?t=${timestamp}`, { 
        headers: {
            "Content-Type": "application/json",
            "accept": "application/json"
        },
        method:"POST", 
        body:JSON.stringify({ exposition :exposure}) 
    })
      .then((res) => res.blob())
      .then((blob) => {
        const newImageUrl = URL.createObjectURL(blob);
        setImage1(newImageUrl);
        setIsLoading(false);
        loadFwhm();
        if (loopEnabledRef.current) fetchImages();
        
      });
  };

  const setBinning = async () => {
    //if (camera?.binx_focuser!==1) await apiService.setBinX(camera.binx_focuser as number)
    //if (camera?.biny_focuser!==1) await apiService.setBinY(camera.biny_focuser as number)
  }

  useEffect(() => {
    if (isConnected) fetchImages();
    setBinning();

  }, []);

  const captureImage = async () => {
    fetchImages();
  }

  

  const openModal = (imageUrl: string) => {
    setModalImage(imageUrl);
  };

  const closeModal = () => {
    setModalImage(null);
  };


  const handleAutofocus = async () => {
    if (isAutofocusRunning) {
      apiService.stopPlan();
      setIsAutoFocusRunning(false);
      return ;
    }
    setLoopEnabled(false);
    setIsAutoFocusRunning(true);
    apiService.startAutoFocus();
    

  };


  if (isConnected) {
    const formattedFwhm = fwhm?.fwhm != null ? (fwhm.fwhm as number).toFixed(2) : 'N/A';
    return (
    <div className="flex flex-col items-center justify-center p-4 space-y-6">

      {/* IMAGES EN COURS */}
      <div className="flex flex-wrap gap-6 h-[40%]">
        {image1 && (
          <ImageBox
            src={image1}
            label=""
            onClick={() => openModal(image1)}
            className={'max-h-[50vh] max-w-full h-auto w-auto object-contain'}
          />
        )}
       
      </div>
      {(isLoading) && <LoadingIndicator text={t("global.loading")}/>}
      {( fwhmResults) && (
        <div className="w-[50%] "><FwhmChart data={fwhmResults} /></div>
      )}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">FWHM:</span>
        {fwhmLoading && ! isAutofocusRunning? (
          // petit loader inline
          <span
            className="inline-block h-4 w-4 border-2 border-white/70 border-t-transparent rounded-full animate-spin"
            aria-label={t("global.loading")}
          />
        ) : (
          <span className="font-mono">{formattedFwhm}</span>
        )}
      </div>
       <FocusSlider onUpdate={captureImage} loopEnable={setLoopEnabled} disabled={isAutofocusRunning} />
        <ExposureTimeInput
          value={exposure}
          onChange={setExposure}
          min={1}
          max={10}
        />
       <div className="flex items-center justify-center gap-4 mt-4">
          <Button onClick={handleAutofocus} >
            {isAutofocusRunning ? <StopCircleIcon /> : <div className="flex flex-col justify-center items-center">{t('focuser.startAutofocus')}<Focus /></div>}
          </Button>
          </div>

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
  } else {
    return (<ServiceUnavailable />)
  }
}