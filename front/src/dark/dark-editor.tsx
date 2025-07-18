import { useEffect, useState } from "react";
import { useObserverStore, useConfigStore } from "../../store/store";
import { CameraCard } from "../../components/observatory/cameraCard";
import { Trash2, Plus, Check, Minus } from "lucide-react";
import  TextInput  from "../../design-system/inputs/input";
import Button from "../../design-system/buttons/main";
import type { DarkLibraryType } from "../../types/api.type";
import { apiService } from "../../api/api";
import Swal from "sweetalert2";
import { useTranslation } from 'react-i18next';

export default function DarkEditor({refresh}: {refresh:() => void;}) {
  const { camera } = useObserverStore();
  const { config } = useConfigStore();
  const [lib, setLib] = useState<DarkLibraryType[]>([]);
  const [newRows, setNewRows] = useState<DarkLibraryType[]>([
  ]);
  const { t } = useTranslation();
  

  useEffect(()=> {
    const getLibrary = async() => {
        const lib = await apiService.getDarkForCamera(camera.id as string);
        setLib(lib);
    }

    getLibrary();
  }, [])

  const  handleDelete = async(index: string|undefined) => {

    if (index==undefined) return;
    Swal.fire({
          title: t('form.confirm'),
          showCancelButton: true,
          confirmButtonText: t('form.delete'),
          denyButtonText: t('form.dontdelete')
        }).then(async (result) => {
          if (result.isConfirmed){
            const newDark = await apiService.deleteDark(camera.id as string, index);
            setLib(newDark);
          }
        });

  };

  const handleAddRow = () => {
    console.log(camera)
    setNewRows([
      ...newRows,
      { temperature: camera.temperature as number  , 
        exposition: config.dark_default_exposition as number, 
        gain: camera.default_gain as number, count: config.dark_default_captures as number, 
        date:''
      },
    ]);
  };

  const deleteRow = ( index:number ) => {
    const newLib = [...newRows];
    newLib.splice(index, 1);
    setNewRows(newLib);

  }
  const handleChange = (
    index: number,
    field: keyof DarkLibraryType,
    value: number
  ) => {
    if (field=='date') return
    const updated = [...newRows];
    updated[index][field] = value;
    setNewRows(updated);
  };

    const handleValidateAll = () => {
        apiService.setNewDarkForCamera(camera.id as string,newRows )

        setLib([...lib, ...newRows]);
        setNewRows([]);
        refresh();
    };
    console.log(camera)
  return (
        <div className="p-4 space-y-6">
            <h2 className="text-xl font-bold text-center">{t('nav.dark_manager')}</h2>

            <div className="flex-1 bg-white/10 border border-blue-300 rounded-2xl p-6 shadow-lg backdrop-blur-md  mx-auto max-w-2xl w-[90%]">
            <CameraCard item={camera} />
            </div>

            <div className="space-y-2">
            {lib.map((item, index) => (
                <div
                key={index}
                className="flex items-center justify-between bg-gray-800 text-white p-4 rounded-xl shadow mx-auto max-w-2xl w-[90%]"
                >
                <div className="flex flex-wrap gap-4">
                    {camera.is_cooled===true && <div><span className="font-semibold">{t('global.temperature')}:</span> {item.temperature}°C</div>}
                    <div><span className="font-semibold">{t('global.exposition')}:</span> {item.exposition}s</div>
                    <div><span className="font-semibold">{t('global.gain')}:</span> {item.gain}</div>
                    <div><span className="font-semibold">{t('global.captures')}:</span> {item.count}</div>
                </div>
                <button
                    onClick={() => handleDelete(item.date)}
                    className="text-red-500 hover:text-red-700"
                    title="Supprimer"
                >
                    <Trash2 size={20} />
                </button>
                </div>
            ))}
            </div>

            <h3 className="flex text-lg font-semibold items-center justify-center text-center">{t('form.add_dark')}                <Button
                    onClick={handleAddRow}
                    className="flex items-center ml-4 gap-1 text-blue-600 hover:text-blue-800"
                >
                    <Plus size={20} /></Button></h3>

            <div className="space-y-2">
            {newRows.map((row, index) => (
                <div
                key={index}
                className="flex flex-wrap items-end gap-4 bg-gray-100 p-4 rounded-xl mx-auto max-w-2xl w-[90%] justify-center"
                >{camera.is_cooled===true && (
                    <div className="flex flex-col">
                        <label className="text-sm font-medium text-gray-700 mb-1 text-center">
                        {t('global.temperature')}(°C)
                        </label>
                        <TextInput
                        type="number"
                        value={row.temperature}
                        onChange={(e) => handleChange(index, "temperature", +e.target.value)}
                        className="w-28 px-2 py-1 rounded border"
                        />
                    </div>
                )}
                <div className="flex flex-col">
                    <label className="text-sm font-medium text-gray-700 mb-1 text-center">
                    {t('global.exposition')} (s)
                    </label>
                    <TextInput
                    type="number"
                    value={row.exposition}
                    onChange={(e) => handleChange(index, "exposition", +e.target.value)}
                    className="w-32 px-2 py-1 rounded border"
                    />
                </div>
                <div className="flex flex-col">
                    <label className="text-sm font-medium text-gray-700 mb-1 text-center">
                    {t('global.gain')}
                    </label>
                    <TextInput
                    type="number"
                    value={row.gain}
                    onChange={(e) => handleChange(index, "gain", +e.target.value)}
                    className="w-24 px-2 py-1 rounded border"
                    />
                </div>
                <div className="flex flex-col">
                    <label className="text-sm font-medium text-gray-700 mb-1 text-center">
                    {t('global.captures')}
                    </label>
                    <TextInput
                    type="number"
                    value={row.count}
                    onChange={(e) => handleChange(index, "count", +e.target.value)}
                    className="w-24 px-2 py-1 rounded border"
                    />
                </div>
               <Button
                    onClick={() => deleteRow(index)}
                    className="flex items-center gap-1 text-green-600 hover:text-green-800"
                >
                    <Minus className="text-red-500"/>
                </Button>
                </div>
            ))}
            </div>
                <div className="flex justify-center gap-6 mt-4">

                { (newRows.length>0) && (
                <Button
                    onClick={() => handleValidateAll()}
                    className="flex items-center gap-1 text-green-600 hover:text-green-800"
                >
                    <Check size={20} /> {t('form.validate')}                 </Button>
                )}
                </div>
        </div>
    );

}
