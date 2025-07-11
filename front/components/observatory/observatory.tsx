import React, { useEffect, useState } from "react";
import { Pencil, Trash } from "lucide-react";
import type {  ConfigItems } from '../../store/config.type';
import DynamicForm from "../forms/dynamicform";
import type { Field } from "../../types/dynamicform.type";
import Button from "../../design-system/buttons/main";
import { generateRandomName } from "../../lib/fsutils";
import Swal from "sweetalert2";

export type Props = {
    items: ConfigItems[];
    onEdit?: (item: ConfigItems[]) => void;
    formLayout : Field[];
    editable?: boolean;
    CardComponent: React.ComponentType<{ item: ConfigItems }>;
    selectedName? : string | null;
    onSelect?: (item: ConfigItems) => void;
}
const colors = [
  "bg-sky-900",
  "bg-blue-900",
];

const ObservatoryList: React.FC<Props> = ({ items, formLayout, onEdit, CardComponent, editable=true, selectedName=null, onSelect }) => {
  const [selectedId, setSelectedId] = useState<string | null>(selectedName);

  const [currentItems, setCurrentItems] = useState<ConfigItems[]> ([]);
  const [edit, setEdit] = useState<string | null>(null);
  const [currentEdit, setCurrentEdit] = useState<ConfigItems|null>(null);
  const [hasError, setHasError] = useState<boolean>(false);

  useEffect(()=> {
    setCurrentItems(items);
  },[items]);

  
  const handleSelect = (id: ConfigItems) => {
    if (edit) return;

    Swal.fire({
      title: "Do you want to change ?",
      showCancelButton: true,
      confirmButtonText: "Change",
      denyButtonText: `Don't Change`
    }).then((result) => {
      if (result.isConfirmed){
        setSelectedId(id.name as string);
        if(onSelect) onSelect(id);
      }
    });
  };

  const handleEdit = (id:ConfigItems)=> {
    setEdit(id.name as string || null);
  }

  const handleSave = async (updatedItem : ConfigItems|null, index:number) => {
        if (hasError) return; 
        if (updatedItem===null) return;
        let selected : ConfigItems|null = null;
        if (currentItems[index].name===selectedId) selected=updatedItem
        const newItems = currentItems.map((item, newindex) =>
                            index === newindex ? updatedItem : item
                        );
        if (onEdit) {
           onEdit(newItems);
           if (selected && onSelect) {
              onSelect(selected);
            setSelectedId(selected.name as string);
           }

        }
        setEdit(null);
  }

  const handleDelete = async (deletedItem : ConfigItems) => {
    Swal.fire({
          title: "Are you sure?",
          text: "You won't be able to revert this!",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#3085d6",
          cancelButtonColor: "#d33",
          confirmButtonText: "Yes, delete it!"
        }).then((result) => {        
          if (result.isConfirmed) {
            const newItems = items.filter((item) => item.name !== deletedItem.name);
            if (onEdit)  onEdit(newItems);
            setEdit(null);
          }
        });

  }

  const handleAdd = () => {
    const name = generateRandomName();
    const newItem : ConfigItems = {};
    formLayout.forEach((element)=>newItem[element.fieldName]=element.defaultValue);
    newItem["name"]= name;
    setCurrentItems([...currentItems,newItem]);
    setEdit(name)
    setCurrentEdit(newItem)
  }

  const dynamicFormChange = (change : ConfigItems, error: boolean) => {
    setHasError(error);
    setCurrentEdit(change);
  }
  console.log(currentItems);

  return (
    <div className="flex flex-col items-center space-y-4">
      {currentItems && currentItems.map((item, index) => {
        const isSelected = item.name === selectedId;
        const isEdit = edit === item.name;
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
                    <Button disabled={hasError} onClick={() => {handleSave(currentEdit, index)}}>Enregister</Button>
                    <Button  onClick={() => setEdit(null)} className="ml-8 bg-gray-800">Annuler</Button>
                  </div>
                </div>
             ) : ( 
                <CardComponent item={item}/>)
            }
          </div>
        );
      })}
         {editable && (<Button onClick={handleAdd}>Add</Button>) }

    </div>
  );
};

export default ObservatoryList;
