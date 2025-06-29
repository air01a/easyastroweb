import React, { useEffect, useState } from "react";
import { Pencil, Trash } from "lucide-react";
//import type {ObservatoryItem } from './observatory.type';
import type {  ConfigItems } from '../../store/config.type';
import DynamicForm from "../forms/dynamicform";
import type { Field } from "../forms/dynamicform.type";
import Button from "../../design-system/buttons/main";
import { generateRandomName } from "../../lib/fsutils";

export type Props = {
    items: ConfigItems[];
    onEdit: (item: ConfigItems[]) => void;
    formLayout : Field[];
}
const colors = [
  "bg-red-200",
  "bg-green-200",
  "bg-blue-200",
  "bg-yellow-200",
  "bg-purple-200",
];

const ObservatoryList: React.FC<Props> = ({ items, formLayout, onEdit  }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [currentItems, setCurrentItems] = useState<ConfigItems[]> ([]);
  const [edit, setEdit] = useState<string | null>(null);


  useEffect(()=> {
    setCurrentItems(items);
  },[items]);

  
  const handleSelect = (id: ConfigItems) => {
    setSelectedId(id.name as string);
  };

  const handleEdit = (id:ConfigItems)=> {
    setEdit(id.name as string || null);
  }

  const handleSave = (updatedItem : ConfigItems) => {
 

        const newItems = items.map((item) =>
                            item.name === updatedItem.name ? updatedItem : item
                        );
        onEdit(newItems);
        setEdit(null);
  }

  const handleDelete = (deletedItem : ConfigItems) => {
    if (confirm(`Supprimer: ${deletedItem.name} ?`)) {
        const newItems = items.filter((item) => item.name !== deletedItem.name);

        onEdit(newItems);
        setEdit(null);
    }
  }

  const handleAdd = () => {
    const name = generateRandomName();
    setCurrentItems([...currentItems,{name, altitude: 0, longitude:0, latitude:0}]);
    setEdit(name)
  }


  return (
    <div className="flex flex-col items-center space-y-4">
      {currentItems.map((item, index) => {
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
            { isEdit ? (
                <div><DynamicForm  formDefinition={formLayout} initialValues={item}/> <Button onClick={() => {handleSave(item)}}>Enregister</Button></div>
             ) : ( 
                <div>
                    <h3 className="text-lg font-semibold">{item.name}</h3>
                    <p className="text-gray-700">{item.longitude} / {item.latitude} / { item.altitude }</p>
                </div>)
            }
          </div>
        );
      })}
        <Button onClick={handleAdd}>Add</Button>

    </div>
  );
};

export default ObservatoryList;
