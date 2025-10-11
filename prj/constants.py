from PyQt5.QtCore import Qt  # Добавлено в начало файла

# ---------- Константы ----------
CONFIG_DIR = 'save/config'
PROJECTS_DIR = 'save/projects'
SAVE_DIR = 'save'

AUTOSAVE_FILE = 'save/config/autosave.json'  # Автосохранение в папке config

RATES_FILE = 'save/config/rates.json'
FACADE_FILE = 'save/config/facade_types.json'
COLUMNS_FILE = 'save/config/columns_config.json'
WORKERS_FILE = 'save/config/workers.json'
STYLE_SETTINGS_FILE = 'save/config/style_settings.json'
OTHER_SETTINGS_FILE = 'save/config/other_settings.json'
CONFIG_FILE = 'save/config/config.json'
WORKERS_FILE = 'save/config/workers.json'
WRAPPING_RATE_FILE = 'save/config/wrapping_rate.json'



DEFAULT_SEPARATOR_HEIGHT = 5
DEFAULT_MAX_ROWS_PER_PAGE = 25
DEFAULT_PAINT_CONSUMPTION = 0.35  # кг/м² (350 гр/м²)
# Можно добавить константы для печати если понадобится
PRINT_MARGIN = 12  # мм
PRINT_TABLE_SPACING = 15  # мм




DEFAULT_WORK_TYPES = ['Подготовка', 'Грунтовка', 'Покраска', 'Замотка', 'Полировка']
DEFAULT_DETAIL_TYPES = ['мыло', 'фр', 'фр + мыло', 'планка', 'глянец', 'шпон', ' жалюзи', 'нестандарт']
DEFAULT_COLUMNS = ['Длина', 'Ширина', 'Кол-во', 'Толщина', 'Сторон', 'Тип детали', 'Краска', 'Комментарий', 'Ручка', 'Склейка']
MAIN_COLUMNS = ['Длина', 'Ширина', 'Кол-во', 'Тип детали']
NUMERIC_FIELDS = {'Длина', 'Ширина', 'Кол-во', 'Толщина', 'Сторон', 'Ручка'}
DEFAULT_WORKERS = {
    'Подготовка': '',
    'Грунтовка': 'Сергей', 
    'Покраска': 'Артём мал.',
    'Замотка': 'Саша',
    'Полировка': 'Сергей',
    'Склейка': ''
}


# Константы для разделителей
SEPARATOR_WIDTH = 3  # толщина разделителей в пикселях
SEPARATOR_COLOR = Qt.darkGray  # цвет разделителей
SEPARATOR_STYLE = "solid"  # стиль разделителей

# Индексы колонок для ограничения разделителей
SEPARATOR_LIMIT_COLUMNS = {
    'detail_type': 'Тип детали',  # разделитель типа фасадов доходит только до этой колонки
    'paint': 'Краска'  # разделитель краски доходит только до этой колонки
}

# Константы для разделителей (обновить существующие)
SEPARATOR_HEIGHT = 5  # высота разделителей в мм (будет переопределяться из настроек)
MAX_ROWS_PER_PAGE = 25  # максимальное количество строк на странице печати