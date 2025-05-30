import { ConfigItems } from "./config.type";
import { getTxtFile } from "./fsutils";

let configItems : ConfigItems | null = null;

export const getConfiguration  = async () : Promise<ConfigItems> => {
    if (configItems) {
        return configItems;
    }
    const newConfigItems = JSON.parse(await getTxtFile('config/config.json'));
    configItems = newConfigItems;
    return newConfigItems as ConfigItems;
};

export const reloadConfiguration = async () : Promise<ConfigItems> => {
    configItems = null
    return getConfiguration();
}