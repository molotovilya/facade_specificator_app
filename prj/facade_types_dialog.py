from imports import *
from file_operations import save_facade_types, save_rates

class FacadeTypesDialog(QDialog):
    def __init__(self, types_list, rates, work_types, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Типы фасадов')
        self.resize(500, 500)
        self.types = list(types_list)
        self.original_types = list(types_list)
        self.rates = rates
        self.work_types = work_types

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
        for facade_type in self.types:
            QListWidgetItem(facade_type, self.list_widget)

    def accept(self):
        """Сохраняем изменения при закрытии OK"""
        new_order = []
        for i in range(self.list_widget.count()):
            new_order.append(self.list_widget.item(i).text())
        
        # Сохраняем новые типы фасадов
        save_facade_types(new_order)
        # Сохраняем обновленные ставки
        save_rates(self.rates)
        
        super().accept()


    def update_button_states(self):
        current_item = self.list_widget.currentItem()
        self.btn_rename.setEnabled(current_item is not None)
        self.btn_delete.setEnabled(current_item is not None)
    
    def add_type(self):
        text, ok = QInputDialog.getText(self, 'Новый тип фасада', 'Название:')
        if ok and text.strip():
            name = text.strip()
            if name in self.types:
                QMessageBox.warning(self, 'Ошибка', 'Тип фасада с таким названием уже существует!')
                return
            self.types.append(name)
            self.update_list()
            # НЕ сохраняем здесь, только при OK/Cancel
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == name:
                    self.list_widget.setCurrentRow(i)
                    break

    def rename_type(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
            
        old_name = current_item.text()
        text, ok = QInputDialog.getText(self, 'Переименовать тип фасада', 'Новое название:', text=old_name)
        if ok and text.strip():
            new_name = text.strip()
            if new_name in self.types:
                QMessageBox.warning(self, 'Ошибка', 'Тип фасада с таким названием уже существует!')
                return
                
            index = self.types.index(old_name)
            self.types[index] = new_name
            
            # Обновляем ставки для нового имени
            new_rates = {}
            for work in self.work_types:
                old_key = f"{work}_{old_name}"
                new_key = f"{work}_{new_name}"
                new_rates[new_key] = self.rates.get(old_key, 0)
            
            self.rates.update(new_rates)
            
            self.update_list()
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == new_name:
                    self.list_widget.setCurrentRow(i)
                    break
    
    def delete_type(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
            
        facade_type = current_item.text()
        reply = QMessageBox.question(self, 'Подтверждение', 
                                   f'Удалить тип фасада "{facade_type}"? Все ставки для этого типа фасадов будут удалены!')
        if reply == QMessageBox.Yes:
            # Удаляем ставки для этого типа фасадов
            for work in self.work_types:
                key = f"{work}_{facade_type}"
                if key in self.rates:
                    del self.rates[key]
            
            self.types.remove(facade_type)
            self.update_list()
            self.update_button_states()
    
    def get_types(self):
        new_order = []
        for i in range(self.list_widget.count()):
            new_order.append(self.list_widget.item(i).text())
        return new_order, self.rates