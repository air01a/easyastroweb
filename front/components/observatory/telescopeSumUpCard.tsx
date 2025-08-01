import type { ConfigItems } from '../../store/config.type';
import { useTranslation } from 'react-i18next';

export type Props = {
  telescope: ConfigItems;
  camera: ConfigItems;
  filterWheel: ConfigItems;
};

export const TelescopeSumUpCard: React.FC<Props> = ({ telescope, camera, filterWheel }) => {
  const  sampling = 57.3 * 10e-4 * (camera.pixel_size as number ?? 0) / (telescope.focale as number ?? 1)
  const horizontalFov = sampling * (camera.horizontal_pixels as number);
  const verticalFov = sampling * (camera.vertical_pixels as number);
  const { t } = useTranslation();

  return (
    <div
      className="
        w-full
         md:rounded md:p-4 md:shadow-sm
        space-y-3
      "
    >
      <h3 className="text-lg font-semibold text-gray-100">{telescope.name}</h3>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-700">
        <div>
          <dt className="font-medium text-gray-500">{t('global.focale')}</dt>
          <dd className="text-gray-400">{telescope.focale ?? "-"} mm</dd>
        </div>
        <div>
          <dt className="font-medium text-gray-500">{t('global.apperture')}</dt>
          <dd className="text-gray-400">{telescope.apperture ?? "-"} mm</dd>
        </div>
       </dl>
              <h3 className="text-lg font-semibold text-gray-100 w-full mr-500">{camera.name}</h3>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-700">
        <div>
          <dt className="font-medium text-gray-500">{t('global.pixelSize')}</dt>
          <dd className="text-gray-400">{camera.pixel_size ?? "-"} µm</dd>
        </div>
                <div>
          <dt className="font-medium text-gray-500">{t('global.captorSize')}</dt>
          <dd className="text-gray-400">{camera.horizontal_pixels ?? "?"} x {camera.vertical_pixels ?? "?"}</dd>
        </div>
         <div>
          <dt className="font-medium text-gray-500">{t('global.fov')}</dt>
          <dd className="text-gray-400">{horizontalFov.toFixed(2)}° x {verticalFov.toFixed(2)}°</dd>
        </div>
      </dl>
      {filterWheel && filterWheel.filters && (
        <div>
            <h3 className="text-lg font-semibold text-gray-100">{filterWheel.name ?? '-'}</h3>
            <div>
              <dt className="font-medium text-gray-500">{t('global.filters')}</dt>
              <dd className="text-gray-400">{(filterWheel.filters as string[]).length}</dd>
          </div>
        </div>
        )
      }
    </div>
  );
};
