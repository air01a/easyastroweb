import { useEffect, useState } from "react";
import { apiService } from "../../api/api";
import Button from "../../design-system/buttons/main";
import Swal from "sweetalert2";
import { X, LoaderCircle } from "lucide-react"; // icône animée de statut
import { useWebSocketStore } from "../../store/store";

export default function RunningPlanPage({ refresh }: { refresh: () => void }) {
  const [image1, setImage1] = useState<string | null>(null);
  const [image2, setImage2] = useState<string | null>(null);
  const [modalImage, setModalImage] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>("En attente d’instructions...");
  
  const connect = useWebSocketStore((state) => state.connect);
  const messages = useWebSocketStore((state) => state.messages);
  const isConnected = useWebSocketStore((state) => state.isConnected);

  const fetchImages = () => {
    const baseUrl = apiService.getBaseUrl();
    const timestamp = Date.now();

    fetch(`${baseUrl}/observation/last_stacked_image?t=${timestamp}`)
      .then((res) => res.blob())
      .then((blob) => setImage1(URL.createObjectURL(blob)));

    fetch(`${baseUrl}/observation/last_image?t=${timestamp}`)
      .then((res) => res.blob())
      .then((blob) => setImage2(URL.createObjectURL(blob)));
  };

  useEffect(() => {
    fetchImages();
    if (!isConnected) {
      connect();
    }
  }, [connect, isConnected]);

  useEffect(() => {
    const newMessage = messages[messages.length - 1];
    if (!newMessage) return;

    if (newMessage.sender === "SCHEDULER") {
      if (newMessage.message === "NEWIMAGE") {
        fetchImages();
      } else if (newMessage.message === "STATUS") {
        setJobStatus(newMessage.data as string|| "Statut inconnu");
      }
    }
  }, [messages]);

  const handleClick = () => {
    Swal.fire({
      title: "Are you sure?",
      text: "You won't be able to revert this!",
      icon: "warning",
      showCancelButton: true,
      confirmButtonColor: "#3085d6",
      cancelButtonColor: "#d33",
      confirmButtonText: "Yes, stop it!",
    }).then((result) => {
      if (result.isConfirmed) {
        apiService.stopPlan();
        refresh();
      }
    });
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 space-y-6">
      
      {/* ✅ Encart de statut visible en permanence */}
      <div className="w-full max-w-4xl bg-blue-50 text-blue-800 border border-blue-200 rounded-md px-4 py-3 flex items-center gap-3 shadow-sm">
        <LoaderCircle className="animate-spin w-5 h-5" />
        <p className="text-sm font-medium">{jobStatus}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl">
        {image1 && (
          <div className="flex flex-col items-center w-full">
            <div
              className="w-full h-64 border rounded overflow-hidden bg-black cursor-pointer"
              onClick={() => setModalImage(image1)}
            >
              <img
                src={image1}
                alt="Last stacked"
                className="w-full h-full object-cover"
              />
            </div>
            <p className="mt-2 text-center text-sm text-gray-600">Last stacked image</p>
          </div>
        )}
        {image2 && (
          <div className="flex flex-col items-center w-full">
            <div
              className="w-full h-64 border rounded overflow-hidden bg-black cursor-pointer"
              onClick={() => setModalImage(image2)}
            >
              <img
                src={image2}
                alt="Last taken"
                className="w-full h-full object-cover"
              />
            </div>
            <p className="mt-2 text-center text-sm text-gray-600">Last image taken</p>
          </div>
        )}
      </div>

      <div>
        <Button onClick={handleClick}>Stop plan</Button>
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
