import React, { useEffect, useState } from "react";
import SelectInput  from '../../design-system/inputs/select'
import Input  from '../../design-system/inputs/input'
import Checkbox  from '../../design-system/inputs/checkbox'

import type {Field} from './dynamicform.type'

type Props = {
  formDefinition: Field[];
  initialValues?: Record<string, any>;
  onChange?: (values: Record<string, any>) => void;
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

  
  const validate = (field: Field, value: any): string | null => {
    switch (field.varType) {
      case "INT":
        return /^-?\d+$/.test(String(value)) ? null : "Entier attendu";
      case "REAL":
        return /^-?\d+(\.\d+)?$/.test(String(value)) ? null : "Nombre réel attendu";
      case "STR":
        return typeof value === "string" ? null : "Texte invalide";
      case "BOOL":
        return typeof value === "boolean" ? null : "Booléen attendu";
      default:
        return null;
    }
  };

  const handleChange = (field: Field, rawValue: any) => {
    let value: any = rawValue;

    if (field.fieldType === "CHECKBOX") {
      value = !!rawValue;
    }

    const error = validate(field, value);
    setErrors((prev) => ({ ...prev, [field.fieldName]: error || "" }));

    if (!error) {
      if (field.varType === "INT") value = parseInt(value);
      else if (field.varType === "REAL") value = parseFloat(value);
      const newFormData = { ...formData, [field.fieldName]: value };
      setFormData(newFormData);
      onChange?.(newFormData);

    }

  };


  return (
    <form >
      {formDefinition.map((field) => {
        const value = formData[field.fieldName];
        const error = errors[field.fieldName];

        return (
          <div key={field.fieldName} style={{ marginBottom: "1rem" }}>
            <label className="text-white mb-1">{field.description} : </label>

            {field.fieldType === "INPUT" && (
              <Input
                type="text"
                value={value}
                onChange={(e) => handleChange(field, e.target.value)}
              />
            )}

            {field.fieldType === "SELECT" && (
              <SelectInput
                value={value}
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
                
                checked={value}
                onChange={(e) => handleChange(field, e.target.checked)}
              />
            )}

            {error && <div className="text-red-400 text-sm mt-1">{error}</div>}
          </div>
        );
      })}

    </form>
  );
};

export default DynamicForm;
