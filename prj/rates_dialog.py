from imports import *
from constants import *
from file_operations import save_rates, load_workers, save_workers
# ДОБАВИТЬ ИМПОРТ ↓
from work_types_config import load_work_types

class RatesDialog(QDialog):
    def __init__(self, rates: dict, get_work_types, get_detail_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Настройка ставок и исполнителей')
        self.rates = rates
        self.get_work_types = get_work_types
        self.get_detail_types = get_detail_types
        self.workers = load_workers()
        self.resize(900, 400)
        layout = QVBoxLayout(self)

        # Загружаем актуальные типы работ
        self.work_types = load_work_types()
        
        # Загружаем детали и отфильтровываем комбинированные фасады (с '+')
        all_detail_types = self.get_detail_types()
        self.detail_types = [d for d in all_detail_types if '+' not in d]

        # Создаем таблицу с дополнительной колонкой для исполнителей
        self.table = QTableWidget(len(self.work_types), len(self.detail_types) + 1, self)
        
        # Устанавливаем заголовки
        headers = self.detail_types + ['Исполнитель']
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setVerticalHeaderLabels(self.work_types)
        
        # Настраиваем resize policy
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(len(self.detail_types), QHeaderView.ResizeToContents)

        # Заполняем таблицу ставок
        for i, work in enumerate(self.work_types):
            for j, detail in enumerate(self.detail_types):
                key = f"{work}_{detail}"
                val = self.rates.get(key, 0)
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, j, item)
            
            # Добавляем ячейку для исполнителя
            worker = self.workers.get(work, '')
            worker_item = QTableWidgetItem(worker)
            worker_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, len(self.detail_types), worker_item)

        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btn_save = QPushButton('Сохранить', self, clicked=self.save_rates)
        btn_cancel = QPushButton('Отмена', self, clicked=self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def save_rates(self):
        new_rates = {}
        new_workers = {}
        
        for i, work in enumerate(self.work_types):
            # Сохраняем исполнителя
            worker_item = self.table.item(i, len(self.detail_types))
            if worker_item:
                new_workers[work] = worker_item.text().strip()
            
            # Сохраняем ставки
            for j, detail in enumerate(self.detail_types):
                text = self.table.item(i, j).text().strip() if self.table.item(i, j) else '0'
                try:
                    value = float(text.replace(',', '.'))
                except ValueError:
                    QMessageBox.warning(self, 'Ошибка', f'Неверное число для {work} × {detail}')
                    return
                new_rates[f"{work}_{detail}"] = value
        
        # Обновляем и сохраняем
        self.rates.update(new_rates)
        self.workers.update(new_workers)
        save_rates(self.rates)
        save_workers(self.workers)
        self.accept()












