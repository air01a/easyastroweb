import React, { useState } from "react";
import CreatableSelect from "react-select/creatable";

const options = [
  { value: "Option 1", label: "Option 1" },
  { value: "Option 2", label: "Option 2" },
];

export default function ComboBoxSelect() {
  const [selected, setSelected] = useState<{ label: string; value: string } | null>(null);

  return (
    <div>
      <label className="block font-bold">Choisir ou saisir :</label>
      <CreatableSelect
        isClearable
        onChange={(value) => setSelected(value)}
        options={options}
      />
      <p className="mt-2">Valeur sélectionnée : <strong>{selected?.value || "-"}</strong></p>
    </div>
  );
}
