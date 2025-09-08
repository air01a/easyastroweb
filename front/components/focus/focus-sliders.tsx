import { useState, useEffect } from "react";
import Input from '../../design-system/inputs/input'
import Button from "../../design-system/buttons/main";
import { ArrowBigLeft, ArrowBigRight, ArrowLeft, ArrowRight, CameraIcon,  StopCircleIcon } from "lucide-react";
import { apiService } from "../../api/api";
import { useObserverStore } from "../../store/store";
import { useTranslation } from 'react-i18next';

export default function FocusSlider({ onUpdate, loopEnable, disabled }: { onUpdate: () => void , loopEnable: (value: boolean) => void, disabled:boolean }) {
  const [position, setPosition] = useState(25000);
  const [maxPosition, setMaxPosition] = useState(25000);
  const [step, setStep] = useState(50);
  const [isMoving, setIsMoving] = useState<boolean>(false);
  const [isLooping, setIsLooping] = useState<boolean>(false);
  const { t } = useTranslation();

  // Loop management
  const [loopEnabled, setLoopEnabled] = useState(false);   // Checkbox State

  const { camera, isFocuserConnected } = useObserverStore();

  useEffect(() => {
    const getParams = async () => {
      const currentPosition = await apiService.getFocuserPosition();
      setPosition(currentPosition);
      const maxPosition = await apiService.getMaxFocuser();
      setMaxPosition(maxPosition);
      const step = camera["focuser_step"] ? (camera["focuser_step"] as number) : 50;
      setStep(step);
    };
    getParams();
  }, [camera]);



  const handlePositionChangeSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    setPosition(value);
  };

  const moveFocuser = async (position: number) => {
    const newPosition = await apiService.setFocuserPosition(position);
    setPosition(newPosition);
    setIsMoving(false);
    onUpdate();
  };

  const handlePositionChange = async (position: number) => {
    setIsMoving(true);
    moveFocuser(position);
  };

  const halt = async () => {
    await apiService.focuserHalt();
  };


  const handleMainButton = () => {
    if (isLooping) {
      loopEnable(false);
      setIsLooping(false);
    } else {
      if (loopEnabled) setIsLooping(true);
      onUpdate();
    }

  };



  const handleLoop = (value: boolean) => {
    setLoopEnabled(value);
    loopEnable(value);
  }


  return (
  <div className="space-y-4 p-4 w-[50%] min-w-[400px] bg-gray-900 text-white rounded-xl shadow">
    <div>
      <label htmlFor="stretch" className="block mb-1">
        {t('focuser.position')}: {isMoving ? t('focuser.moving'): position}
      </label>

      {isFocuserConnected && (
        <div>
          {/* Contrôles de position - Responsive */}
          <div className="mb-4">
            {/* Desktop: Une seule ligne */}
            <div className="hidden sm:flex justify-center items-center gap-2">
              <Button 
                disabled={isMoving||disabled} 
                onClick={() => handlePositionChange(position - step)}
                className="flex-shrink-0"
              >
                <ArrowBigLeft />
              </Button>
              <Button
                disabled={isMoving||disabled}
                onClick={() => handlePositionChange(position - Math.floor(step / 5))}
                className="flex-shrink-0"
              >
                <ArrowLeft />
              </Button>
              <Input 
                disabled={isMoving} 
                type="text" 
                value={position} 
                className="text-center mx-2 min-w-0 flex-shrink-0" 
                size={5} 
                readOnly 
              />
              <Button
                disabled={isMoving||disabled}
                onClick={() => handlePositionChange(position + Math.floor(step / 5))}
                className="flex-shrink-0"
              >
                <ArrowRight />
              </Button>
              <Button 
                disabled={isMoving||disabled} 
                onClick={() => handlePositionChange(position + step)}
                className="flex-shrink-0"
              >
                <ArrowBigRight />
              </Button>
            </div>

            {/* Mobile: Disposition en grille */}
            <div className="sm:hidden space-y-3">
              {/* Première ligne: gros déplacements */}
              <div className="flex justify-center items-center gap-4">
                <Button 
                  disabled={isMoving||disabled} 
                  onClick={() => handlePositionChange(position - step)}
                  className="flex-1 max-w-[80px]"
                >
                  <ArrowBigLeft />
                </Button>
                <div className="flex-1 max-w-[100px]">
                  <Input 
                    disabled={isMoving} 
                    type="text" 
                    value={position} 
                    className="text-center w-full" 
                    readOnly 
                  />
                </div>
                <Button 
                  disabled={isMoving||disabled} 
                  onClick={() => handlePositionChange(position + step)}
                  className="flex-1 max-w-[80px]"
                >
                  <ArrowBigRight />
                </Button>
              </div>
              
              {/* Deuxième ligne: petits déplacements */}
              <div className="flex justify-center items-center gap-8">
                <Button
                  disabled={isMoving||disabled}
                  onClick={() => handlePositionChange(position - Math.floor(step / 5))}
                  className="flex-shrink-0"
                >
                  <ArrowLeft />
                </Button>
                <Button
                  disabled={isMoving||disabled}
                  onClick={() => handlePositionChange(position + Math.floor(step / 5))}
                  className="flex-shrink-0"
                >
                  <ArrowRight />
                </Button>
              </div>
            </div>
          </div>

          {/* Slider - Responsive */}
          <div className="mb-4">
            <input
              id="position"
              type="range"
              min="1"
              max={maxPosition}
              step="10"
              value={position}
              onChange={handlePositionChangeSlider}
              onMouseUp={() => handlePositionChange(position)}
              onTouchEnd={() => handlePositionChange(position)}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
              disabled={isMoving||disabled}
            />
          </div>
        </div>
      )}

      {/* Contrôles principaux - Responsive */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-4">
        <Button 
          onClick={handleMainButton} 
          disabled={isMoving||disabled}
          className="w-full sm:w-auto"
        >
          {isLooping ? <StopCircleIcon /> : <CameraIcon />}
        </Button>

        <label className="flex items-center gap-2 cursor-pointer select-none w-full sm:w-auto justify-center">
          <input
            type="checkbox"
            className="accent-white w-4 h-4"
            checked={loopEnabled}
            onChange={(e) => handleLoop(e.target.checked)}
          />
          <span className="text-sm sm:text-base">{t('focuser.loop')}</span>
        </label>
      </div>
    </div>

    {/* Bouton d'arrêt - Centré et responsive */}
    {isMoving && (
      <div className="flex items-center justify-center pt-2">
        <Button 
          onClick={() => halt()}
          className="w-full sm:w-auto bg-red-600 hover:bg-red-700"
        >
          <StopCircleIcon className="mr-2" />
          <span className="sm:hidden">[{t('focuser.stop')}]</span>
        </Button>
      </div>
    )}
  </div>
);
}
