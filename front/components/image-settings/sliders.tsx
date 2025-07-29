import { useState, useEffect } from "react";
import { apiService } from "../../api/api";

export default function ImageSettingsSliders( { onUpdate} : {onUpdate :  ()=>void}) {
  const [stretch, setStretch] = useState(1);
  const [blackPoint, setBlackPoint] = useState(0);

 useEffect(() => {

    const getParams = async () => {
            const imageSettings = await apiService.getImageSettings();
            setStretch(Math.round(imageSettings.stretch*100));
            setBlackPoint(imageSettings.black_point)
    }
    getParams();

 },[]);

  const handleStretchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseFloat(e.target.value);
    setStretch(value);
  };

  const handleBlackPointChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value);
    setBlackPoint(value);
  };

  const sendValues = async () => {
    await apiService.setImageSettings(stretch/100, blackPoint);
    onUpdate();
  }

  const stretchFloat = stretch / 100;

  return (
    <div className="space-y-4 p-4 w-[50%] min-w-100 bg-gray-900 text-white rounded-xl shadow">
      <div>
        <label htmlFor="stretch" className="block mb-1">
          Stretch: {stretchFloat.toFixed(2)}
        </label>
        <input
          id="stretch"
          type="range"
          min="5"
          max="400"
          step="1"
          value={stretch}
          onChange={handleStretchChange}
          onMouseUp={sendValues}
          onTouchEnd={sendValues}
          className="w-full"
        />
      </div>

      <div>
        <label htmlFor="backPoint" className="block mb-1">
          Point noir: {blackPoint}
        </label>
        <input
          id="backPoint"
          type="range"
          min="0"
          max="100"
          step="1"
          value={blackPoint}
          onChange={handleBlackPointChange}
         onMouseUp={sendValues}
          onTouchEnd={sendValues}
          className="w-full"
        />
      </div>
    </div>
  );
}
