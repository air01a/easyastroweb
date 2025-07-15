import { useState } from 'react';
import { DelayInput} from '../../components/forms/timer'
import { Clock } from 'lucide-react';
import Button from '../../design-system/buttons/main';
import { useTranslation } from 'react-i18next';

export default function Spacer( { id,initialValue,  onUpdate} : {id:number, initialValue: number, onUpdate : ( id:number, value: number) => void}) {
  const [delay, setDelay] = useState<number>(initialValue);
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const { t } = useTranslation();

  const getHourStr = (delay:number):string => {
    if (delay<60) return `${delay} s`;
    const min = Math.floor(delay/60);
    const sec = delay - 60 * min; 
    if (min<60) return `${min} m ${delay - 60*min}`
    const hour = Math.floor(min/60);
    return `${hour} h ${min-hour*60} m ${sec} s`;
  }

  const onChangeDelay = (delay:number):void =>{
    setDelay(delay);
    onUpdate(id, delay);
  }

  return (<div className="flex flex-col bg-gray-800 rounded-lg border border-gray-200 p-6 shadow-sm mb-4">
            { delay===0 ? (
                    <div className="flex flex-col justify-center  items-center" onClick={() =>setIsOpen(true)}>➕ {t('timer.addDelay')}</div>
            ) :
                    <div className="flex flex-col justify-center  items-center" onClick={() =>setIsOpen(true)}>
                    <h3 className="flex text-lg font-semibold text-gray-10"><Clock className="w-5 h-5 text-blue-500 mt-1 mr-2" /> {t('timer.delay')} : {getHourStr(delay)}</h3></div>
            }
            {isOpen && (

                <div className="flex flex-col w-200 justify-center  items-center"> 
                    <DelayInput
                        onDelayChange={onChangeDelay}
                        initialDelay={initialValue} // 5 minutes par défaut
                        minDelay={0}
                        maxDelay={3 * 3600} // 24 heures
                    />
                    <Button onClick={() => setIsOpen(false)}> {t('timer.validDelay')}</Button>
                 </div>
            )}
    </div>)
}
