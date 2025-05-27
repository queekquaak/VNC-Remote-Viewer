import os
import json
from pathlib import Path

# The port of web-app
FRONTEND_PORT = os.getenv('FRONTEND_PORT', "5000")

# The port of api-server
API_SERVER_ADDR = os.getenv('API_SERVER_ADDR', "localhost:8080")

# Token for API validations
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "moneyprintergobrrr")

# VNC-server password for the view-only mode
VIEW_ONLY_PASS = os.getenv('VIEW_ONLY_PASS', "password")

# VNC compression value
VNC_COMPRESSION = os.getenv('VNC_COMPRESSION', '9')

# VNC render quality for tiles (1-9)
VNC_TILE_QUALITY = os.getenv('VNC_TILE_QUALITY', "1")

# VNC scale for tiles
VNC_TILE_SCALE = os.getenv('VNC_TILE_SCALE', "0.5")

# VNC render quality for fullscreen mode
VNC_FULLSCREEN_QUALITY = os.getenv('VNC_FULLSCREEN_QUALITY', "5")

# VNC scale for fullscreen mode
VNC_FULLSCREEN_SCALE = os.getenv('VNC_FULLSCREEN_SCALE', "0.8")

# Lists storage
LISTS_FILE = Path(__file__).parent.parent / 'data' / 'lists.json'


def load_lists():
    try:
        if LISTS_FILE.exists():
            with open(LISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"All Servers": []}
    except Exception:
        return {"All Servers": []}


def save_lists(lists):
    try:
        LISTS_FILE.parent.mkdir(exist_ok=True)
        with open(LISTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(lists, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving lists: {e}")
        raise


def to_dict() -> dict:
    """
    Return all UPPER‑CASE names from this module as a dict.
    """
    result = {}
    for name, value in globals().items():
        if name.isupper():
            if isinstance(value, Path):
                result[name] = str(value)
            else:
                result[name] = value
    return result
