from imports import *
from constants import *
from pathlib import Path
from file_operations import *
from file_operations import save_project_data, load_project_data, get_next_project_number, PROJECTS_DIR, delete_autosave

class ProjectManager:
    def __init__(self, main_window):
        self.main_window = main_window

    def is_editing(self):
        """Проверяет, находится ли таблица в режиме редактирования"""
        if not self.table:
            return False
        return self.table.state() == QAbstractItemView.EditingState

    def _load_project_data(self, project_data, filepath):
        try:
            print("Начинаем загрузку данных проекта...")
            
            # Блокируем сигналы полей ввода перед загрузкой данных
            self.main_window.block_signals(True)
            
            # Сохраняем путь к проекту
            self.main_window.current_project_path = filepath

            # Убедимся что колонки установлены перед загрузкой данных
            self.main_window.table.setColumnCount(len(self.main_window.columns))
            self.main_window.table.setHorizontalHeaderLabels(self.main_window.columns)
            
            # Восстанавливаем данные, НО не перезаписываем настройки!
            self.main_window.columns = project_data.get('columns', self.main_window.columns)
            
            # ТИПЫ ФАСАДОВ И СТАВКИ НЕ ПЕРЕЗАПИСЫВАЕМ из проекта!
            # Они должны браться из конфигов
            self.main_window.current_project_number = project_data.get('project_number')
            self.main_window.customer_name = project_data.get('customer_name', '')
            
            # Загружаем дату проекта
            self.main_window.project_date = project_data.get('project_date', 
                                                        QDateTime.currentDateTime().toString('dd.MM.yyyy'))
            
            print(f"Загружены данные: project_number={self.main_window.current_project_number}, customer={self.main_window.customer_name}, date={self.main_window.project_date}")
            
            # ОБНОВЛЯЕМ ПОЛЯ В ИНТЕРФЕЙСЕ
            self.main_window.le_project_number.setText(str(self.main_window.current_project_number) if self.main_window.current_project_number else "")
            self.main_window.le_customer.setText(self.main_window.customer_name)
            self.main_window.le_date.setText(self.main_window.project_date)
            
            # Разблокируем сигналы полей ввода после загрузки данных
            self.main_window.block_signals(False)
            
            # Обновляем структуру таблицы
            self.main_window.table.setRowCount(0)
            
            # Загружаем данные таблицы
            table_data = project_data.get('table_data', [])
            print(f"Загружаем {len(table_data)} строк данных таблицы")
            
            if table_data:
                self.main_window.table.setRowCount(len(table_data))
                for row, row_data in enumerate(table_data):
                    for col, value in enumerate(row_data):
                        if col < self.main_window.table.columnCount():
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.main_window.table.setItem(row, col, item)
                
                # Временно блокируем сигналы таблицы
                self.main_window.table.blockSignals(True)
                # Разблокируем после загрузки данных
                self.main_window.table.blockSignals(False)
                
                self.main_window.force_calculation() # автоматический расчёт

            # Обновляем делегат для типа детали (ВАЖНО!)
            print("Обновляем делегат...")
            self.main_window.update_detail_type_delegate()
            
            # Обновляем заголовок окна
            print("Обновляем заголовок...")
            self.main_window.update_window_title()
            
            # Сбрасываем флаг изменений
            if hasattr(self.main_window, 'mark_as_saved'):
                self.main_window.mark_as_saved()
            
            self.main_window.show_status_message(f'Проект загружен: №{self.main_window.current_project_number}', 3000)
            print("Загрузка проекта завершена успешно!")
            
            # ПОСЛЕ загрузки данных - принудительно проверяем ВСЕ ячейки
            if hasattr(self.main_window, 'validate_all_cells'):
                self.main_window.validate_all_cells()
                
            self.main_window.show_status_message(f'Проект загружен: №{self.main_window.current_project_number}', 3000)

        except Exception as e:
            print(f"Ошибка при загрузке данных проекта: {str(e)}")
            # Гарантируем, что сигналы будут разблокированы даже при ошибке
            self.main_window.block_signals(False)
            self.main_window.table.blockSignals(False)
            QMessageBox.critical(self.main_window, 'Ошибка', f'Не удалось загрузить данные проекта: {str(e)}')


    def save_project(self):
        try:
            # Безопасный расчет перед сохранением (только если метод существует)
            if (hasattr(self.main_window, 'force_calculation') and 
                callable(getattr(self.main_window, 'force_calculation'))):
                self.main_window.force_calculation()
            
            # Удаляем пустые строки перед сохранением
            if (hasattr(self.main_window, 'table_manager') and 
                hasattr(self.main_window.table_manager, 'remove_empty_rows')):
                self.main_window.table_manager.remove_empty_rows()
            
            # Получаем следующий номер проекта если его нет
            if self.main_window.current_project_number is None:
                self.main_window.current_project_number = get_next_project_number()
            
            # Обновляем дату из поля ввода перед сохранением
            date_text = self.main_window.le_date.text().strip()
            if not date_text:
                current_date = QDateTime.currentDateTime().toString('dd.MM.yyyy')
                self.main_window.project_date = current_date
                self.main_window.le_date.setText(current_date)
            else:
                self.main_window.project_date = date_text
            
            # Собираем данные таблицы
            table_data = []
            for row in range(self.main_window.table.rowCount()):
                row_data = []
                for col in range(self.main_window.table.columnCount()):
                    item = self.main_window.table.item(row, col)
                    row_data.append(item.text() if item else '')
                table_data.append(row_data)
            
            project_data = {
                'project_number': self.main_window.current_project_number,
                'customer_name': self.main_window.customer_name,
                'project_date': self.main_window.project_date,
                'last_modified': QDateTime.currentDateTime().toString('dd-MM-yyyy HH:mm:ss'),
                'columns': self.main_window.columns,
                'table_data': table_data,
                'detail_types': self.main_window.detail_types
            }
            
            # Диалог сохранения
            default_filename = f"{self.main_window.current_project_number}"
            if self.main_window.customer_name:
                default_filename += f"_{self.main_window.customer_name}"
            
            # Преобразуем дату в формат день-месяц-год для имени файла
            if self.main_window.project_date:
                date_parts = self.main_window.project_date.split('.')
                if len(date_parts) == 3:
                    day, month, year = date_parts
                    date_str = f"{day}.{month}.{year}"
                else:
                    date_str = QDateTime.currentDateTime().toString('dd-MM-yyyy')
            else:
                date_str = QDateTime.currentDateTime().toString('dd-MM-yyyy')
            
            default_filename += f"_{date_str}.json"
            
            filepath, _ = QFileDialog.getSaveFileName(
                self.main_window,
                "Сохранить проект",
                str(Path(PROJECTS_DIR) / default_filename),
                "JSON Files (*.json)"
            )
            
            if not filepath:
                return  # Пользователь отменил
            
            project_number, filename = save_project_data(project_data, filepath)
            self.main_window.current_project_number = project_number
            self.main_window.current_project_path = filepath
            
            # Сбрасываем флаг изменений
            if hasattr(self.main_window, 'mark_as_saved'):
                self.main_window.mark_as_saved()
                
            self.main_window.update_window_title()
            
            self.main_window.show_status_message(f'Проект сохранен: {filename}', 3000)

             # Возвращаем True при успешном сохранении
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении: {str(e)}")
            QMessageBox.critical(self.main_window, 'Ошибка', f'Не удалось сохранить проект: {str(e)}')
            return False


    def new_project(self, silent=False):
        # Проверяем, есть ли несохраненные изменения
        if not silent and hasattr(self.main_window, 'is_modified') and self.main_window.is_modified:
            msg_box = QMessageBox(self.main_window)
            msg_box.setWindowTitle("Сохранение проекта")
            msg_box.setText("Проект был изменен. Сохранить изменения?")
            save_btn = msg_box.addButton("Сохранить", QMessageBox.YesRole)
            discard_btn = msg_box.addButton("Нет", QMessageBox.NoRole)
            cancel_btn = msg_box.addButton("Отмена", QMessageBox.RejectRole)
            msg_box.setDefaultButton(save_btn)
            msg_box.exec_()

            if msg_box.clickedButton() == save_btn:
                try:
                    self.save_project()
                    if hasattr(self.main_window, 'is_modified') and self.main_window.is_modified:
                        return
                except Exception as e:
                    print(f"Ошибка при сохранении: {e}")
                    return
            elif msg_box.clickedButton() == cancel_btn:
                return  # Отменяем создание нового проекта

        # Блокируем сигналы полей ввода перед изменением
        self.main_window.block_signals(True)

        # Очищаем таблицу НЕ трогая колонки
        self.main_window.table.setRowCount(0)
        self.main_window.table.setRowCount(10)

        # Заполняем пустыми ячейками
        self.main_window.table.blockSignals(True)
        for row in range(10):
            for col in range(self.main_window.table.columnCount()):
                item = QTableWidgetItem('')
                item.setTextAlignment(Qt.AlignCenter)
                self.main_window.table.setItem(row, col, item)
                self.main_window.table_manager._update_cell_style(item, '')
        self.main_window.table.blockSignals(False)

        # Получаем следующий номер проекта
        next_number = get_next_project_number()
        self.main_window.current_project_number = next_number
        self.main_window.customer_name = ""

        # Устанавливаем текущую дату
        self.main_window.project_date = QDateTime.currentDateTime().toString('dd.MM.yyyy')
        self.main_window.le_project_number.setText(str(next_number))
        self.main_window.le_customer.setText("")
        self.main_window.le_date.setText(self.main_window.project_date)
        self.main_window.current_project_path = None

        # Разблокируем сигналы полей ввода
        self.main_window.block_signals(False)

        # Сбрасываем флаг изменений
        if hasattr(self.main_window, 'mark_as_saved'):
            self.main_window.mark_as_saved()

        if not silent:
            self.main_window.show_status_message(f'Создан новый проект №{next_number}', 2000)

        # Принудительно обновляем расчет
        if hasattr(self.main_window, 'force_calculation'):
            self.main_window.force_calculation()


    def load_project(self):
        # Проверяем, есть ли несохраненные изменения
        if hasattr(self.main_window, 'is_modified') and self.main_window.is_modified:
            msg_box = QMessageBox(self.main_window)
            msg_box.setWindowTitle("Сохранение проекта")
            msg_box.setText("Проект был изменен. Сохранить изменения?")
            save_btn = msg_box.addButton("Сохранить", QMessageBox.YesRole)
            discard_btn = msg_box.addButton("Нет", QMessageBox.NoRole)
            cancel_btn = msg_box.addButton("Отмена", QMessageBox.RejectRole)
            msg_box.setDefaultButton(save_btn)
            msg_box.exec_()

            if msg_box.clickedButton() == save_btn:
                try:
                    self.save_project()
                    if hasattr(self.main_window, 'is_modified') and self.main_window.is_modified:
                        return
                except Exception as e:
                    print(f"Ошибка при сохранении: {e}")
                    return
            elif msg_box.clickedButton() == cancel_btn:
                return  # Отменяем загрузку проекта

        # Продолжаем с загрузкой проекта
        try:
            filepath, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Открыть проект",
                str(Path(PROJECTS_DIR)),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filepath:
                return  # Пользователь отменил

            project_data = load_project_data(filepath)
            self._load_project_data(project_data, filepath)

        except Exception as e:
            print(f"Ошибка при загрузке проекта: {str(e)}")
            QMessageBox.critical(self.main_window, 'Ошибка', f'Не удалось загрузить проект: {str(e)}')










