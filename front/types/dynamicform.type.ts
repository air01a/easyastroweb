export type FieldType = boolean|number|string|boolean[]|string[];

export type Field = {
  fieldName: string;
  description: string;
  fieldType: "INPUT" | "SELECT" | "CHECKBOX" | "CIRCULAR" | "MULTIPLEINPUT" | "SEPARATOR";
  varType: "INT" | "FLOAT" | "STR" | "BOOL" | "BOOLARRAY" | "STRARRAY" | "NONE";
  defaultValue: FieldType;
  required?: boolean;
  possibleValue?: string[];
};


