export type Field = {
  fieldName: string;
  description: string;
  fieldType: "INPUT" | "SELECT" | "CHECKBOX";
  varType: "INT" | "REAL" | "STR" | "BOOL";
  defaultValue: boolean|string|number;
  possibleValue?: string[];
};