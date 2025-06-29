export type Field = {
  fieldName: string;
  description: string;
  fieldType: "INPUT" | "SELECT" | "CHECKBOX";
  varType: "INT" | "REAL" | "STR" | "BOOL";
  defaultValue: boolean|string|number;
  required?: boolean;
  possibleValue?: string[];
};


export type FieldType = boolean|number|string;