# work_types_config.py
from imports import *
from constants import DEFAULT_WORK_TYPES
from file_operations import ensure_dirs

WORK_TYPES_FILE = 'save/config/work_types.json'

def load_work_types():
    ensure_dirs()
    try:
        with open(WORK_TYPES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list) or not data:
                raise ValueError
            return data
    except Exception:
        return DEFAULT_WORK_TYPES[:]

def save_work_types(work_types):
    ensure_dirs()
    with open(WORK_TYPES_FILE, 'w', encoding='utf-8') as f:
        json.dump(work_types, f, ensure_ascii=False, indent=2)