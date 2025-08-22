import { useState, useEffect } from "react";
import Input from '../../design-system/inputs/input'
import Button from "../../design-system/buttons/main";
import { ArrowBigLeft, ArrowBigRight, ArrowLeft, ArrowRight, CameraIcon, StopCircleIcon } from "lucide-react";
import { apiService } from "../../api/api";

export default function FocusSlider( { onUpdate} : {onUpdate :  ()=>void}) {
  const [position, setPosition] = useState(25000);
  const [maxPosition, setMaxPosition] = useState(25000);
  const [isMoving, setIsMoving] = useState<boolean>(false);
 useEffect(() => {

    const getParams = async () => {
            const currentPosition= await apiService.getFocuserPosition();
            setPosition(currentPosition);
            const maxPosition = await apiService.getMaxFocuser();
            setMaxPosition(maxPosition);
    }
    getParams();

 },[]);

  const handlePositionChangeSlider = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    //handlePositionChange(value);
    setPosition(value);

  };

  const moveFocuser = async (position:number) => {
    const newPosition = await apiService.setFocuserPosition(position);
    setPosition(newPosition);
    setIsMoving(false);
    onUpdate();
  }

  const handlePositionChange = async (position: number) => {
    setIsMoving(true);
    moveFocuser(position);

  };
  

  const halt = async () => {
    await apiService.focuserHalt();
  };
  


  return (
    <div className="space-y-4 p-4 w-[50%] min-w-100 bg-gray-900 text-white rounded-xl shadow">
      
      <div>

        <label htmlFor="stretch" className="block mb-1">
          Position: {isMoving}
        </label>
        <div className="flex flex-wrap justify-center align-center mb-4">
            <Button disabled={isMoving} className="mr-4" onClick={() => {handlePositionChange(position-50) }}><ArrowBigLeft/></Button>
            <Button disabled={isMoving}  className="mr-4" onClick={() => {handlePositionChange(position-10) }}><ArrowLeft/></Button>
            <Input  disabled={isMoving}  type="text" value={position} className="mr-4 text-center" size={5} readOnly />
            <Button disabled={isMoving}  className="mr-4"  onClick={() => {handlePositionChange(position+10) }}><ArrowBigRight/></Button>
            <Button disabled={isMoving}  className="mr-4"  onClick={() => {handlePositionChange(position+50) }}><ArrowRight/></Button>
        </div>
        <input
          id="position"
          type="range"
          min="1"
          max={maxPosition}
          step="10"
          value={position}
          onChange={handlePositionChangeSlider}
          onMouseUp={()=> {handlePositionChange(position) }}
          onTouchEnd={()=> {handlePositionChange(position) }}
          className="w-full"
          disabled={isMoving} 
        />
        <div className="flex justify-center"><Button onClick={onUpdate} disabled={isMoving} ><CameraIcon /></Button></div>
      </div>
      {isMoving && (
        <div className="flex align-center justify-center"><Button onClick={()=>halt()}><StopCircleIcon/></Button></div>
      )}
    </div>
  );
}
