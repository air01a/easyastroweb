import { useState } from "react";
import CreatableSelect from "react-select/creatable";
import type { StylesConfig } from "react-select";

type OptionType = { label: string; value: string };



const customStyles: StylesConfig<OptionType, false> = {
  control: (base, state) => ({
    ...base,
    backgroundColor: "#1f2937", // bg-gray-800
    borderColor: "#ffffff",     // border-white
    color: "#ffffff",
    paddingTop: "0.25rem",      // py-2 (top)
    paddingBottom: "0.25rem",   // py-2 (bottom)
    paddingLeft: "0.75rem",     // px-3
    paddingRight: "0.75rem",
    borderRadius: "0.375rem",   // rounded
    boxShadow: state.isFocused ? "0 0 0 2px #ffffff" : "none", // focus:ring-2 focus:ring-white
    "&:hover": {
      borderColor: "#ffffff",
    },
  }),
  singleValue: (base) => ({
    ...base,
    color: "#ffffff", // text-white
  }),
  input: (base) => ({
    ...base,
    color: "#ffffff", // placeholder-white
  }),
  placeholder: (base) => ({
    ...base,
    color: "#ffffff",
  }),
  menu: (base) => ({
    ...base,
    backgroundColor: "#1f2937", // bg-gray-800 for dropdown
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isFocused ? "#374151" : "#1f2937", // hover:bg-gray-700
    color: "#ffffff",
    cursor: "pointer",
  }),
};

export default function ComboBoxSelect({options, defaultValue,  onSelectValue}: {options:OptionType[], defaultValue:OptionType, onSelectValue: (value:string)=>void}) {
  const [selected, setSelected] = useState<OptionType | null>(defaultValue);

  return (
    <div className="ml-3">
      <CreatableSelect
        isClearable
        onChange={(value) => { setSelected(value); onSelectValue(value?.value ||'')}}
        options={options}
        styles={customStyles}
        value={selected}
        placeholder="Choisissez ou écrivez..."
      />
    </div>
  );
}
