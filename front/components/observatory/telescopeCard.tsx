import type {  ConfigItems } from '../../store/config.type';


export type Props = {
    item: ConfigItems;
}

export const TelescopeCard: React.FC<Props> = ({item}) => {
    return (
        <div>
            <h3 className="text-lg font-semibold">{item.name}</h3>
            <p className="text-gray-700">{item.focale} / {item.pixel_size}</p>
        </div>);
}