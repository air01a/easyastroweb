import { useEffect, useRef } from "react";

type SidePanelProps = {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
};

export default function ResizableSidePanel({ isOpen, onClose, children }: SidePanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const isResizingRef = useRef(false);

  // Fermer sur clic extérieur ou Escape
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  // Redimensionnement
  /*useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isResizingRef.current) {
        const newWidth = Math.min(Math.max(e.clientX, 300), window.innerWidth * 0.9); // min 300px, max 90vw
        setWidth(newWidth);
      }
    };

    const stopResizing = () => {
      isResizingRef.current = false;
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", stopResizing);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, []);*/

  if (!isOpen) return null;

  return (
        <div
      ref={panelRef}
      className={`fixed top-0 right-0 h-full z-50 w-full md:w-[60%] transition-transform duration-300 bg-black text-white shadow-lg overflow-y-auto ${
        isOpen ? "translate-x-0" : "-translate-x-full "
      }`}

    >
      {/* Bouton de fermeture */}
      <button
        className="fixed top-4 right-6 text-2xl font-bold z-50 text-white "
        onClick={onClose}
      >
        ✕
      </button>

      {/* Contenu scrollable, prend toute la place */}
      <div className="flex-1 bg-black overflow-y-auto pt-16 px-4 w-full">
        <div className="w-full h-full">{children}</div>
      </div>

      {/* Barre de redimensionnement */}
      <div
        className="absolute top-0 right-0 h-full w-2 cursor-ew-resize z-50"
        onMouseDown={() => (isResizingRef.current = true)}
      />
    </div>
  );
}
