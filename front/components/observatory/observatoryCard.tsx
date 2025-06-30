import type {  ConfigItems } from '../../store/config.type';
import CircularButtonSelection from '../forms/circularbutton';


export type Props = {
    item: ConfigItems;
}

export const ObservatoryCard: React.FC<Props> = ({item}) => {
    return (
        <div>
            <h3 className="text-lg font-semibold">{item.name}</h3>
            <p className="text-gray-700">{item.longitude} / {item.latitude} / { item.altitude }</p>
            <div > <CircularButtonSelection miniature={true} selectedButtons={item.visibility? item.visibility as boolean[]: Array(36).fill(true)} name={item.name as string} editable={false} ></CircularButtonSelection></div>
        </div>);
}