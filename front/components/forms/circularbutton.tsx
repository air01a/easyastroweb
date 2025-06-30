import React, { useState, useEffect } from 'react';

interface CircularButtonProps {
  isSelected: boolean;
  onTap: () => void;
  label: string;
}

const CircularButton: React.FC<CircularButtonProps> = ({ isSelected, onTap, label }) => {
  return (
    <div
      onClick={onTap}
      className={`
        w-9 h-9 rounded-full flex items-center justify-center cursor-pointer
        ${isSelected ? 'bg-green-500' : 'bg-red-500'}
        text-white text-xs font-medium
        hover:opacity-80 transition-opacity
      `}
    >
      {label}
    </div>
  );
};

interface CircularButtonSelectionProps {
  name: string;
  callBack?: (name: string, values: boolean[]) => void;
  selectedButtons: boolean[];
  editable?: boolean ;
  miniature? : boolean;
}

const CircularButtonSelection: React.FC<CircularButtonSelectionProps> = ({
  name,
  callBack,
  selectedButtons: initialSelectedButtons,
  editable = true,
  miniature = false
}) => {
  const [selectedButtons, setSelectedButtons] = useState<boolean[]>(initialSelectedButtons);

  useEffect(() => {
    setSelectedButtons(initialSelectedButtons);
  }, [initialSelectedButtons]);

  const toggleButton = (index: number) => {
    setSelectedButtons(prev => {
      const newState = [...prev];
      newState[index] = !newState[index];
      if (callBack) callBack(name, newState);
      return newState;
    });
  };

  const getLabel = (index: number): string => {
    switch (index) {
      case 0: return "N";
      case 9: return "E";
      case 18: return "S";
      case 27: return "W";
      default: return (index * 10).toString();
    }
  };

  return (
    <div className={`flex items-center justify-center ${miniature ? "min-h-20 min-w-20": "min-h-50 min-w-50"}`}>
      <div className={`relative ${miniature?"w-[200px] h-[200px]": "w-[400px] h-[420px]"}`}>
        {Array.from({ length: 36 }, (_, index) => {
          const angle = index * 10 - 90; // Adjusting angle for compass orientation
          const radius = miniature? 80 : 160;
          const radian = (angle * Math.PI) / 180;
          
          const x = radius * Math.cos(radian);
          const y = radius * Math.sin(radian);
          
          return (
            <div
              key={index}
              className="absolute"
              style={{
                left: '50%',
                top: '50%',
                transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`
              }}
            >
              <CircularButton
                isSelected={selectedButtons[index]}
                onTap={() => {
                  if (editable) toggleButton(index);

                  }
                }
                label={miniature? '' : getLabel(index)}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default CircularButtonSelection;