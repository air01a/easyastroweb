import type { ConfigItems } from '../../store/config.type';

export type Props = {
  item: ConfigItems;
};

export const FilterWheelsCard: React.FC<Props> = ({ item }) => {


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
          <dt className="font-medium text-gray-500">Number of filters</dt>
          <dd className="text-gray-400">{(item.filters as string[]).length ?? 1}</dd>
        </div>
      </dl>
      <div className="flex flex-wrap">
      { (item.filters as string[]).map((element) => { 
          return (<div className="text-gray-400 mr-4"> {element} </div>)
        })
      }
      </div>

    </div>
  );
};
