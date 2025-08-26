import React, { useEffect, useState } from "react";
import { Pencil, Trash } from "lucide-react";
import type {  ConfigItems } from '../../store/config.type';
import DynamicForm from "../forms/dynamicform";
import type { Field } from "../../types/dynamicform.type";
import Button from "../../design-system/buttons/main";
import { generateRandomName } from "../../lib/fsutils";
import Swal from "sweetalert2";
import { useTranslation } from 'react-i18next';

export type Props = {
    items: ConfigItems[];
    onEdit?: (item: ConfigItems[]) => void;
    formLayout : Field[];
    editable?: boolean;
    CardComponent: React.ComponentType<{ item: ConfigItems }>;
    selectedItem? : string | null;
    onSelect?: (item: ConfigItems) => void;
}
const colors = [
  "bg-sky-900",
  "bg-blue-900",
];

const ObservatoryList: React.FC<Props> = ({ items, formLayout, onEdit, CardComponent, editable=true, selectedItem=null, onSelect }) => {
  const [selectedId, setSelectedId] = useState<string | null>(selectedItem);

  const [currentItems, setCurrentItems] = useState<ConfigItems[]> ([]);
  const [edit, setEdit] = useState<string | null>(null);
  const [currentEdit, setCurrentEdit] = useState<ConfigItems|null>(null);
  const [hasError, setHasError] = useState<boolean>(false);
  const { t } = useTranslation();
  useEffect(()=> {
    setCurrentItems(items);
  },[items]);

  
  const handleSelect = (id: ConfigItems) => {
    if (edit) return;

    Swal.fire({
      title: t('form.confirm'),
      showCancelButton: true,
      confirmButtonText: t('form.change'),
      denyButtonText: t('form.dontChange')
    }).then((result) => {
      if (result.isConfirmed){
        setSelectedId(id.id as string);
        if(onSelect) onSelect(id);
      }
    });
  };

  const handleEdit = (id:ConfigItems)=> {
    setEdit(id.id as string || null);
  }

  const handleSave = async (updatedItem : ConfigItems|null, index:number) => {
        if (hasError) return; 
        if (updatedItem===null) return;
        let selected : ConfigItems|null = null;
        if (currentItems[index].id===selectedId) selected=updatedItem
        const newItems = currentItems.map((item, newindex) =>
                            index === newindex ? updatedItem : item
                        );
        if (onEdit) {
           onEdit(newItems);
           if (selected && onSelect) {
              onSelect(selected);
            setSelectedId(selected.id as string);
           }

        }
        setEdit(null);
  }

  const handleDelete = async (deletedItem : ConfigItems) => {
    Swal.fire({
          title: t('form.confirm'),
          text: t('form.noReverse'),
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#3085d6",
          cancelButtonColor: "#d33",
          confirmButtonText: t('delete')
        }).then((result) => {        
          if (result.isConfirmed) {
            const newItems = items.filter((item) => item.id !== deletedItem.id);
            if (onEdit)  onEdit(newItems);
            setEdit(null);
          }
        });

  }

  const handleAdd = () => {
    const id = generateRandomName();
    const newItem : ConfigItems = {};
    formLayout.forEach((element)=>newItem[element.fieldName]=element.defaultValue);
    newItem["id"]= id;
    setCurrentItems([...currentItems,newItem]);
    setEdit(id)
    setCurrentEdit(newItem)
  }

  const dynamicFormChange = (change : ConfigItems, error: boolean) => {
    setHasError(error);
    setCurrentEdit(change);
  }
  return (
    <div className="flex flex-col items-center space-y-4">
      {currentItems && currentItems.map((item, index) => {
        const isSelected = item.id === selectedId;
        const isEdit = edit === item.id;
        return (
          <div
            key={index}
            onClick={() => handleSelect(item)}
            className={`relative w-[90%] rounded-lg p-4 shadow-md cursor-pointer transition
              ${colors[index % colors.length]}
              ${isSelected ? "ring-4 ring-blue-500" : "hover:ring-2 hover:ring-blue-300"}
            `}
          >
            {editable && (
            <div className="absolute top-2 right-2 flex space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleEdit(item);
                }}
                className="p-1 bg-white rounded shadow hover:bg-gray-100"
                aria-label="Éditer"
              >
                <Pencil className="w-5 h-5 text-gray-800" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(item);
                }}
                className="p-1 bg-white rounded shadow hover:bg-gray-100"
                aria-label="Supprimer"
              >
                <Trash className="w-5 h-5 text-red-600" />
              </button>
            </div>
            )}
            { isEdit ? (
                <div className="">
                  <DynamicForm  onChange={dynamicFormChange} formDefinition={formLayout} initialValues={item}/> 
                  <div className="flex justify-center items-center">
                    <Button disabled={hasError} onClick={() => {handleSave(currentEdit, index)}}>{t('form.save')}</Button>
                    <Button  onClick={() => setEdit(null)} className="ml-8 bg-gray-800">{t('form.cancel')}</Button>
                  </div>
                </div>
             ) : ( 
                <CardComponent item={item}/>)
            }
          </div>
        );
      })}
         {editable && (<Button onClick={handleAdd}>{t('form.add')}</Button>) }

    </div>
  );
};

export default ObservatoryList;
