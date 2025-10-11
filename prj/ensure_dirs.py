import os
import sys
from pathlib import Path





def ensure_dirs():
    """Создает все необходимые папки только при запуске из EXE"""
    # Создаем папки ТОЛЬКО при запуске из собранного EXE
    if getattr(sys, 'frozen', False):
        base_dir = Path(os.path.dirname(sys.executable))
        
        # Создаем папки save рядом с EXE-файлом
        for directory in ['save', 'save/config', 'save/projects']:
            dir_path = base_dir / directory
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # Создаем базовые конфиги
        config_files = {
            'save/config/columns_config.json': '["Длина", "Ширина", "Кол-во", "Толщина", "Сторон", "Тип детали", "Краска", "Комментарий", "Ручка"]',
            'save/config/facade_types.json': '["мыло", "фр", "фр + мыло", "планка", "глянец", "шпон", "жалюзи", "нестандарт"]',
            'save/config/work_types.json': '["Подготовка", "Грунтовка", "Покраска", "Замотка", "Полировка"]',
            'save/config/rates.json': '{}',
            'save/config/workers.json': '{"Подготовка": "", "Грунтовка": "Сергей", "Покраска": "Артём мал.", "Замотка": "Саша", "Полировка": "Сергей", "Склейка": ""}',
            'save/config/paint_consumption.json': '0.35',
            'save/config/style_settings.json': '{"separator_height": 5, "max_rows_per_page": 25}'  # Добавляем новый файл
        }
        
        for file_path, default_content in config_files.items():
            full_path = base_dir / file_path
            if not full_path.exists():
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(default_content)

# Вызываем при импорте
ensure_dirs()