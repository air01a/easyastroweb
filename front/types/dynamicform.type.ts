export type Field = {
  fieldName: string;
  description: string;
  fieldType: "INPUT" | "SELECT" | "CHECKBOX" | "CIRCULAR";
  varType: "INT" | "FLOAT" | "STR" | "BOOL" | "BOOLARRAY";
  defaultValue: boolean|string|number|boolean[];
  required?: boolean;
  possibleValue?: string[];
};


export type FieldType = boolean|number|string|boolean[];