from imports import *
from constants import *
from file_operations import save_columns_config

class TableStructureDialog(QDialog):

    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Структура таблицы')
        self.resize(500, 500)
        self.original_columns = columns[:]  # Используем переданные колонки
        self.columns = columns[:]  # Работаем с копией
        
        self.init_ui()

    def accept(self):
        """Сохраняем изменения при закрытии OK"""
        new_order = []
        for i in range(self.list_widget.count()):
            new_order.append(self.list_widget.item(i).text())
        
        # Сохраняем в конфиг
        from file_operations import save_columns_config
        save_columns_config(new_order)
        
        super().accept()

    def add_column(self):
        text, ok = QInputDialog.getText(self, 'Новая колонка', 'Название колонки:')
        if ok and text.strip():
            new_column = text.strip()
            if new_column in self.columns:
                QMessageBox.warning(self, 'Ошибка', 'Колонка с таким названием уже существует!')
                return
            self.columns.append(new_column)
            self.update_list()
            # НЕ сохраняем здесь, только при OK
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == new_column:
                    self.list_widget.setCurrentRow(i)
                    break




    def init_ui(self):
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.currentItemChanged.connect(self.update_button_states)
        layout.addWidget(QLabel('Перетаскивайте элементы для изменения порядка:'))
        layout.addWidget(self.list_widget)

        self.btn_add = QPushButton('Добавить')
        self.btn_rename = QPushButton('Переименовать')
        self.btn_delete = QPushButton('Удалить')

        self.btn_add.clicked.connect(self.add_column)
        self.btn_rename.clicked.connect(self.rename_column)
        self.btn_delete.clicked.connect(self.delete_column)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.btn_add)
        buttons_layout.addWidget(self.btn_rename)
        buttons_layout.addWidget(self.btn_delete)
        layout.addLayout(buttons_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.update_list()
        self.update_button_states()

    def update_list(self):
        self.list_widget.clear()
        for column in self.columns:
            item = QListWidgetItem(column)
            if column in MAIN_COLUMNS:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
                item.setBackground(QColor(240, 240, 240))
                item.setToolTip('Основная колонка (нельзя удалить)')
            self.list_widget.addItem(item)

    def update_button_states(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            column_name = current_item.text()
            self.btn_rename.setEnabled(True)
            self.btn_delete.setEnabled(column_name not in MAIN_COLUMNS)
        else:
            self.btn_rename.setEnabled(False)
            self.btn_delete.setEnabled(False)

    def rename_column(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
        old_name = current_item.text()
        if old_name in MAIN_COLUMNS:
            QMessageBox.warning(self, 'Ошибка', 'Нельзя переименовать основную колонку!')
            return
        text, ok = QInputDialog.getText(self, 'Переименовать колонку', 'Новое название:', text=old_name)
        if ok and text.strip():
            new_name = text.strip()
            if new_name in self.columns:
                QMessageBox.warning(self, 'Ошибка', 'Колонка с таким названием уже существует!')
                return
            index = self.columns.index(old_name)
            self.columns[index] = new_name
            self.update_list()
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == new_name:
                    self.list_widget.setCurrentRow(i)
                    break

    def delete_column(self):
        current_item = self.list_widget.currentItem()
        if not current_item:
            return
        column_name = current_item.text()
        if column_name in MAIN_COLUMNS:
            QMessageBox.warning(self, 'Ошибка', 'Нельзя удалить основную колонку!')
            return
        reply = QMessageBox.question(self, 'Подтверждение', 
                                     f'Удалить колонку "{column_name}"? Все данные в этой колонке будут потеряны!')
        if reply == QMessageBox.Yes:
            self.columns.remove(column_name)
            self.update_list()
            self.update_button_states()

    def get_columns(self):
        new_order = []
        for i in range(self.list_widget.count()):
            new_order.append(self.list_widget.item(i).text())
        return new_order




