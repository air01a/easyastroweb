import React, { useEffect, useState } from "react";
import { useTranslation } from 'react-i18next';

export interface SkyMapFiltersProps {
  showConstellations: boolean;
  showStarNames: boolean;
  showDeepSky: boolean;
  minMagnitude: number;
  dateTime: Date; // vrai Date
  onChange: (next: {
    showConstellations: boolean;
    showStarNames: boolean;
    showDeepSky: boolean;
    minMagnitude: number;
    dateTime: Date;
  }) => void;
}

function toDateTimeLocalValue(d: Date): string {
  const pad = (n: number) => n.toString().padStart(2, "0");
  return (
    d.getFullYear() +
    "-" +
    pad(d.getMonth() + 1) +
    "-" +
    pad(d.getDate()) +
    "T" +
    pad(d.getHours()) +
    ":" +
    pad(d.getMinutes())
  );
}

const DT_RE = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/;

/** Parse "YYYY-MM-DDTHH:MM" via constructeur numérique (gère le rollover) */
function parseWithRollover(v: string): Date | null {
  const m = DT_RE.exec(v);
  if (!m) return null;
  const year = parseInt(m[1], 10);
  const month = parseInt(m[2], 10); // 1..12 (mais on laisse JS gérer >12 -> rollover année)
  const day = parseInt(m[3], 10);   // 1..31 (JS rollovers si > last day)
  const hour = parseInt(m[4], 10);
  const minute = parseInt(m[5], 10);
  const d = new Date(year, month - 1, day, hour, minute);
  return isNaN(d.getTime()) ? null : d;
}

export const SkyMapFilters: React.FC<SkyMapFiltersProps> = ({
  showConstellations,
  showStarNames,
  showDeepSky,
  minMagnitude,
  dateTime,
  onChange,
}) => {
  const { t } = useTranslation();
  
  // valeur locale pour l'input (permet l'édition temporairement invalide)
  const [localValue, setLocalValue] = useState<string>(() => toDateTimeLocalValue(dateTime));

  // si le parent change la date, on répercute dans l'input
  useEffect(() => {
    setLocalValue(toDateTimeLocalValue(dateTime));
  }, [dateTime]);

  const emit = (next: {
    showConstellations: boolean;
    showStarNames: boolean;
    showDeepSky: boolean;
    minMagnitude: number;
    dateTime: Date;
  }) => onChange(next);

  

  const handleBlurDate = () => {
    // À la sortie, on normalise toujours via rollover (31/09 -> 01/10)
    const d = parseWithRollover(localValue);
    if (d) {
      const normalized = toDateTimeLocalValue(d);
      setLocalValue(normalized);
      emit({
        showConstellations,
        showStarNames,
        showDeepSky,
        minMagnitude,
        dateTime: d,
      });
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4 rounded-xl m-2 bg-gray-800 text-white w-full max-w-sm shadow-lg">
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={showConstellations}
          onChange={(e) =>
            emit({
              showConstellations: e.target.checked,
              showStarNames,
              showDeepSky,
              minMagnitude,
              dateTime,
            })
          }
        />
        {t('skymap.showConstellations')}
      </label>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={showStarNames}
          onChange={(e) =>
            emit({
              showConstellations,
              showStarNames: e.target.checked,
              showDeepSky,
              minMagnitude,
              dateTime,
            })
          }
        />
        {t('skymap.showStars')}
      </label>

      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          checked={showDeepSky}
          onChange={(e) =>
            emit({
              showConstellations,
              showStarNames,
              showDeepSky: e.target.checked,
              minMagnitude,
              dateTime,
            })
          }
        />
        {t('skymap.showDso')}
      </label>

      <div className="flex flex-col gap-2">
        <label>
          {t('skymap.maxMagnitude')} : <span className="font-mono">{minMagnitude}</span>
        </label>
        <input
          type="range"
          min={-1}
          max={6}
          step={0.1}
          value={minMagnitude}
          onChange={(e) =>
            emit({
              showConstellations,
              showStarNames,
              showDeepSky,
              minMagnitude: parseFloat(e.target.value),
              dateTime,
            })
          }
        />
      </div>

      <div className="flex flex-col gap-2">
        <label>{t('skymap.observationTime')}</label>
        <input
            type="datetime-local"
            step={1800} // 30 min
            value={localValue}
            onChange={(e) => {
                const v = e.target.value;
                // Si la saisie est complète (YYYY-MM-DDTHH:MM), on normalise immédiatement
                if (DT_RE.test(v)) {
                const d = parseWithRollover(v); // new Date(year, month-1, day, hour, minute)
                if (d) {
                    const normalized = toDateTimeLocalValue(d); // => "YYYY-MM-DDTHH:MM" (local)
                    setLocalValue(normalized);                   // >>> mettra bien 2025-10-01, pas 2025-09-01
                    onChange({
                    showConstellations,
                    showStarNames,
                    showDeepSky,
                    minMagnitude,
                    dateTime: d,
                    });
                    return;
                }
                }
                // Sinon on garde la chaîne telle quelle pendant l'édition incomplète
                setLocalValue(v);
            }}
            onBlur={handleBlurDate} // garde ta normalisation au blur en backup
            className="text-black rounded px-2 py-1"
            />
      </div>
    </div>
  );
};
