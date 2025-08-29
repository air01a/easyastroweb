import { useState, useEffect } from "react";
import Input from '../../design-system/inputs/input'
import Button from "../../design-system/buttons/main";
import { ArrowBigLeft, ArrowBigRight, ArrowLeft, ArrowRight, CameraIcon,  StopCircleIcon } from "lucide-react";
import { apiService } from "../../api/api";
import { useObserverStore } from "../../store/store";

export default function FocusSlider({ onUpdate, loopEnable, disabled }: { onUpdate: () => void , loopEnable: (value: boolean) => void, disabled:boolean }) {
  const [position, setPosition] = useState(25000);
  const [maxPosition, setMaxPosition] = useState(25000);
  const [step, setStep] = useState(50);
  const [isMoving, setIsMoving] = useState<boolean>(false);
  const [isLooping, setIsLooping] = useState<boolean>(false);

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
    <div className="space-y-4 p-4 w-[50%] min-w-100 bg-gray-900 text-white rounded-xl shadow">
      <div>
        <label htmlFor="stretch" className="block mb-1">
          Position: {isMoving ? "moving..." : position}
        </label>

        {isFocuserConnected && (
          <div>
            <div className="flex flex-wrap justify-center items-center mb-4">
              <Button disabled={isMoving||disabled} className="mr-4" onClick={() => handlePositionChange(position - step)}>
                <ArrowBigLeft />
              </Button>
              <Button
                disabled={isMoving||disabled}
                className="mr-4"
                onClick={() => handlePositionChange(position - Math.floor(step / 5))}
              >
                <ArrowLeft />
              </Button>
              <Input disabled={isMoving} type="text" value={position} className="mr-4 text-center" size={5} readOnly />
              <Button
                disabled={isMoving||disabled}
                className="mr-4"
                onClick={() => handlePositionChange(position + Math.floor(step / 5))}
              >
                <ArrowBigRight />
              </Button>
              <Button disabled={isMoving||disabled} className="mr-4" onClick={() => handlePositionChange(position + step)}>
                <ArrowRight />
              </Button>
            </div>

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
              className="w-full"
              disabled={isMoving||disabled}
            />
          </div>
        )}

        <div className="flex items-center justify-center gap-4 mt-4">
          <Button onClick={handleMainButton} disabled={isMoving||disabled}>
            {isLooping ? <StopCircleIcon /> : <CameraIcon />}
          </Button>

          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              className="accent-white"
              checked={loopEnabled}
              onChange={(e) => handleLoop(e.target.checked)}
            />
            <span>Loop</span>
          </label>
        </div>
      </div>



      {isMoving && (
        <div className="flex items-center justify-center">
          <Button onClick={() => halt()}>
            <StopCircleIcon />
          </Button>
        </div>
      )}
    </div>
  );
}
