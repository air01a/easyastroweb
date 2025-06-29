import json
from pathlib import Path
from typing import Dict, Union, List, Any
import asyncio

from utils.configlayoutparser import load_layout, get_item_to_save_from_layout

ConfigEntry = Dict[str, Union[str, int, bool]]
ConfigList = List[ConfigEntry]
AllowedValue = Union[str, int, float, bool]

CONFIG: Dict[str, AllowedValue] = {}
CONFIG_SCHEME: ConfigList = []

CURRENT_DIR = Path(__file__).parent
CONFIG_PATH = CURRENT_DIR.parent / "config" / "config.json"
CONFIG_SCHEMA_PATH = CURRENT_DIR.parent / "config" / "configschema.json"
OBSERVATORY_PATH = CURRENT_DIR.parent / "config" / "observatory.json"
OBSERVATORY_SCHEMA_PATH = CURRENT_DIR.parent / "config" / "observatoryschema.json"

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

    CONFIG.clear()
    CONFIG.update(new_config)

async def load_config_async() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, load_config)

async def save_config(config: Dict[str, AllowedValue]) -> bool:
    global CONFIG_SCHEME

    config_to_save = get_item_to_save_from_layout(config, CONFIG_SCHEME)
    await write_json(CONFIG_PATH, config_to_save)
    return True

async def get_observatory() -> ConfigList:
    return await read_json(OBSERVATORY_PATH)

async def get_observatory_schema() -> Dict[str, AllowedValue]:
    return await read_json(OBSERVATORY_SCHEMA_PATH)

async def save_observatory(observatory: List[Dict[str, AllowedValue]]):
    await write_json(OBSERVATORY_PATH, observatory)

load_config()