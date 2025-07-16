import SelectInput  from '../../design-system/inputs/select'
import Input  from '../../design-system/inputs/input'
import ToggleButton from '../../design-system/buttons/toggle';
import { useTranslation } from 'react-i18next';

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
  const { t } = useTranslation();
  return (
    <div className="flex flex-wrap gap-2 p-2 items-center justify-center mb-2">
      <Input value={filters.keywords || ''}
        onChange={(e) => setFilters({ ...filters, keywords: e.target.value })} placeholder={t('catalog.filter')}/>
      <ToggleButton
        onClick={() => toggle('invisible')}
        active={filters.invisible}
      >
        {t('catalog.invisbleObjects')}
      </ToggleButton>
      <ToggleButton
        onClick={() => toggle('hidden')}
       active={filters.hidden}
      >
        {t('catalog.masked')}
      </ToggleButton>
      <ToggleButton
        onClick={() => toggle('partial')}
        active = { filters.partial }
      >
        {t('catalog.partially')}
      </ToggleButton>
          <div className="mb-4 flex flex-col items-center">
      <label htmlFor="object-type" className="block text-sm font-medium text-gray-200">
        {t('catalog.objectType')} :
      </label>
      <SelectInput
        id="object-type"
        value={filters.type}
        onChange={(e) => setFilters({ ...filters, type: e.target.value })}
      >
        {objectTypes.map((type) => (
          <option key={type} value={type}>
            {t(`catalog.${type}`)}
          </option>
        ))}
      </SelectInput>
    </div>
    </div>
  );
}
