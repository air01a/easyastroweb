import { useState, useEffect } from "react";
import Input from '../../design-system/inputs/input'
import Button from "../../design-system/buttons/main";
import { ArrowBigLeft, ArrowBigRight, ArrowLeft, ArrowRight } from "lucide-react";
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
    handlePositionChange(value);

  };

  const moveFocuser = async (position:number) => {
    await apiService.setFocuserPosition(position);
    setPosition(position);

    setIsMoving(false);
  }

  const handlePositionChange = (position: number) => {
    setIsMoving(true);
    moveFocuser(position);
  };
  



  const sendValues = async () => {
    onUpdate();
  }


  return (
    <div className="space-y-4 p-4 w-[50%] min-w-100 bg-gray-900 text-white rounded-xl shadow">
      
      <div>

        <label htmlFor="stretch" className="block mb-1">
          Position: {isMoving}
        </label>
        <div className="flex flex-wrap justify-center align-center mb-4">
            <Button disabled={isMoving} className="mr-4" onClick={() => {handlePositionChange(position-50) }}><ArrowBigLeft/></Button>
            <Button disabled={isMoving}  className="mr-4" onClick={() => {handlePositionChange(position-10) }}><ArrowLeft/></Button>
            <Input  disabled={isMoving}  type="text" value={position} className="mr-4"/>
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
          onMouseUp={sendValues}
          onTouchEnd={sendValues}
          className="w-full"
          disabled={isMoving} 
        />
      </div>
    </div>
  );
}
