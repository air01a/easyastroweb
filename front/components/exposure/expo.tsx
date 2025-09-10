import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface ExposureTimeInputProps {
  value: number; // temps en secondes
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  className?: string;
}

const ExposureTimeInput: React.FC<ExposureTimeInputProps> = ({
  value,
  onChange,
  min = 1,
  max = 3600,
  className = ''
}) => {
  const { t } = useTranslation();

  const [isChanging, setIsChanging] = useState(false);

  // Formater l'affichage du temps
  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return remainingSeconds > 0 
        ? `${minutes}m ${remainingSeconds}s`
        : `${minutes}m`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainingSeconds = seconds % 60;
      let result = `${hours}h`;
      if (minutes > 0) result += ` ${minutes}m`;
      if (remainingSeconds > 0) result += ` ${remainingSeconds}s`;
      return result;
    }
  };

  const animateChange = () => {
    setIsChanging(true);
    setTimeout(() => setIsChanging(false), 300);
  };

  const decrease = () => {
    const newValue = Math.max(min, value - 1);
    if (newValue !== value) {
      onChange(newValue);
      animateChange();
    }
  };

  const increase = () => {
    const newValue = Math.min(max, value + 1);
    if (newValue !== value) {
      onChange(newValue);
      animateChange();
    }
  };

  const canDecrease = value > min;
  const canIncrease = value < max;

  return (
    <div className={`flex items-center bg-gray-900 rounded-2xl p-2  max-w-xs ${className}`}>
      
      <button 
        className={`w-8 h-8 rounded-xl text-white text-xl font-semibold transition-all duration-200 touch-manipulation select-none
          ${canDecrease 
            ? 'bg-gradient-to-br from-pink-400 to-red-500 hover:scale-105 hover:shadow-lg hover:shadow-pink-300/40 active:scale-95' 
            : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        onClick={decrease}
        disabled={!canDecrease}
        title={canDecrease ? "Réduire d'1 seconde" : `Minimum: ${min}s`}
        aria-label="Diminuer le temps d'exposition"
      >
        −
      </button>

      <div className={`flex-1 text-center text-xl font-bold text-slate-800 px-6 py-4 mx-3 bg-gradient-to-br from-slate-50 to-slate-100 rounded-xl border border-slate-200 relative overflow-hidden transition-all duration-300
        ${isChanging ? 'scale-105 text-blue-500' : ''} 
        sm:text-xl sm:px-4 sm:py-5 sm:mx-4`}>
        
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-500"></div>
        
        {formatTime(value)}
        
        <div className="absolute bottom-1 right-2 text-xs text-slate-500 font-medium uppercase tracking-wide">
          {t('focuser.exposure')}
        </div>
      </div>

      <button 
        className={`w-8 h-8 rounded-xl text-white text-xl font-semibold transition-all duration-200 touch-manipulation select-none
          ${canIncrease 
            ? 'over:bg-blue-800 bg-blue-700 disabled:bg-gray-400 hover:scale-105 hover:shadow-lg hover:shadow-indigo-300/40 active:scale-95' 
            : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        onClick={increase}
        disabled={!canIncrease}
        title={canIncrease ? "Augmenter d'1 seconde" : `Maximum: ${max}s`}
        aria-label="Augmenter le temps d'exposition"
      >
        +
      </button>
    </div>
  );
};
export default ExposureTimeInput;