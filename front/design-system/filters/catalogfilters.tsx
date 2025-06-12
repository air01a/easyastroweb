import SelectInput  from '../../design-system/inputs/select'
import Input  from '../../design-system/inputs/input'
import ToggleButton from '../../design-system/buttons/toggle'
type ObjectType =
  | 'all'
  | 'planet'
  | 'star'
  | 'galaxy'
  | 'globular_cluster'
  | 'open_cluster'
  | 'planetary_nebula'
  | 'dark_nebula';

const objectTypes: ObjectType[] = [
  'all',
  'planet',
  'star',
  'galaxy',
  'globular_cluster',
  'open_cluster',
  'planetary_nebula',
  'dark_nebula',
];


export default function CatalogFilters({ filters, setFilters }: {
  filters: { invisible: boolean; hidden: boolean; partial: boolean; keywords: string;    type : string | ObjectType;
},
  setFilters: (f: typeof filters) => void
}) {
  function toggle(key: keyof typeof filters) {
    setFilters({ ...filters, [key]: !filters[key] });
  }

  return (
    <div className="flex flex-wrap gap-2 p-2 items-center justify-center mb-2">
      <Input value={filters.keywords || ''}
        onChange={(e) => setFilters({ ...filters, keywords: e.target.value })} placeholder='Filter'/>
      <ToggleButton
        onClick={() => toggle('invisible')}
        active={filters.invisible}
      >
        Objets invisibles
      </ToggleButton>
      <ToggleButton
        onClick={() => toggle('hidden')}
       active={filters.hidden}
      >
        Objets masqués
      </ToggleButton>
      <ToggleButton
        onClick={() => toggle('partial')}
        active = { filters.partial }
      >
        Partiellement visibles
      </ToggleButton>
          <div className="mb-4">
      <label htmlFor="object-type" className="block text-sm font-medium text-gray-700">
        Type d'objet :
      </label>
      <SelectInput
        id="object-type"
        value={filters.type}
        onChange={(e) => setFilters({ ...filters, type: e.target.value })}
      >
        {objectTypes.map((type) => (
          <option key={type} value={type}>
            {type.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
          </option>
        ))}
      </SelectInput>
    </div>
    </div>
  );
}
