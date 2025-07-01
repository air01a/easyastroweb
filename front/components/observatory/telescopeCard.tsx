import type { ConfigItems } from '../../store/config.type';

export type Props = {
  item: ConfigItems;
};

export const TelescopeCard: React.FC<Props> = ({ item }) => {
  return (
    <div
      className="
        w-full
         md:rounded md:p-4 md:shadow-sm
        space-y-3
      "
    >
      <h3 className="text-lg font-semibold text-gray-800">{item.name}</h3>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-700">
        <div>
          <dt className="font-medium text-gray-500">Focale</dt>
          <dd className="text-gray-400">{item.focale ?? "-"}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-500">Taille pixel</dt>
          <dd className="text-gray-400">{item.pixel_size ?? "-"}</dd>
        </div>
      </dl>
    </div>
  );
};
