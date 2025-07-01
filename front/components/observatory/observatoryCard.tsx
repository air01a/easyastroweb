import type { ConfigItems } from '../../store/config.type';
import CircularButtonSelection from '../forms/circularbutton';

export type Props = {
  item: ConfigItems;
};

export const ObservatoryCard: React.FC<Props> = ({ item }) => {
  return (
    <div
        className="
            w-full
            md:rounded md:p-4 md:shadow-sm
            space-y-3
            flex flex-col justify-center items-center
        "
        >
      <h3 className="text-lg font-semibold text-gray-600">{item.name}</h3>
      
      <dl className="flex flex-row gap-x-4 gap-y-1 text-sm text-gray-700">
        <div>
          <dt className="font-medium text-gray-400 mr-4">Longitude</dt>
          <dd className="text-gray-400">{item.longitude ?? "-"}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-400 mr-4">Latitude</dt>
          <dd className="text-gray-400">{item.latitude ?? "-"}</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-400">Altitude</dt>
          <dd className="text-gray-400">{item.altitude ?? "-"} m</dd>
        </div>
      </dl>

      <div>
        <CircularButtonSelection
          miniature={true}
          selectedButtons={
            item.visibility
              ? (item.visibility as boolean[])
              : Array(36).fill(true)
          }
          name={item.name as string}
          editable={false}
        />
      </div>
    </div>
  );
};
