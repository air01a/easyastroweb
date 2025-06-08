import React, { useEffect, useRef } from "react";
// Si skymap est un module npm (adapter l'import selon la doc)
import SkyMap from "skymap";

const SkyMapComponent: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialiser la carte dans le container
    // Exemple basé sur une API générique, adapter selon la doc skymap
    const sky = new SkyMap(containerRef.current, {
      // options ici, par exemple :
      width: 600,
      height: 600,
      // ... autres options
    });

    // Démarrer ou dessiner la carte
    sky.draw();

    // Cleanup (si applicable)
    return () => {
      sky.destroy?.();
    };
  }, []);

  return <div ref={containerRef} />;
};

export default SkyMapComponent;
