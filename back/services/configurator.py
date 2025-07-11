import json
from pathlib import Path
from typing import Dict, Union, List, Any
import asyncio
from models.api import ConfigAllowedValue
from utils.configlayoutparser import load_layout, get_item_to_save_from_layout
from utils.jsonload import load_array_form_json


ConfigEntry = Dict[str, Union[str, int, bool]]
ConfigList = List[ConfigEntry]

CONFIG : Dict[str,Dict[str, ConfigAllowedValue]] = {}

CONFIG['global'] = {}
CONFIG['telescope'] = {}
CONFIG['observatory'] = {}
CONFIG['camera'] = {}
CONFIG['filterwheel'] = {}


CURRENT_DIR = Path(__file__).parent
CONFIG_PATH = CURRENT_DIR.parent / "config" / "config.json"
CONFIG_SCHEMA_PATH = CURRENT_DIR.parent / "models" / "configschema.json"
OBSERVATORY_PATH = CURRENT_DIR.parent / "config" / "observatory.json"
OBSERVATORY_SCHEMA_PATH = CURRENT_DIR.parent / "models" / "observatoryschema.json"
TELESCOPE_PATH = CURRENT_DIR.parent / "config" / "telescope.json"
TELESCOPE_SCHEMA_PATH = CURRENT_DIR.parent / "models" / "telescopeschema.json"
DEFAULT_PATH = CURRENT_DIR.parent / "config" / "default.json"
CAMERAS_PATH = CURRENT_DIR.parent / "config" / "cameras.json"
CAMERAS_SCHEMA_PATH = CURRENT_DIR.parent / "models" / "cameraschema.json"
FILTERWHEELS_PATH = CURRENT_DIR.parent / "config" / "filterwheels.json"
FILTERWHEELS_SCHEMA_PATH = CURRENT_DIR.parent / "models" / "filterwheelsschema.json"

def find_item_from_name(name: str, config: ConfigList):
    for item in config:
        if "name" in item.keys():
            if item["name"]==name:
                return item
    return None


# Helper function to read JSON asynchronously
async def read_json(path: Path) -> Any:
    loop = asyncio.get_running_loop()
    def load():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return await loop.run_in_executor(None, load)

# Helper function to write JSON asynchronously
async def write_json(path: Path, data: Any):
    loop = asyncio.get_running_loop()
    def dump():
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    await loop.run_in_executor(None, dump)

def load_config() -> None:
    global CONFIG
    global CONFIG_SCHEME

    tmp_config = {}
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            tmp_config = json.load(f)

    with CONFIG_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        CONFIG_SCHEME = json.load(f)

    new_config = load_layout(tmp_config, CONFIG_SCHEME)

    CONFIG['global'].clear()
    CONFIG['global'].update(new_config)


def _get_default(key, default, path):
    items = load_array_form_json(path)

    item = None
    if key in default.keys():
        item = find_item_from_name(default[key], items)
    if not item and len(items)>0:
        item = items[0]
    return item
    

def load_defaults() -> None:
    global CONFIG


    default = load_array_form_json(DEFAULT_PATH)

    telescope = _get_default("telescope", default, TELESCOPE_PATH)
    observatory = _get_default("observatory", default, OBSERVATORY_PATH)
    camera = _get_default("camera", default, CAMERAS_PATH)
    wheel = _get_default("filterwheel", default, FILTERWHEELS_PATH)
    
    CONFIG["observatory"].clear()
    if observatory:
        CONFIG["observatory"].update(observatory)
    
    CONFIG["telescope"].clear()
    if telescope:
        CONFIG["telescope"].update(telescope)

    CONFIG["camera"].clear()
    if camera:
        CONFIG["camera"].update(camera)

    CONFIG["filterwheel"].clear()
    if wheel:
        CONFIG["filterwheel"].update(wheel)



async def load_config_async() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, load_config)

async def save_config(config: Dict[str, ConfigAllowedValue]) -> bool:
    global CONFIG_SCHEME

    config_to_save = get_item_to_save_from_layout(config, CONFIG_SCHEME)
    await write_json(CONFIG_PATH, config_to_save)
    return True


async def get_telescope_config(filepath: Path) -> ConfigList:
    if filepath.exists():
        return await read_json(filepath)
    return []

async def get_telescope_config_schema(filepath: Path) -> Dict[str, ConfigAllowedValue]:
    if filepath.exists():
        return await read_json(filepath)
    return []

async def save_telescope_config(filepath: Path, telescope_config: List[Dict[str, ConfigAllowedValue]], type:str, schema_path:Path) -> tuple[bool, str]:
    schema = await get_telescope_config_schema(schema_path)
    for item in telescope_config:
        error = await check_data_format(item, schema)
        if error:
            return (False, error)
    try : 
        await write_json(filepath, telescope_config)
    except Exception as e:
        return (False, str(e))
    await set_default_telescope_config(telescope_config[0]["name"],type, filepath)
    return (True, "No Error")


async def set_default_telescope_config(item: str, type: str, filepath: Path):
    global CONFIG
    await change_default(type, item)
    CONFIG[item] = find_item_from_name(item, await get_telescope_config(filepath))


async def get_default() -> Dict[str, ConfigAllowedValue]:
    if DEFAULT_PATH.exists():
        return await read_json(DEFAULT_PATH)
    return []

async def change_default(key, value) -> Dict[str, ConfigAllowedValue]:
    current = await get_default()
    current[key]=value
    await write_json(DEFAULT_PATH, current)



async def check_data_format(
    data: Dict[str, ConfigAllowedValue],
    schema: List[Dict[str, Any]]
) -> Union[None, str]:

    type_mapping = {
        "INT": (int,),
        "FLOAT": (float, int),  
        "BOOL": (bool,),
        "STR": (str,),
        "BOOLARRAY": (list,),
        "STRARRAY": (list,),
    }

    for item in schema:
        field_name = item["fieldName"]

        # Vérifier si le champ est présent
        if field_name in data:
            value = data[field_name]
            expected_types = type_mapping.get(item["varType"])

            if expected_types:
                if not isinstance(value, expected_types):
                    return f"Wrong data type for {field_name}"

                # Si c'est un BOOLARRAY, vérifier que tous les éléments sont des bool
                if item["varType"] == "BOOLARRAY":
                    if not all(isinstance(v, bool) for v in value):
                        return f"Invalid array content for {field_name}"
                if item["varType"] == "STRARRAY":
                    if not all(isinstance(v, str) for v in value):
                        return f"Invalid array content for {field_name}"
        else:
            if item.get("required", False):
                return f"Missing required field {field_name}"
    
    allowed_fields = {item["fieldName"] for item in schema}
    extra_fields = set(data.keys()) - allowed_fields
    if extra_fields:
        return f"Unexpected fields: {', '.join(extra_fields)}"
    return None

load_config()
load_defaults()