import React, { useState, useEffect } from 'react';
import { Clock, RotateCcw } from 'lucide-react';

interface DelayInputProps {
  onDelayChange?: (totalSeconds: number) => void;
  initialDelay?: number; // en secondes
  minDelay?: number; // en secondes
  maxDelay?: number; // en secondes
  className?: string;
}

export const DelayInput: React.FC<DelayInputProps> = ({
  onDelayChange,
  initialDelay = 0,
  minDelay = 1,
  maxDelay = 24 * 3600, // 24 heures par défaut
  className = ''
}) => {
  const [hours, setHours] = useState(0);
  const [minutes, setMinutes] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [mode, setMode] = useState<'simple' | 'detailed'>('simple');

  // Convertir les secondes en heures, minutes, secondes
  const convertSecondsToTime = (totalSecs: number) => {
    const h = Math.floor(totalSecs / 3600);
    const m = Math.floor((totalSecs % 3600) / 60);
    const s = totalSecs % 60;
    return { h, m, s };
  };

  // Initialiser les valeurs
  useEffect(() => {
    const { h, m, s } = convertSecondsToTime(initialDelay);
    setHours(h);
    setMinutes(m);
    setSeconds(s);
  }, [initialDelay]);

  // Calculer le total en secondes
  const totalSeconds = hours * 3600 + minutes * 60 + seconds;

  // Notifier le changement
  useEffect(() => {
    if (onDelayChange && totalSeconds >= minDelay && totalSeconds <= maxDelay) {
      onDelayChange(totalSeconds);
    }
  }, [totalSeconds, onDelayChange, minDelay, maxDelay]);

  // Formater l'affichage du temps
  const formatTime = (h: number, m: number, s: number) => {
    const parts : string[] = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (s > 0) parts.push(`${s}s`);
    return parts.length > 0 ? parts.join(' ') : '0s';
  };

  // Présets courants
  const presets = [
    { label: '30s', value: 30 },
    { label: '1m', value: 60 },
    { label: '5m', value: 300 },
    { label: '15m', value: 900 },
    { label: '30m', value: 1800 },
    { label: '1h', value: 3600 },
    { label: '2h', value: 7200 },
  ].filter(preset => preset.value >= minDelay && preset.value <= maxDelay);

  const handlePresetClick = (value: number) => {
    const { h, m, s } = convertSecondsToTime(value);
    setHours(h);
    setMinutes(m);
    setSeconds(s);
  };

  const handleReset = () => {
    setHours(0);
    setMinutes(0);
    setSeconds(0);
  };

  const handleSliderChange = (value: number) => {
    const { h, m, s } = convertSecondsToTime(value);
    setHours(h);
    setMinutes(m);
    setSeconds(s);
  };

  return (
    <div className={`bg-white rounded-lg border border-gray-200 p-6 shadow-sm ${className}`}>
      <div className="flex items-center gap-2 mb-4">
        <Clock className="w-5 h-5 text-blue-500" />
        <h3 className="text-lg font-semibold text-gray-800">Délai</h3>
        <button
          onClick={handleReset}
          className="ml-auto p-1 hover:bg-gray-100 rounded-full transition-colors"
          title="Réinitialiser"
        >
          <RotateCcw className="w-4 h-4 text-gray-500" />
        </button>
      </div>

      {/* Affichage du temps actuel */}
      <div className="text-center mb-6">
        <div className="text-3xl font-mono font-bold text-gray-800 mb-2">
          {formatTime(hours, minutes, seconds)}
        </div>
        <div className="text-sm text-gray-500">
          Total: {totalSeconds.toLocaleString()} secondes
        </div>
      </div>

      {/* Basculer entre mode simple et détaillé */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setMode('simple')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            mode === 'simple'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Simple
        </button>
        <button
          onClick={() => setMode('detailed')}
          className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
            mode === 'detailed'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Détaillé
        </button>
      </div>

      {mode === 'simple' ? (
        <div className="space-y-4">
          {/* Slider principal */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Délai (utiliser le slider)
            </label>
            <input
              type="range"
              min={minDelay}
              max={Math.min(maxDelay, 7200)} // Limité à 2h pour le slider
              value={Math.min(totalSeconds, 7200)}
              onChange={(e) => handleSliderChange(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-500 mt-1">
              <span>{minDelay}s</span>
              <span>2h</span>
            </div>
          </div>

          {/* Présets */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Présets courants
            </label>
            <div className="grid grid-cols-4 gap-2">
              {presets.map((preset) => (
                <button
                  key={preset.value}
                  onClick={() => handlePresetClick(preset.value)}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    totalSeconds === preset.value
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Contrôles détaillés */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Heures
              </label>
              <input
                type="number"
                min="0"
                max="23"
                value={hours}
                onChange={(e) => setHours(Math.max(0, Math.min(23, parseInt(e.target.value) || 0)))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minutes
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={minutes}
                onChange={(e) => setMinutes(Math.max(0, Math.min(59, parseInt(e.target.value) || 0)))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Secondes
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={seconds}
                onChange={(e) => setSeconds(Math.max(0, Math.min(59, parseInt(e.target.value) || 0)))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Sliders individuels */}
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Heures: {hours}
              </label>
              <input
                type="range"
                min="0"
                max="23"
                value={hours}
                onChange={(e) => setHours(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minutes: {minutes}
              </label>
              <input
                type="range"
                min="0"
                max="59"
                value={minutes}
                onChange={(e) => setMinutes(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Secondes: {seconds}
              </label>
              <input
                type="range"
                min="0"
                max="59"
                value={seconds}
                onChange={(e) => setSeconds(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
          </div>
        </div>
      )}

      {/* Validation */}
      {(totalSeconds < minDelay || totalSeconds > maxDelay) && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-700">
            Le délai doit être entre {minDelay}s et {maxDelay}s
          </p>
        </div>
      )}

      <style>
        {`
        .slider::-webkit-slider-thumb {
          appearance: none;
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        .slider::-moz-range-thumb {
          height: 20px;
          width: 20px;
          border-radius: 50%;
          background: #3b82f6;
          cursor: pointer;
          border: none;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        `}
      </style>
    </div>
  );
};

