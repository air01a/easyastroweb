import { useEffect, useState } from "react";
import { apiService } from "../../api/api";

import { X } from "lucide-react";
import ImageBox from "../../design-system/box/imagebox";
import { useTranslation } from 'react-i18next';
import FocusSlider from "../../components/image-settings/focus-sliders"
import LoadingIndicator from "../../design-system/messages/loadingmessage";
import { useConfigStore } from "../../store/store";


export default function FocusHelper() {
  const [image1, setImage1] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const  getItem  = useConfigStore((state) => state.getItem);
  const { t } = useTranslation();
//focuser_exposition


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
        body:JSON.stringify({ exposition :getItem("focuser_exposition")}) 
    })
      .then((res) => res.blob())
      .then((blob) => {
        const newImageUrl = URL.createObjectURL(blob);
        setImage1(newImageUrl);
        setIsLoading(false);

      });
  };

  useEffect(() => {
    fetchImages();
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
        <FocusSlider onUpdate={captureImage}/>


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