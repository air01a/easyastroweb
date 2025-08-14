import { useState } from 'react';
import  TextInput  from '../../design-system/inputs/input';
import SelectInput  from '../../design-system/inputs/select'
import Button from '../../design-system/buttons/main';
import {AddButton, RemoveButton} from '../../design-system/buttons/addremove';
import type { ImageConfig } from './plan.type'
import { useObserverStore } from "../../store/store";
import Checkbox from '../../design-system/inputs/checkbox';
import  ComboBoxSelect from '../../design-system/inputs/select-input';

import { useTranslation } from 'react-i18next';


// Générateur d’ID unique
let nextId = 0;

export default function ImageSettings( { initialSettings,  onUpdate, maxDuration, gains, expositions} : {initialSettings: ImageConfig[],gains : number[], expositions:number[], onUpdate : ( settings: ImageConfig[]) => void , maxDuration:number}) {
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
        exposureTime: expositions[0],
        filter: filters[0],
        focus: false,
        gain: gains[0],
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


  let availableExposition: {label:string, value:string}[] = [];
  let availableGains: {label:string, value:string}[] = [];
  availableExposition = Array.from(expositions, (exposition)=>  { return {label:exposition.toString(), value:exposition.toString()}});
  availableGains = Array.from(gains, (gain)=>  { return {label:gain.toString(), value:gain.toString()}});


  return (
    <div className="space-y-4 mt-4 items-center">
  {settings && settings.map((config) => (
    <div
      key={config.id}
      className="bg-gray-800 p-2 rounded"
    >
      {/* Version Desktop - une ligne avec séparateurs */}
      <div className="hidden md:flex md:flex-wrap md:flex-row md:items-center md:gap-2">
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
        <span>|</span>
        
        <span>{t('form.exposition')} </span>
        <ComboBoxSelect 
          options={availableExposition}
          onSelectValue={(value)=> { handleChange(config.id, 'exposureTime', Number(value)) }}
          defaultValue={availableExposition[0]}
        />
        <span>s |</span>
        
        <span>{t('form.gain')} </span>
        <ComboBoxSelect 
          options={availableGains}
          onSelectValue={(value)=> { handleChange(config.id, 'gain', Number(value)) }}
          defaultValue={availableGains[0]}
        />
        <span>|</span>
        
        <span>{t('form.filter')}</span>
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
        <span>|</span>
        
        <span>{t('form.refocus')}</span>
        <Checkbox 
          checked={config.focus===true}
          onChange={() => handleChange(config.id, 'focus', !config.focus)}
        />
        
        <AddButton
          onClick={addRow}
          title={t('form.add')}
        />
        <RemoveButton
          onClick={() => removeRow(config.id)}
          title={t('form.delete')}
        />
      </div>

      {/* Version Mobile - colonnes avec labels */}
      <div className="md:hidden space-y-3">
        <div className="flex items-center justify-between">
          <span className="font-medium">{t('form.imagesNumber')}</span>
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
        </div>
        
        <div className="flex items-center justify-between">
          <span className="font-medium">{t('form.exposition')}</span>
          <ComboBoxSelect 
            options={availableExposition}
            onSelectValue={(value)=> { handleChange(config.id, 'exposureTime', Number(value)) }}
            defaultValue={availableExposition[0]}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <span className="font-medium">{t('form.gain')}</span>
          <ComboBoxSelect 
            options={availableGains}
            onSelectValue={(value)=> { handleChange(config.id, 'gain', Number(value)) }}
            defaultValue={availableGains[0]}
          />
        </div>
        
        <div className="flex items-center justify-between">
          <span className="font-medium">{t('form.filter')}</span>
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
        </div>
        
        <div className="flex items-center justify-between">
          <span className="font-medium">{t('form.refocus')}</span>
          <Checkbox 
            checked={config.focus===true}
            onChange={() => handleChange(config.id, 'focus', !config.focus)}
          />
        </div>
        
        <div className="flex justify-center gap-2 pt-2">
          <AddButton
            onClick={addRow}
            title={t('form.add')}
          />
          <RemoveButton
            onClick={() => removeRow(config.id)}
            title={t('form.delete')}
          />
        </div>
      </div>
    </div>
  ))}
  {(!settings || settings.length === 0) && (
    <Button onClick={addRow}>
      {t('form.configurationAdd')}
    </Button>
  )}
</div>
  );
}
