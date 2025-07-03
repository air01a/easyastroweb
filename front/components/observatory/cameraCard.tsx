import type { ConfigItems } from '../../store/config.type';

export type Props = {
  item: ConfigItems;
};

export const CameraCard: React.FC<Props> = ({ item }) => {

  //const  sampling = 57.3 * 10e-4 * (item.pixel_size as number ?? 0) / (item.focale as number ?? 1)
  //const horizontalFov = sampling * (item.horizontal_pixels as number);
  //const verticalFov = sampling * (item.vertical_pixels as number);


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
          <dt className="font-medium text-gray-500">Taille pixel</dt>
          <dd className="text-gray-400">{item.pixel_size ?? "-"} µm</dd>
        </div>
                <div>
          <dt className="font-medium text-gray-500">Taille capteur</dt>
          <dd className="text-gray-400">{item.horizontal_pixels ?? "?"} x {item.vertical_pixels ?? "?"}</dd>
        </div>

      </dl>
    </div>
  );
};
