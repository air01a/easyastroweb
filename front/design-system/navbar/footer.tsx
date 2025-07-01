import { useObserverStore } from "../..//store/store"
import { MapPin, Telescope, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { ObservatoryCard } from "../../components/observatory/observatoryCard";
import Button from "../buttons/main";
import { TelescopeCard } from "../../components/observatory/telescopeCard";

export default function Footer() {
    const {observatory, telescope}= useObserverStore();
    const [openMenu, setOpenMenu] = useState<"observatory" | "telescope" | null>(null);
    const navigate = useNavigate();
    const toggleMenu = (menu: "observatory" | "telescope") => {
        setOpenMenu(openMenu === menu ? null : menu);

    }
    const telescopeName = telescope.name;
    const observatoryName = observatory.name; 



    return (
       <footer className="relative w-full bg-gray-800 text-white py-3 px-4 flex items-center justify-between">
      {/* Observatoire */}
      <div className="relative">
        <button
          onClick={() => toggleMenu("observatory")}
          className="flex items-center space-x-2 hover:text-blue-300"
        >
          <MapPin className="w-5 h-5 text-blue-400" />
          <span className="text-sm">
            Site sélectionné: <strong>{observatoryName || "Aucun"}</strong>
          </span>
        </button>
        {openMenu === "observatory" && (
            <div
              className="
                z-50
                fixed inset-10
                bg-white text-gray-800
                p-8
                flex flex-col
                md:absolute md:inset-auto md:bottom-full md:mb-2 md:left-0
                md:rounded md:shadow-lg md:w-64
              "
            >
              {/* Barre de titre */}
              <div className="flex justify-between items-center mb-4 md:mb-2">
                <h4 className="font-semibold">Détails du site</h4>
                <button onClick={() => setOpenMenu(null)}>
                  <X className="w-10 h-10 md:w-5 md:h-5" />
                </button>
              </div>

              {/* Contenu */}
              <div className="flex flex-col flex-1 justify-center items-center space-y-4 md:justify-start">
                <ObservatoryCard item={observatory}/>
                <Button
                  onClick={() => {
                    navigate("/config/telescopes");
                    setOpenMenu(null);
                  }}
                  className="text-blue-600 hover:underline text-sm"
                >
                  Changer de télescope
                </Button>
              </div>
            </div>
          )}


      </div>

      {/* Télescope */}
      <div className="relative">
        <button
          onClick={() => toggleMenu("telescope")}
          className="flex items-center space-x-2 hover:text-green-300"
        >
          <Telescope className="w-5 h-5 text-green-400" />
          <span className="text-sm">
            Télescope sélectionné: <strong>{telescopeName || "Aucun"}</strong>
          </span>
        </button>

        {openMenu === "telescope" && (
            <div
              className="
                z-50
                fixed inset-0
                bg-white text-gray-800
                p-4
                flex flex-col
                md:absolute md:inset-auto md:bottom-full md:mb-2 md:right-0
                md:rounded md:shadow-lg md:w-64
              "
            >
              {/* Barre de titre */}
              <div className="flex justify-between items-center mb-4 md:mb-2">
                <h4 className="font-semibold">Détails du télescope</h4>
                <button onClick={() => setOpenMenu(null)}>
                  <X className="w-10 h-10 md:w-5 md:h-5" />
                </button>
              </div>

              {/* Contenu */}
              <div className="flex flex-col flex-1 justify-center items-center space-y-4 md:justify-start">
                <TelescopeCard item={telescope} />
                <Button
                  onClick={() => {
                    navigate("/config/telescopes");
                    setOpenMenu(null);
                  }}
                  className="text-blue-600 hover:underline text-sm"
                >
                  Changer de télescope
                </Button>
              </div>
            </div>
          )}

      </div>
    </footer>
  );
}
