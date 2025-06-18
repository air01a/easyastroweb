import React, { useEffect, useState } from "react";
import { CheckCircle, AlertTriangle, Info, X } from "lucide-react";
import classNames from "classnames";

type MessageType = "success" | "error" | "info";

interface FlashMessageProps {
  type: MessageType;
  message: string;
  duration?: number; // en ms (par défaut : 3000)
  onClose?: () => void;
}

const icons = {
  success: <CheckCircle className="text-green-600" />,
  error: <AlertTriangle className="text-red-600" />,
  info: <Info className="text-blue-600" />,
};

export const FlashMessage: React.FC<FlashMessageProps> = ({ type, message, duration = 3000, onClose }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      if (onClose) onClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!visible) return null;

  return (
    <div
      className={classNames(
        "flex items-center gap-3 rounded-lg border p-4 shadow-md w-fit animate-fade-in-out transition-opacity duration-500",
        {
          "bg-green-50 border-green-200": type === "success",
          "bg-red-50 border-red-200": type === "error",
          "bg-blue-50 border-blue-200": type === "info",
        }
      )}
    >
      <div>{icons[type]}</div>
      <span className="text-sm text-gray-800">{message}</span>
      <button onClick={() => { setVisible(false); if (onClose) onClose(); }} className="ml-4 text-gray-500 hover:text-gray-700">
        <X size={16} />
      </button>
    </div>
  );
};

export default FlashMessage;
