import React, { useEffect, useState } from "react";
import SelectInput  from '../../design-system/inputs/select'
import Input  from '../../design-system/inputs/input'
import Checkbox  from '../../design-system/inputs/checkbox'

import type {Field, FieldType} from './dynamicform.type'
import CircularButtonSelection from "./circularbutton";

type Props = {
  formDefinition: Field[];
  initialValues?: Record<string, FieldType>;
  onChange?: (values: Record<string, FieldType>,error: boolean) => void;

};

const DynamicForm: React.FC<Props> = ({
  formDefinition,
  initialValues = {},
  onChange,
}) => {


  const getDefaultValue = (field: Field) => {
    if (field.defaultValue !== undefined) return field.defaultValue;
      switch (field.varType) {
        case "INT":
        case "REAL":
          return 0;
        case "STR":
          return "";
        case "BOOL":
          return false;
        default:
          return "";
      }
  };

  const [formData, setFormData] = useState(() =>
    Object.fromEntries(
      formDefinition.map((f) => [
          f.fieldName,
          initialValues[f.fieldName] ?? getDefaultValue(f),
      ])
    )
  );

  useEffect(() => {
    const initialFormData = Object.fromEntries(
      formDefinition.map((f) => [
        f.fieldName,
        initialValues[f.fieldName] ?? f.defaultValue,
      ])
    );
    setFormData(initialFormData);
  }, [formDefinition, initialValues]);

  const [errors, setErrors] = useState<Record<string, string>>({});

  
  const validate = (field: Field, value: string): string | null => {
    console.log(typeof value)
    if (field.required===true && value.length===0) return "Parameter required"
    switch (field.varType) {
      case "INT":
        return /^-?\d*$/.test(String(value)) ? null : "Entier attendu";
      case "REAL":
        return /^-?\d*(\.\d+)?$/.test(String(value)) ? null : "Nombre réel attendu";
      case "STR":
        return typeof value === "string" ? null : "Texte invalide";
      case "BOOL":
        return value==="1" || value=="0" ? null : "Booléen attendu";
      default:
        return null;
    }
  };

  const handleChange = (field: Field, rawValue: string) => {
    let value: FieldType = rawValue;

    if (field.fieldType === "CHECKBOX") {
      value = rawValue==="1"?true:false;
      console.log("value", value)
    }

    const error = validate(field, rawValue);
    setErrors((prev) => ({ ...prev, [field.fieldName]: error || "" }));
    if (!error) {
      if (field.varType === "INT") value = parseInt(value as string)||0;
      else if (field.varType === "REAL") value = parseFloat(value as string)||0.0;


    }
      const newFormData = { ...formData, [field.fieldName]: value };
      setFormData(newFormData);
      onChange?.(newFormData, error!==null);

  };

  const circularCallBack = (name: string, values: boolean[])  => {
    const newFormData = { ...formData, [name]:values};
    setFormData(newFormData);
    onChange?.(newFormData, false)
  }

  return (
    <form >
      {formDefinition.map((field) => {
        const value = formData[field.fieldName];
        const error = errors[field.fieldName];
        console.log(value);
        return (
          <div key={field.fieldName} style={{ marginBottom: "1rem" }}>
            <label className="text-white mb-1">{field.description} : </label>

            {field.fieldType === "INPUT" && (
              <Input
                type="text"
                value={value as string}
                onChange={(e) => handleChange(field, e.target.value)}
              />
            )}

            {field.fieldType === "SELECT" && (
              <SelectInput
                value={value as string}
                onChange={(e) => handleChange(field, e.target.value)}
              >
                {field.possibleValue?.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </SelectInput>
            )}

            {field.fieldType === "CHECKBOX" && (
              <Checkbox
                
                checked={value===true}
                onChange={(e) => handleChange(field, e.target.checked ? '1':'0')}
              />
            )}

            {field.fieldType=="CIRCULAR" && (
              <div><CircularButtonSelection callBack={circularCallBack} name={field.fieldName} selectedButtons={value as boolean[]}></CircularButtonSelection></div>
            )}
            {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
          </div>
        );
      })}

    </form>
  );
};

export default DynamicForm;
