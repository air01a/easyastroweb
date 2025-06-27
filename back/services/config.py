import json
from pathlib import Path
from typing import Dict, Union

AllowedValue = Union[str, int, float, bool]
from typing import List, Dict, Union
from utils.configlayoutparser import load_layout, get_item_to_save_from_layout

ConfigEntry = Dict[str, Union[str, int, bool]]
ConfigList = List[ConfigEntry]


CONFIG: Dict[str, AllowedValue] = {}
CONFIG_SCHEME : ConfigList = []

CURRENT_DIR = Path(__file__).parent
CONFIG_PATH = CURRENT_DIR.parent / "config" / "config.json"
CONFIG_SCHEME_PATH = CURRENT_DIR.parent / "config" / "configschema.json"


def load_config() -> None:
    global CONFIG
    global CONFIG_SCHEME
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            tmp_config = json.load(f)

    with CONFIG_SCHEME_PATH.open("r", encoding="utf-8") as f:
        CONFIG_SCHEME = json.load(f)
    
    new_config = load_layout(tmp_config, CONFIG_SCHEME)
    CONFIG.clear()
    for key, value in new_config.items():
        CONFIG[key]=value


def save_config(config:Dict[str, AllowedValue]) -> bool:
    global CONFIG
    global CONFIG_SCHEME
    config_to_save = {}

    config_to_save = get_item_to_save_from_layout(config, CONFIG_SCHEME)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_to_save, f, indent=4)

load_config()
