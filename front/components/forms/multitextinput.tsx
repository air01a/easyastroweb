import React, { useState } from "react";
import {Plus, Minus} from 'lucide-react';
import  Input from '../../design-system/inputs/input'
import Swal from "sweetalert2";

type Props = {
    name: string;
    onChange?: (name: string, values: string[]) => void;
    initialValues: string[]
};

const MultiTextInput: React.FC<Props> = ({ name,  onChange, initialValues }) => {
  const [values, setValues] = useState<string[]>(initialValues);
  
 

  const handleChange = (index: number, newValue: string) => {
    const updated = [...values];
    updated[index] = newValue;
    setValues(updated);
    onChange?.(name, updated);
  };

  const handleAdd = () => {

    const updated = [...values, ""];
    setValues(updated);
    //onChange?.(name, updated);
  }

  const handleDelete = (index: number) => {
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
                const updated = values.filter((_, ind) => ind !== index);
                setValues(updated);
                  onChange?.(name, updated);
              }
            });
  }

  return (
    <div className="space-y-2 flex flex-col w-60 items-center justify-center">
      {values.map((value, index) => (
        <div className="flex flex-row">
          <Input
            key={index}
            type="text"
            value={value}
            onChange={(e) => handleChange(index, e.target.value)}
            className="border px-2 py-1 rounded "
            placeholder={`Champ ${index + 1}`}
          />
            <button type="button" className="ml-4" onClick={()=>{handleDelete(index)}}><Minus className="w-5 h-5 text-red-500"/></button>
        </div>
      ))}
      <button type="button" onClick={(e)=> {e.stopPropagation();handleAdd();}}><Plus/></button>
    </div>
  );
};
export default MultiTextInput;