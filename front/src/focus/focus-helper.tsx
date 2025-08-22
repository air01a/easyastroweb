import { useEffect, useState } from "react";
import { apiService } from "../../api/api";

import { X, LoaderCircle } from "lucide-react";
import { useWebSocketStore } from "../../store/store";
import ImageBox from "../../design-system/box/imagebox";
import { useTranslation } from 'react-i18next';
import FocusSlider from "../../components/image-settings/focus-sliders"

export default function FocusHelper() {
  const [image1, setImage1] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const [modalImageType, setModalImageType] = useState<'image1' | 'image2' | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("En attente d'instructions...");
  const { t } = useTranslation();

  const connect = useWebSocketStore((state) => state.connect);
  const messages = useWebSocketStore((state) => state.messages);
  const isConnected = useWebSocketStore((state) => state.isConnected);

  const fetchImages = async () => {
    const baseUrl = apiService.getBaseUrl();
    const timestamp = Date.now();

    fetch(`${baseUrl}/observation/last_image?t=${timestamp}`)
      .then((res) => res.blob())
      .then((blob) => {
        const newImageUrl = URL.createObjectURL(blob);
        setImage1(newImageUrl);
        // Mettre à jour la modal si elle affiche image2
        if (modalImageType === 'image2') {
          setModalImage(newImageUrl);
        }
      });
  };

  useEffect(() => {
    fetchImages();
    if (!isConnected) connect();
  }, []);

  useEffect(() => {
    const newMessage = messages[messages.length - 1];
    if (!newMessage) return;
    if (newMessage.sender === "SCHEDULER") {
      if (newMessage.message === "NEWIMAGE") {
        fetchImages();
      } else if (newMessage.message === "STATUS") {
        setJobStatus((newMessage.data as string) || t("plan.unknown_status"));
      }  else if (newMessage.message === "TEMPERATURE") {
        setJobStatus(`${t("plan.temperature")} [${newMessage.data}]`);
      }
    }
  }, [messages]);

  

  const openModal = (imageUrl: string, imageType: 'image1' | 'image2') => {
    setModalImage(imageUrl);
    setModalImageType(imageType);
  };

  const closeModal = () => {
    setModalImage(null);
    setModalImageType(null);
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 space-y-6">
      {/* STATUT */}
      <div className="w-full max-w-4xl bg-blue-50 text-blue-800 border border-blue-200 rounded-md px-4 py-3 flex items-center gap-3 shadow-sm">
        {jobStatus!="finished" && (<LoaderCircle className="animate-spin w-5 h-5" />)}
        <p className="text-sm font-medium">{jobStatus}</p>
      </div>

      {/* IMAGES EN COURS */}
      <div className="flex flex-wrap gap-6 h-[40%]">
        {image1 && (
          <ImageBox
            src={image1}
            label="Last stacked image"
            onClick={() => openModal(image1, 'image1')}
            className={'max-h-[50vh] max-w-full h-auto w-auto object-contain'}
          />
        )}
        
      </div>
        <FocusSlider onUpdate={fetchImages}/>


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