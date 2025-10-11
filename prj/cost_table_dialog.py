# cost_table_dialog.py
from imports import *
from cost_calculator import CostCalculator
from constants import DEFAULT_WORK_TYPES
from work_types_config import load_work_types

class CostTableDialog(QDialog):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.calculator = CostCalculator()
        self.setWindowTitle('Стоимость работ')
        self.resize(1200, 600)  # Увеличиваем ширину для новых колонок
        
        self.init_ui()
        self.calculate_costs()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Таблица стоимости
        self.table = QTableWidget()
        layout.addWidget(self.table)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def calculate_costs(self):
        # Собираем данные таблицы
        table_data = []
        for row in range(self.main_window.table.rowCount()):
            row_data = []
            for col in range(self.main_window.table.columnCount()):
                item = self.main_window.table.item(row, col)
                row_data.append(item.text() if item else '')
            table_data.append(row_data)
        
        # Рассчитываем стоимость
        results = self.calculator.calculate_costs(table_data, self.main_window.columns, 
                                                 self.main_window.detail_types)
        
        # Заполняем таблицу
        self.update_table(results)

    def update_table(self, results):
        # Определяем все типы фасадов из результатов
        all_detail_types = set()
        has_additional_work = False  # Флаг наличия дополнительных работ
        
        for work_data in results.values():
            all_detail_types.update(work_data.get('by_detail', {}).keys())
            if work_data.get('additional_cost', 0) > 0:
                has_additional_work = True
        
        detail_types = sorted(list(all_detail_types))
        
        # Загружаем актуальные типы работ
        work_types = load_work_types()
        
        # Получаем work_types в порядке из конфига, но только те, которые реально используются
        used_work_types = []
        for work_type in work_types:
            # Проверяем, есть ли ненулевые ставки для этого типа работ
            has_non_zero_rates = False
            for detail_type in detail_types:
                rate_key = f"{work_type}_{detail_type}"
                rate = self.calculator.rates.get(rate_key, 0)
                if rate > 0:
                    has_non_zero_rates = True
                    break
            
            # Проверяем, есть ли данные в результатах
            has_data = work_type in results and (results[work_type]['total_cost'] > 0 or 
                                                results[work_type].get('additional_cost', 0) > 0)
            
            if has_non_zero_rates or has_data:
                used_work_types.append(work_type)

        # Формируем заголовки
        headers = ['Тип работ']
        headers.extend(detail_types)
        
        # Добавляем колонку "Доп. работы" только если есть дополнительные работы
        if has_additional_work:
            headers.append('Доп. работы')
        
        headers.extend(['Общая стоимость', 'Исполнитель'])
        
        self.table.setRowCount(len(used_work_types) + 1)  # +1 для итоговой строки
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Переменная для подсчета общей суммы
        total_cost_sum = 0
        
        # Заполняем данные
        for row, work_type in enumerate(used_work_types):
            if work_type not in results:
                # Пустая строка для типа работы без данных
                self.table.setItem(row, 0, QTableWidgetItem(work_type))
                
                # Заполняем нулями для всех типов фасадов
                for col in range(1, len(detail_types) + 1):
                    self.table.setItem(row, col, QTableWidgetItem('0 ₽'))
                
                # Доп. работы (только если есть)
                if has_additional_work:
                    self.table.setItem(row, len(detail_types) + 1, QTableWidgetItem('0 ₽'))
                
                # Общая стоимость и исполнитель
                col_offset = len(detail_types) + (1 if has_additional_work else 0)
                self.table.setItem(row, col_offset + 1, QTableWidgetItem('0 ₽'))
                self.table.setItem(row, col_offset + 2, QTableWidgetItem(self.calculator.workers.get(work_type, '')))
                continue
                
            data = results[work_type]
            
            # Колонка 0: Тип работ
            self.table.setItem(row, 0, QTableWidgetItem(work_type))
            
            # Колонки 1+: По типам фасадов (стоимость, округляем до целых)
            for col, detail_type in enumerate(detail_types, 1):
                if detail_type in data['by_detail']:
                    detail_data = data['by_detail'][detail_type]
                    cost = round(detail_data['cost'])
                    self.table.setItem(row, col, QTableWidgetItem(f"{cost} ₽"))
                else:
                    self.table.setItem(row, col, QTableWidgetItem('0 ₽'))
            
            # Колонка доп. работ (только если есть)
            if has_additional_work:
                additional_cost = round(data.get('additional_cost', 0))
                self.table.setItem(row, len(detail_types) + 1, QTableWidgetItem(f"{additional_cost} ₽"))
            
            # Колонка общей стоимости
            col_offset = len(detail_types) + (1 if has_additional_work else 0)
            total_cost = round(data['total_cost'])
            self.table.setItem(row, col_offset + 1, QTableWidgetItem(f"{total_cost} ₽"))
            total_cost_sum += total_cost
            
            # Колонка исполнителя
            self.table.setItem(row, col_offset + 2, QTableWidgetItem(self.calculator.workers.get(work_type, '')))
        
        # Добавляем итоговую строку
        total_row = len(used_work_types)
        col_offset = len(detail_types) + (1 if has_additional_work else 0)
        
        self.table.setItem(total_row, 0, QTableWidgetItem('ИТОГО'))
        
        # Пропускаем колонки с типами фасадов и доп. работами
        for col in range(1, col_offset + 1):
            self.table.setItem(total_row, col, QTableWidgetItem(''))
        
        # В колонке "Общая стоимость" выводим сумму
        self.table.setItem(total_row, col_offset + 1, QTableWidgetItem(f"{total_cost_sum} ₽"))
        
        # Колонка исполнителя оставляем пустой
        self.table.setItem(total_row, col_offset + 2, QTableWidgetItem(''))
        
        # Настраиваем внешний вид
        self.table.resizeColumnsToContents()
        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 40)
        
        # Подгоняем размер окна под таблицу
        total_width = sum([self.table.columnWidth(i) for i in range(self.table.columnCount())]) + 50
        total_height = sum([self.table.rowHeight(i) for i in range(self.table.rowCount())]) + 100
        
        # Ограничиваем максимальный размер
        screen_geometry = QApplication.desktop().availableGeometry()
        max_width = screen_geometry.width() * 0.8
        max_height = screen_geometry.height() * 0.8
        
        self.resize(min(total_width, max_width), min(total_height, max_height))
        
        # Центрируем окно
        self.move(screen_geometry.center() - self.rect().center())