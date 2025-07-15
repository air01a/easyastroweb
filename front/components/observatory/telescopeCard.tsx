import type { ConfigItems } from '../../store/config.type';
import { useTranslation } from 'react-i18next';

export type Props = {
  item: ConfigItems;
};

export const TelescopeCard: React.FC<Props> = ({ item }) => {
  const { t } = useTranslation();


  return (
    <div
      className="
        w-full
         md:rounded md:p-4 md:shadow-sm
        space-y-3
      "
    >
      <h3 className="text-lg font-semibold text-gray-100">{item.name}</h3>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-700">
        <div>
          <dt className="font-medium text-gray-500">{t('global.focale')}</dt>
          <dd className="text-gray-400">{item.focale ?? "-"} mm</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-500">{t('global.apperture')}</dt>
          <dd className="text-gray-400">{item.apperture ?? "-"} mm</dd>
        </div>

      </dl>
    </div>
  );
};
