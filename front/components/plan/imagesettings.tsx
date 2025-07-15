import { useState } from 'react';
import  TextInput  from '../../design-system/inputs/input';
import SelectInput  from '../../design-system/inputs/select'
import Button from '../../design-system/buttons/main';
import {AddButton, RemoveButton} from '../../design-system/buttons/addremove';
import type { ImageConfig } from './plan.type'
import { useObserverStore } from "../../store/store";
import Checkbox from '../../design-system/inputs/checkbox';

import { useTranslation } from 'react-i18next';


// Générateur d’ID unique
let nextId = 0;

export default function ImageSettings( { initialSettings,  onUpdate, maxDuration} : {initialSettings: ImageConfig[], onUpdate : ( settings: ImageConfig[]) => void , maxDuration:number}) {
  const [settings, setSettings] = useState<ImageConfig[]>(initialSettings);
  //const [remaining, setRemaining] = useState<number>(0);
  const {filterWheel} = useObserverStore();
  const { t } = useTranslation();
  
  const filters = (filterWheel.filters as string[]).length>0?(filterWheel.filters as string[]):["No Filter"];

  const getDuration = (settings : ImageConfig[]) => {
        let newDuration=0;
        settings.forEach((item)=>newDuration+=item.exposureTime*item.imageCount)
        return newDuration/=3600;
    }

  const handleChange = (id: number, field: keyof ImageConfig, value: string|number|boolean) => {
    const prev = settings.map(item =>
        item.id === id ? { ...item, [field]: value } : item
      );


    setSettings(prev);
    onUpdate(prev);
    if (getDuration(settings)> maxDuration) console.log("+++++ Depasse le temps possible")
      

  };

  const addRow = () => {
    const prev = [
      ...settings,
      {
        id: nextId++,
        imageCount: 1,
        exposureTime: 30,
        filter: filters[0],
        focus: false,
      },
    ];
    setSettings(prev);
    onUpdate(prev);
        if (getDuration(settings)> maxDuration) console.log("+++++ Depasse le temps possible")

  };

  const removeRow = (id: number) => {
    const prev=settings.filter(item => item.id !== id)
    setSettings(prev);
  };

  return (
    <div className="space-y-4 mt-4 items-center">
      {settings && settings.map((config) => (
        <div
          key={config.id}
          className="flex items-center gap-2 bg-gray-800 p-2 rounded"
        >
          <span>{t('form.imagesNumber')}</span>
          <TextInput
            type="number"
            min={1}
            value={config.imageCount}
            onChange={(e) =>
              handleChange(config.id, 'imageCount', Number(e.target.value))
            }
            className="w-20 p-1 border rounded"
            placeholder="Nb images"
          />
          <span> | </span>
          <span>{t('form.exposition')}</span>

          <TextInput
            type="number"
            min={1}
            value={config.exposureTime}
            onChange={(e) =>
              handleChange(config.id, 'exposureTime', Number(e.target.value))
            }
            className="w-20 p-1 border rounded"
            placeholder="Exposition (s)"
          />
          <span>s | {t('form.filter')} </span>

          <SelectInput
            value={config.filter}
            onChange={(e) =>
              handleChange(config.id, 'filter', e.target.value)
            }
            className="p-1 border rounded"
          >
            {filters.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </SelectInput>

          <div className="flex items-center justify-center">
            <label className="mr-4">{t('form.refocus')}</label>
            <Checkbox 
              checked={config.focus===true}
              onChange={() => handleChange(config.id, 'focus', !config.focus)}
            />
          </div>

          <AddButton
            onClick={addRow}
            title={t('form.add')}
          />


          <RemoveButton
            onClick={() => removeRow(config.id)}
            title={t('form.delete')}
          />
           
        </div>
      ))}

      {(!settings || settings.length === 0) && (
        <Button
          onClick={addRow}
        >
          {t('form.configurationAdd')}
        </Button>
      )}
    </div>
  );
}
