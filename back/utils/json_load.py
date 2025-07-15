import json
from pathlib import Path

def load_array_form_json(name: Path):
    if name.exists():
        with name.open("r", encoding="utf-8") as f:
            tmp_config = json.load(f)
            return tmp_config
    return []