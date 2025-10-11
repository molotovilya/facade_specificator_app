
from imports import *
from constants import *
import re
import os
from pathlib import Path
import json

def ensure_dirs():
    """Создает все необходимые папки (дублирующая функция - оставляем пустой)"""
    # Теперь эта функция ничего не делает, т.к. ensure_dirs.py уже все создает
    # Но добавим создание файла wrapping_rate.json если его нет
    try:
        if not os.path.exists(WRAPPING_RATE_FILE):
            with open(WRAPPING_RATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(120.0, f)  # Значение по умолчанию
    except:
        pass

def load_workers():
    ensure_dirs()
    try:
        with open(WORKERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return DEFAULT_WORKERS.copy()

def save_workers(workers: dict):
    ensure_dirs()
    with open(WORKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(workers, f, ensure_ascii=False, indent=2)

def ensure_dirs():
    """Создает все необходимые папки (дублирующая функция - оставляем пустой)"""
    # Теперь эта функция ничего не делает, т.к. ensure_dirs.py уже все создает
    # Оставляем для обратной совместимости
    pass

def ensure_facade_file():
    ensure_dirs()
    p = Path(FACADE_FILE)
    if not p.exists():
        with p.open('w', encoding='utf-8') as f:
            json.dump(DEFAULT_DETAIL_TYPES, f, ensure_ascii=False, indent=2)

def ensure_projects_dir():
    ensure_dirs()

def load_facade_types():
    ensure_facade_file()
    try:
        with open(FACADE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list) or not data:
                raise ValueError
            return list(dict.fromkeys(data))
    except Exception:
        return DEFAULT_DETAIL_TYPES[:]

def save_facade_types(types: list):
    ensure_dirs()
    with open(FACADE_FILE, 'w', encoding='utf-8') as f:
        json.dump(types, f, ensure_ascii=False, indent=2)

def load_rates():
    ensure_dirs()
    try:
        with open(RATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_rates(rates: dict):
    ensure_dirs()
    with open(RATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(rates, f, ensure_ascii=False, indent=2)

def load_columns_config():
    ensure_dirs()
    try:
        with open(COLUMNS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list) or not data:
                raise ValueError
            return data
    except Exception:
        return DEFAULT_COLUMNS[:]

def save_columns_config(columns: list):
    ensure_dirs()
    with open(COLUMNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(columns, f, ensure_ascii=False, indent=2)

def get_next_project_number():
    ensure_dirs()
    projects_dir = Path(PROJECTS_DIR)
    existing_numbers = []
    
    try:
        for file in projects_dir.glob('*.json'):
            try:
                # Извлекаем номер из имени файла
                filename = file.stem
                # Ищем первую цифру в имени файла
                number_match = re.search(r'^(\d+)', filename)
                if number_match:
                    number = int(number_match.group(1))
                    existing_numbers.append(number)
            except (ValueError, IndexError, AttributeError):
                # Пропускаем файлы с некорректными именами
                continue
        
        if existing_numbers:
            return max(existing_numbers) + 1
        else:
            return 1
            
    except Exception:
        return 1

def save_project_data(project_data: dict, filepath=None):
    ensure_dirs()
    
    customer_name = project_data.get('customer_name', '').replace('_', '-')
    date_str = project_data.get('project_date', QDateTime.currentDateTime().toString('dd.MM.yyyy'))
    date_filename = date_str.replace('.', '-')
    
    project_number = project_data.get('project_number') or get_next_project_number()
    
    if not filepath:
        if customer_name:
            filename = f"{project_number}_{customer_name}_{date_filename}.json"
        else:
            filename = f"{project_number}_{date_filename}.json"
        filepath = Path(PROJECTS_DIR) / filename
    else:
        filename = Path(filepath).name
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    
    return project_number, filename

def load_project_data(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Ошибка загрузки файла: {str(e)}")

def get_saved_projects():
    ensure_dirs()
    projects_dir = Path(PROJECTS_DIR)
    projects = []
    
    for file in sorted(projects_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            filename = file.stem
            parts = filename.split('_')
            project_number = parts[0] if len(parts) > 0 else 'N/A'
            customer_name = parts[1] if len(parts) > 1 else 'Неизвестный'
            
            # ИСПОЛЬЗУЕМ ДАТУ ИЗ ДАННЫХ ПРОЕКТА В ФОРМАТЕ dd.MM.yyyy
            date = data.get('project_date', 'N/A')
                
            projects.append({
                'filepath': str(file),
                'number': project_number,
                'customer': customer_name,
                'date': date,
                'name': f"№{project_number} - {customer_name} - {date}"
            })
        except:
            continue
    
    return projects

def load_config():
    ensure_dirs()
    try:
        config_path = Path(CONFIG_FILE)
        if not config_path.exists():
            # Создаем default config если файла нет
            default_config = {
                'last_project': None, 
                'window_geometry': None,
                'window_maximized': True  # Добавим флаг полноэкранного режима
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            return default_config
            
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'last_project': None, 'window_geometry': None, 'window_maximized': True}
    
def save_config(config):
    ensure_dirs()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_paint_consumption():
    ensure_dirs()
    try:
        with open('save/config/paint_consumption.json', 'r', encoding='utf-8') as f:
            return float(json.load(f))
    except Exception:
        return DEFAULT_PAINT_CONSUMPTION

def save_paint_consumption(consumption):
    ensure_dirs()
    with open('save/config/paint_consumption.json', 'w', encoding='utf-8') as f:
        json.dump(consumption, f, ensure_ascii=False, indent=2)

def save_autosave(data):
    """Сохраняет данные автосохранения"""
    ensure_dirs()
    try:
        with open(AUTOSAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка автосохранения: {e}")
        return False

def load_autosave():
    """Загружает данные автосохранения"""
    ensure_dirs()
    try:
        with open(AUTOSAVE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def delete_autosave():
    """Удаляет файл автосохранения"""
    try:
        if os.path.exists(AUTOSAVE_FILE):
            os.remove(AUTOSAVE_FILE)
    except:
        pass

def load_style_settings():
    ensure_dirs()
    try:
        with open(STYLE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Устанавливаем значения по умолчанию для всех полей
            defaults = {
                'separator_height': DEFAULT_SEPARATOR_HEIGHT,
                'max_rows_per_page': DEFAULT_MAX_ROWS_PER_PAGE
            }
            for key, value in defaults.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except Exception:
        return {
            'separator_height': DEFAULT_SEPARATOR_HEIGHT,
            'max_rows_per_page': DEFAULT_MAX_ROWS_PER_PAGE
        }

def save_style_settings(settings):
    ensure_dirs()
    with open(STYLE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def load_other_settings():
    ensure_dirs()
    try:
        with open(OTHER_SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Устанавливаем значения по умолчанию для всех полей
            defaults = {
                "paint_consumption": 0.35,
                "wrapping_rate": 140.0,
                "gluing_rate": 150.0,
                "handle_rate": 60.0,
                "taping_rate": 50.0

            }
            for key, value in defaults.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except Exception:
        return {
            "paint_consumption": 0.35,
            "wrapping_rate": 140.0,
            "gluing_rate": 150.0,
            "handle_rate": 60.0,
            "taping_rate": 50.0
        }

def save_other_settings(settings):
    ensure_dirs()
    with open(OTHER_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


