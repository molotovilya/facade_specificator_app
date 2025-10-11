# work_types_dialog.py
from imports import *
from constants import DEFAULT_WORK_TYPES
from work_types_config import load_work_types, save_work_types  
from file_operations import save_rates

class WorkTypesDialog(QDialog):
    def __init__(self, work_types, rates, detail_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Типы работ')
        self.resize(500, 500)
        self.work_types = load_work_types()  # Загружаем из конфига
        self.original_work_types = self.work_types[:]  # Копируем
        self.rates = rates
        self.detail_types = detail_types
        
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.currentItemChanged.connect(self.update_button_states)
        self.update_list()
        layout.addWidget(QLabel('Перетаскивайте элементы для изменения порядка:'))
        layout.addWidget(self.list_widget)
        
        buttons_layout = QHBoxLayout()
        self.btn_add = QPushButton('Добавить')
        self.btn_rename = QPushButton('Переименовать')
        self.btn_delete = QPushButton('Удалить')
        
        self.btn_add.clicked.connect(self.add_type)
        self.btn_rename.clicked.connect(self.rename_type)
        self.btn_delete.clicked.connect(self.delete_type)
        
        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_rename)
        buttons_layout.addWidget(self.btn_delete)
        
        layout.addLayout(buttons_layout)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.update_button_states()
        
    def update_list(self):
        self.list_widget.clear()
        for work_type in self.work_types:
            QListWidgetItem(work_type, self.list_widget)
    
    def update_button_states(self):
        current_item = self.list_widget.currentItem()
        self.btn_rename.setEnabled(current_item is not None)
        self.btn_delete.setEnabled(current_item is not None)
    
    def add_type(self):
        text, ok = QInputDialog.getText(self, 'Новый тип работы', 'Название работы:')
        if ok and text.strip():
            new_type = text.strip()
            if new_type in self.work_types:
                QMessageBox.warning(self, 'Ошибка', 'Тип работы с таким названием уже существует!')
                return
            self.work_types.append(new_type)
            self.update_list()
            # НЕ сохраняем здесь, только при OK/Cancel
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == new_type:
                    self.list_widget.setCurrentRow(i)
                    break

    def rename_type(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
            
        old_name = current_item.text()
        text, ok = QInputDialog.getText(self, 'Переименовать тип работы', 'Новое название:', text=old_name)
        if ok and text.strip():
            new_name = text.strip()
            if new_name in self.work_types:
                QMessageBox.warning(self, 'Ошибка', 'Тип работы с таким названием уже существует!')
                return
                
            index = self.work_types.index(old_name)
            self.work_types[index] = new_name
            
            # Обновляем ставки для нового имени
            new_rates = {}
            for detail in self.detail_types:
                old_key = f"{old_name}_{detail}"
                new_key = f"{new_name}_{detail}"
                new_rates[new_key] = self.rates.get(old_key, 0)
            
            # Удаляем старые ставки
            for detail in self.detail_types:
                old_key = f"{old_name}_{detail}"
                if old_key in self.rates:
                    del self.rates[old_key]
            
            # Добавляем новые ставки
            self.rates.update(new_rates)
            
            # НЕМЕДЛЕННО сохраняем
            from file_operations import save_rates
            save_rates(self.rates)
            
            self.update_list()
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == new_name:
                    self.list_widget.setCurrentRow(i)
                    break

    def accept(self):
        """Сохраняем изменения при закрытии OK"""
        new_order = []
        for i in range(self.list_widget.count()):
            new_order.append(self.list_widget.item(i).text())
        
        # Сохраняем типы работ в конфиг
        save_work_types(new_order)
        # Сохраняем обновленные ставки
        save_rates(self.rates)
        
        super().accept()
    def delete_type(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
            
        work_type = current_item.text()
        reply = QMessageBox.question(self, 'Подтверждение', 
                                   f'Удалить тип работы "{work_type}"? Все ставки для этого типа работ будут удалены!')
        if reply == QMessageBox.Yes:
            # Удаляем ставки для этого типа работ
            for detail in self.detail_types:
                key = f"{work_type}_{detail}"
                if key in self.rates:
                    del self.rates[key]
            
            self.work_types.remove(work_type)
            self.update_list()
            # Сохраняем сразу
            save_work_types(self.work_types)
            save_rates(self.rates)
            self.update_button_states()


    
    def get_work_types(self):
        new_order = []
        for i in range(self.list_widget.count()):
            new_order.append(self.list_widget.item(i).text())
        return new_order, self.rates