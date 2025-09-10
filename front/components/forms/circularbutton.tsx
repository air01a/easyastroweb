import React, { useState, useEffect } from 'react';

interface CircularButtonSelectionProps {
  name: string;
  callBack?: (name: string, values: boolean[]) => void;
  selectedButtons: boolean[];
  editable?: boolean;
  miniature?: boolean;
}

const CircularButtonSelection: React.FC<CircularButtonSelectionProps> = ({
  name,
  callBack,
  selectedButtons: initialSelectedButtons,
  editable = true,
  miniature = false
}) => {
  const [selectedButtons, setSelectedButtons] = useState<boolean[]>(initialSelectedButtons);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragAction, setDragAction] = useState<'select' | 'deselect' | null>(null);

  useEffect(() => {
    setSelectedButtons(initialSelectedButtons);
  }, [initialSelectedButtons]);


  const handleMouseDown = (index: number) => {
    if (!editable) return;
    
    setIsDragging(true);
    const newValue = !selectedButtons[index];
    setDragAction(newValue ? 'select' : 'deselect');
    
    // Appliquer l'action sur le premier élément
    setSelectedButtons(prev => {
      const newState = [...prev];
      newState[index] = newValue;
      if (callBack) callBack(name, newState);
      return newState;
    });
  };

  const handleMouseEnter = (index: number) => {
    setHoveredIndex(index);
    
    if (isDragging && dragAction && editable) {
      const targetValue = dragAction === 'select';
      
      setSelectedButtons(prev => {
        const newState = [...prev];
        // Seulement changer si l'état est différent de celui souhaité
        if (newState[index] !== targetValue) {
          newState[index] = targetValue;
          if (callBack) callBack(name, newState);
        }
        return newState;
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragAction(null);
  };

  const handleMouseLeave = () => {
    setHoveredIndex(null);
  };

  // Gérer les événements globaux pour le mouseup
  useEffect(() => {
    const handleGlobalMouseUp = () => {
      setIsDragging(false);
      setDragAction(null);
    };

    if (isDragging) {
      document.addEventListener('mouseup', handleGlobalMouseUp);
      document.addEventListener('touchend', handleGlobalMouseUp);
      
      return () => {
        document.removeEventListener('mouseup', handleGlobalMouseUp);
        document.removeEventListener('touchend', handleGlobalMouseUp);
      };
    }
  }, [isDragging]);

  const getLabel = (index: number): string => {
    switch (index) {
      case 0: return "N";
      case 9: return "E";
      case 18: return "S";
      case 27: return "W";
      default: return (index * 10).toString();
    }
  };

  // Fonction pour créer un path d'arc SVG
  const createArcPath = (centerX: number, centerY: number, radius: number, startAngle: number, endAngle: number): string => {
    const start = polarToCartesian(centerX, centerY, radius, endAngle);
    const end = polarToCartesian(centerX, centerY, radius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
    
    return [
      "M", start.x, start.y, 
      "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
    ].join(" ");
  };

  // Fonction pour créer un secteur circulaire (pour les zones de clic)
  const createSectorPath = (centerX: number, centerY: number, innerRadius: number, outerRadius: number, startAngle: number, endAngle: number): string => {
    const startInner = polarToCartesian(centerX, centerY, innerRadius, startAngle);
    const endInner = polarToCartesian(centerX, centerY, innerRadius, endAngle);
    const startOuter = polarToCartesian(centerX, centerY, outerRadius, startAngle);
    const endOuter = polarToCartesian(centerX, centerY, outerRadius, endAngle);
    
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
    
    return [
      "M", startInner.x, startInner.y,
      "L", startOuter.x, startOuter.y,
      "A", outerRadius, outerRadius, 0, largeArcFlag, 0, endOuter.x, endOuter.y,
      "L", endInner.x, endInner.y,
      "A", innerRadius, innerRadius, 0, largeArcFlag, 1, startInner.x, startInner.y,
      "z"
    ].join(" ");
  };

  const polarToCartesian = (centerX: number, centerY: number, radius: number, angleInDegrees: number) => {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
    return {
      x: centerX + (radius * Math.cos(angleInRadians)),
      y: centerY + (radius * Math.sin(angleInRadians))
    };
  };

  // Grouper les segments consécutifs sélectionnés
  const getSelectedArcs = () => {
    const arcs = [];
    let currentArc = null;
    
    for (let i = 0; i < selectedButtons.length; i++) {
      if (selectedButtons[i]) {
        if (currentArc === null) {
          currentArc = { start: i, end: i };
        } else {
          currentArc.end = i;
        }
      } else {
        if (currentArc !== null) {
          arcs.push(currentArc);
          currentArc = null;
        }
      }
    }
    
    if (currentArc !== null) {
      arcs.push(currentArc);
    }
    
    // Gérer le cas où la sélection traverse 0° (N) SEULEMENT si on a exactement 2 arcs
    // et que le premier commence à 0 et le dernier finit à 35
    if (arcs.length === 2 && 
        arcs[0].start === 0 && 
        arcs[arcs.length - 1].end === selectedButtons.length - 1) {
      
      // Vérifier qu'il n'y a pas d'éléments non-sélectionnés entre les deux arcs
      let hasGapBetweenArcs = false;
      for (let i = arcs[0].end + 1; i < arcs[1].start; i++) {
        if (!selectedButtons[i]) {
          hasGapBetweenArcs = true;
          break;
        }
      }
      
      // Seulement fusionner si il n'y a pas de gap entre les arcs
      if (!hasGapBetweenArcs) {
        const firstArc = arcs.shift()!;
        const lastArc = arcs.pop()!;
        arcs.push({
          start: lastArc.start,
          end: firstArc.end + selectedButtons.length
        });
      }
    }
    
    return arcs;
  };

  const size = miniature ? 200 : 400;
  const center = size / 2;
  const radius = miniature ? 80 : 160;
  const strokeWidth = miniature ? 8 : 20;
  const labelRadius = radius + (miniature ? 20 : 30);
  const clickInnerRadius = radius - (miniature ? 30 : 50);
  const clickOuterRadius = radius + (miniature ? 30 : 50);

  return (
    <div 
      className={`flex items-center justify-center ${miniature ? "min-h-20 min-w-20" : "min-h-50 min-w-50"}`}
      style={{ userSelect: 'none' }}
    >
      <div className="relative">
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Cercle de fond */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#ef4444"
            strokeWidth={strokeWidth}
            opacity={0.3}
          />
          
          {/* Arcs sélectionnés */}
          {getSelectedArcs().map((arc, index) => {
            const startAngle = arc.start * 10;
            const endAngle = (arc.end + 1) * 10;
            
            // Cas spécial : si tout est sélectionné, dessiner un cercle complet
            if (arc.start === 0 && arc.end >= 35) {
              return (
                <circle
                  key={index}
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="none"
                  stroke="#22c55e"
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                />
              );
            }
            
            const actualEndAngle = arc.end >= 36 ? (arc.end - 36 + 1) * 10 + 360 : endAngle;
            
            if (actualEndAngle > 360) {
              // Diviser l'arc qui traverse 0°
              return (
                <g key={index}>
                  <path
                    d={createArcPath(center, center, radius, startAngle, 360)}
                    fill="none"
                    stroke="#22c55e"
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                  />
                  <path
                    d={createArcPath(center, center, radius, 0, actualEndAngle - 360)}
                    fill="none"
                    stroke="#22c55e"
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                  />
                </g>
              );
            }
            
            return (
              <path
                key={index}
                d={createArcPath(center, center, radius, startAngle, actualEndAngle)}
                fill="none"
                stroke="#22c55e"
                strokeWidth={strokeWidth}
                strokeLinecap="round"
              />
            );
          })}
          
          {/* Segment survolé */}
          {hoveredIndex !== null && (
            <path
              d={createArcPath(center, center, radius, hoveredIndex * 10, (hoveredIndex + 1) * 10)}
              fill="none"
              stroke={selectedButtons[hoveredIndex] ? "#16a34a" : "#dc2626"}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              opacity={0.7}
            />
          )}

          {/* Secteurs invisibles pour les clics - MAINTENANT AU-DESSUS */}
          {Array.from({ length: 36 }, (_, index) => {
            const startAngle = index * 10;
            const endAngle = (index + 1) * 10;
            
            return (
              <path
                key={`click-${index}`}
                d={createSectorPath(center, center, clickInnerRadius, clickOuterRadius, startAngle, endAngle)}
                fill="transparent"
                style={{ 
                  cursor: editable ? 'pointer' : 'default',
                  userSelect: 'none',
                  pointerEvents: 'all'
                }}
                onMouseDown={() => handleMouseDown(index)}
                onMouseEnter={() => handleMouseEnter(index)}
                onMouseLeave={handleMouseLeave}
                onMouseUp={handleMouseUp}
                onTouchStart={() => handleMouseDown(index)}
                onTouchMove={(e) => {
                  // Gérer le touch move pour les appareils tactiles
                  const touch = e.touches[0];
                  const element = document.elementFromPoint(touch.clientX, touch.clientY);
                  const pathElement = element?.closest('path[data-index]');
                  if (pathElement) {
                    const touchIndex = parseInt(pathElement.getAttribute('data-index') || '0');
                    handleMouseEnter(touchIndex);
                  }
                }}
                data-index={index}
              />
            );
          })}
        </svg>
        
        {/* Labels */}
        {!miniature && Array.from({ length: 36 }, (_, index) => {
          // Afficher seulement les labels principaux et quelques intermédiaires
          if (index % 3 !== 0) return null;
          
          const angle = index * 10 - 90;
          const radian = (angle * Math.PI) / 180;
          const x = labelRadius * Math.cos(radian);
          const y = labelRadius * Math.sin(radian);
          
          return (
            <div
              key={`label-${index}`}
              className="absolute text-xs font-medium text-gray-600 pointer-events-none text-white"
              style={{
                left: '50%',
                top: '50%',
                transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`
              }}
            >
              {getLabel(index)}
            </div>
          );
        })}
        
        {/* Centre avec indicateur */}
        <div 
          className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 
                     w-4 h-4 bg-gray-300 rounded-full border-2 border-white shadow-sm"
        />
      </div>
    </div>
  );
};

export default CircularButtonSelection;