from imports import *
from constants import NUMERIC_FIELDS
from file_operations import load_other_settings

class TableManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.table = None
        self.clip_value = None
        self.history = []  # История: список состояний всей таблицы
        self.history_index = -1
        self.max_history = 10  # Уменьшим размер истории для скорости
        self.last_save_time = 0  # Для группировки быстрых изменений
        self.updating_style = False




    # table_manager.py
    # Добавляем/проверяем наличие методов:

    def save_current_cell(self):
        """Сохраняет данные текущей ячейки при переходе"""
        if not self.table:
            return
            
        current_item = self.table.currentItem()
        if not current_item:
            return
            
        # Просто сохраняем текущее состояние
        self._save_current_state()
        
        # Обновляем флаг модификации главного окна
        if (hasattr(self, 'main_window') and self.main_window and 
            hasattr(self.main_window, 'mark_as_modified')):
            self.main_window.mark_as_modified()

    def handle_tab_press(self):
        """Обработка нажатия Tab - переход вперед"""
        if not self.table:
            return
            
        row, col = self.table.currentRow(), self.table.currentColumn()
        
        # Переход вперед
        if col < self.table.columnCount() - 1:
            next_col = col + 1
            next_row = row
        else:
            next_col = 0
            next_row = row + 1
        
        self.move_to_cell(next_row, next_col)

    def handle_shift_tab_press(self):
        """Обработка нажатия Shift+Tab - переход назад"""
        if not self.table:
            return
            
        row, col = self.table.currentRow(), self.table.currentColumn()
        
        # Переход назад
        if col > 0:
            next_col = col - 1
            next_row = row
        else:
            if row > 0:
                next_col = self.table.columnCount() - 1
                next_row = row - 1
            else:
                next_col = 0
                next_row = 0
        
        self.move_to_cell(next_row, next_col)

    def move_to_cell(self, row, col):
        """Безопасный переход к указанной ячейке"""
        if not self.table:
            return
            
        # Корректируем координаты
        if row < 0:
            row = 0
        if col < 0:
            col = 0
            
        # Добавляем строки если нужно
        if row >= self.table.rowCount():
            self.add_more_rows()
            
        # Корректируем колонку
        if col >= self.table.columnCount():
            col = self.table.columnCount() - 1
            
        # Переходим к ячейке
        self.table.setCurrentCell(row, col)
        
        # Прокручиваем если нужно
        if row >= self.table.rowCount() - 3:
            self.table.scrollToItem(self.table.item(row, col))









    def clear_table(self):
        if not self.table:
            return
            
        self._save_current_state()
        
        self.table.blockSignals(True)
        
        # Полностью очищаем все ячейки и УДАЛЯЕМ РАЗДЕЛИТЕЛИ
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setText('')
                    item.setBackground(Qt.white)
                    # УДАЛЯЕМ ВСЕ ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ (включая разделители)
                    item.setData(Qt.UserRole, None)
        
        self.table.blockSignals(False)
        
        # Удаляем пустые строки после очистки
        self.remove_empty_rows()
        
        # ПРИНУДИТЕЛЬНО перерисовываем таблицу для удаления разделителей
        self.table.viewport().update()
        
        # Принудительно сохраняем состояние после очистки
        self.main_window._autosave_current_state()
        
        self.main_window.show_status_message('Таблица полностью очищена', 2000)

    def set_table(self, table):
        self.table = table
        # Сохраняем начальное состояние
        self._save_current_state()
        
    def _save_current_state(self):
        """Сохраняет текущее состояние всей таблицы"""
        if not self.table:
            return
            
        current_time = QDateTime.currentMSecsSinceEpoch()
        # Группируем изменения, сделанные менее чем за 500ms
        if current_time - self.last_save_time < 500 and self.history:
            # Заменяем последнее состояние вместо добавления нового
            self.history[self.history_index] = self._get_table_state()
        else:
            # Сохраняем новое состояние
            state = self._get_table_state()
            
            # Удаляем будущие состояния если мы откатывались
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
                
            self.history.append(state)
            self.history_index = len(self.history) - 1
            
            # Ограничиваем размер истории
            if len(self.history) > self.max_history:
                self.history.pop(0)
                self.history_index -= 1
                
        self.last_save_time = current_time
        
    def _get_table_state(self):
        """Возвращает текущее состояние таблицы"""
        state = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else '')
            state.append(row_data)
        return state
        
    def _restore_state(self, state_index):
        """Восстанавливает состояние таблицы"""
        if state_index < 0 or state_index >= len(self.history):
            return False
            
        state = self.history[state_index]
        self.table.blockSignals(True)
        
        # Устанавливаем нужное количество строк
        self.table.setRowCount(len(state))
        
        # Восстанавливаем данные
        for row, row_data in enumerate(state):
            for col, value in enumerate(row_data):
                if col < self.table.columnCount():
                    item = self.table.item(row, col)
                    if not item:
                        item = QTableWidgetItem(value)
                        self.table.setItem(row, col, item)
                    else:
                        item.setText(value)
                    self._update_cell_style(item, value)
        
        self.table.blockSignals(False)
        return True
        
    def undo(self):
        """Отмена последнего действия"""
        if self.history_index <= 0:
            self.main_window.show_status_message("Нечего отменять", 1500)
            return False
            
        if self._restore_state(self.history_index - 1):
            self.history_index -= 1
            self.main_window.show_status_message("Отменено", 1500)
            return True
        return False
        
    def redo(self):
        """Повтор отмененного действия"""
        if self.history_index >= len(self.history) - 1:
            self.main_window.show_status_message("Нечего повторить", 1500)
            return False
            
        if self._restore_state(self.history_index + 1):
            self.history_index += 1
            self.main_window.show_status_message("Повторено", 1500)
            return True
        return False
        
    def _update_cell_style(self, item, value):
        """Обновляет стиль ячейки с проверкой ошибок"""
        if not item or not self.table:
            return
            
        value = str(value).strip()
        item.setTextAlignment(Qt.AlignCenter)
        
        # Стандартная логика
        if value:
            item.setBackground(QColor('#fffbe6'))
        else:
            item.setBackground(Qt.white)
        
        # Если нет доступа к главному окну - выходим
        if not hasattr(self.main_window, 'columns'):
            return
            
        row = item.row()
        col = item.column()
        
        if col >= len(self.main_window.columns):
            return
            
        col_name = self.main_window.columns[col]
        
        # Проверка для числовых полей
        if col_name in NUMERIC_FIELDS and value:
            try:
                num_value = float(value.replace(',', '.'))
                if num_value < 0:
                    item.setBackground(QColor('#ffcccc'))
            except ValueError:
                item.setBackground(QColor('#ffcccc'))
            # НЕ ВОЗВРАЩАЕМСЯ! Продолжаем проверки для "Сторон"
        
        # Проверка для поля "Сторон"
        if col_name == 'Сторон' and value:
            try:
                sides_value = int(float(value.replace(',', '.')))
                
                # Проверка на допустимые значения (только 1 или 2)
                if sides_value not in [1, 2]:
                    item.setBackground(QColor('#ffcccc'))
                    return
                    
                # Ищем тип фасада в этой же строке
                if 'Тип детали' in self.main_window.columns:
                    detail_col = self.main_window.columns.index('Тип детали')
                    detail_item = self.table.item(row, detail_col)
                    if detail_item:
                        detail_type = detail_item.text().strip().lower()
                        
                        # Если тип содержит + и указана 1 сторона - ошибка
                        if '+' in detail_type and sides_value == 1:
                            item.setBackground(QColor('#ffcccc'))
                            
            except ValueError:
                item.setBackground(QColor('#ffcccc'))

    def handle_item_change(self, item):
        """Обработчик изменения ячейки"""
        if not item or self.updating_style:  # ← ПРОВЕРЯЕМ ФЛАГ
            return
            
        print(f"Item changed: row={item.row()}, col={item.column()}, value='{item.text()}'")
        
        # Сохраняем состояние ДО изменения
        self._save_current_state()
        
        # Устанавливаем флаг чтобы избежать рекурсии
        self.updating_style = True
        
        try:
            # Обновляем стиль текущей ячейки
            value = item.text().strip()
            self._update_cell_style(item, value)
            
            # Если изменился "Тип детали" - обновляем также ячейку "Сторон"
            if hasattr(self.main_window, 'columns'):
                col_name = self.main_window.columns[item.column()] if item.column() < len(self.main_window.columns) else ''
                
                if col_name == 'Тип детали' and 'Сторон' in self.main_window.columns:
                    sides_col = self.main_window.columns.index('Сторон')
                    sides_item = self.table.item(item.row(), sides_col)
                    if sides_item:
                        print(f"Updating sides cell because detail type changed")
                        self._update_cell_style(sides_item, sides_item.text())
            
            # Если изменилось поле "Сторон" - проверяем соответствие с типом детали
            if col_name == 'Сторон' and 'Тип детали' in self.main_window.columns:
                detail_col = self.main_window.columns.index('Тип детали')
                detail_item = self.table.item(item.row(), detail_col)
                if detail_item:
                    self._update_cell_style(detail_item, detail_item.text())
                    
        finally:
            # Всегда снимаем флаг
            self.updating_style = False

    def handle_enter_press(self):
        """Обработка нажатия Enter с сохранением данных и переходом"""
        if not self.table:
            return
            
        # Сохраняем текущую ячейку
        self.save_current_cell()
        
        row, col = self.table.currentRow(), self.table.currentColumn()
        
        # Определяем следующую ячейку (под текущей)
        next_row = row + 1
        next_col = col
        
        # Если следующая строка выходит за пределы - добавляем новые строки
        if next_row >= self.table.rowCount():
            self.add_more_rows()
        
        # Устанавливаем фокус на следующую ячейку
        self.table.setCurrentCell(next_row, next_col)
        
        # Прокручиваем к новой ячейке если нужно
        if next_row >= self.table.rowCount() - 3:
            self.table.scrollToItem(self.table.currentItem())




    def remove_empty_rows(self):
        """Удаляет пустые строки в конце таблицы"""
        if not self.table:
            return
            
        # Идем с конца таблицы и находим первую непустую строку
        last_non_empty_row = -1
        for row in range(self.table.rowCount() - 1, -1, -1):
            has_data = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    has_data = True
                    break
            if has_data:
                last_non_empty_row = row
                break
        
        # Удаляем все пустые строки после последней непустой
        if last_non_empty_row < self.table.rowCount() - 1:
            self.table.setRowCount(last_non_empty_row + 1)
            return True
        return False





    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.table:
            key = event.key()
            mods = event.modifiers()
            
            # Обработка навигационных клавиш
            if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
                # Сохраняем текущую ячейку и разрешаем стандартную обработку
                self.save_current_cell()
                return False
                
            elif key == Qt.Key_Tab:
                self.save_current_cell()
                self.handle_tab_press()
                return True
                
            elif key == Qt.Key_Backtab:  # Shift+Tab
                self.save_current_cell()
                self.handle_shift_tab_press()
                return True
                
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                self.save_current_cell()
                self.handle_enter_press()
                return True
                
            elif key == Qt.Key_Z and (mods & Qt.ControlModifier):
                if mods & Qt.ShiftModifier:
                    return self.redo()
                else:
                    return self.undo()
            elif key == Qt.Key_Y and (mods & Qt.ControlModifier):
                return self.redo()
            elif key == Qt.Key_Delete:
                self.clear_selected_cells()
                return True
            elif key == Qt.Key_C and (mods & Qt.ControlModifier):
                self.copy_clip_value()
                return True
            elif key == Qt.Key_V and (mods & Qt.ControlModifier):
                self.paste_clip_value()
                return True
                
        # Обработка клика мыши
        elif event.type() == QEvent.MouseButtonPress and source is self.table:
            # Сохраняем текущую ячейку перед переходом на новую
            self.save_current_cell()
            return False
            
        return False

    def handle_arrow_down(self):
        """Обработка стрелки вниз - добавляет строки если нужно"""
        if not self.table:
            return
            
        current_row = self.table.currentRow()
        current_col = self.table.currentColumn()
        
        # Если мы на предпоследней строке или ниже, добавляем новые строки
        if current_row >= self.table.rowCount() - 2:
            self.add_more_rows()
        
        # Позволяем стандартной обработке продолжиться


    def add_more_rows(self):
        """Добавляет дополнительные строки в таблицу"""
        if not self.table:
            return
            
        current_rows = self.table.rowCount()
        new_rows = 1  # Добавляем 5 строк
        self.table.setRowCount(current_rows + new_rows)
        
        # Заполняем новые строки пустыми ячейками
        self.table.blockSignals(True)
        for r in range(current_rows, current_rows + new_rows):
            for c in range(self.table.columnCount()):
                if not self.table.item(r, c):
                    item = QTableWidgetItem('')
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, c, item)
        self.table.blockSignals(False)


    def add_row(self):
        if not self.table:
            return
            
        self._save_current_state()
        
        current_row = self.table.rowCount()
        self.table.setRowCount(current_row + 1)
        
        for col in range(self.table.columnCount()):
            if not self.table.item(current_row, col):
                self.table.setItem(current_row, col, QTableWidgetItem(''))
        
        self.main_window.show_status_message(f'Добавлена строка {current_row + 1}', 1500)
        
    def copy_clip_value(self):
        if not self.table:
            return
            
        item = self.table.currentItem()
        if item:
            self.clip_value = item.text()
            self.main_window.show_status_message(f"Скопировано: {self.clip_value}", 2000)
            
    def paste_clip_value(self):
        if not self.clip_value or not self.table:
            return
            
        self._save_current_state()
        
        ranges = self.table.selectedRanges()
        if ranges:
            for r in ranges:
                for row in range(r.topRow(), r.bottomRow() + 1):
                    for col in range(r.leftColumn(), r.rightColumn() + 1):
                        item = self._ensure_item(row, col)
                        item.setText(self.clip_value)
                        self._update_cell_style(item, self.clip_value)
        else:
            row, col = self.table.currentRow(), self.table.currentColumn()
            if row >= 0 and col >= 0:
                item = self._ensure_item(row, col)
                item.setText(self.clip_value)
                self._update_cell_style(item, self.clip_value)
                
        self.main_window.show_status_message(f"Вставлено: {self.clip_value}", 2000)
        
    def _ensure_item(self, row, col):
        if not self.table:
            return None
            
        item = self.table.item(row, col)
        if not item:
            item = QTableWidgetItem('')
            self.table.setItem(row, col, item)
        return item
        
    def clear_table(self):
        if not self.table:
            return
            
        self._save_current_state()
        
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setText('')
                    item.setBackground(Qt.white)
        self.table.blockSignals(False)
        
        self.main_window.show_status_message('Таблица очищена', 2000)
        
    def clear_selected_cells(self):
        if not self.table:
            return
            
        self._save_current_state()
        
        selected = self.table.selectedItems()
        for item in selected:
            item.setText('')
            item.setBackground(Qt.white)
            
        self.main_window.show_status_message('Выделенные ячейки очищены', 2000)
        



    def calculate(self, return_data=False):
        """Расчет данных с возможностью возврата результатов"""
        if not self.table:
            if return_data:
                return {}
            return

        # Загружаем все настройки из единого файла
        other_settings = load_other_settings()
        paint_consumption = other_settings.get('paint_consumption', 0.35)
        wrapping_rate = other_settings.get('wrapping_rate', 140.0)

        if 'Длина' not in self.main_window.columns or 'Ширина' not in self.main_window.columns or 'Кол-во' not in self.main_window.columns:
            self.main_window.show_status_message('Ошибка расчета', 3000)
            if return_data:
                return {}
            return
            
        # Индексы колонок
        len_idx = self.main_window.columns.index('Длина')
        wid_idx = self.main_window.columns.index('Ширина')
        qty_idx = self.main_window.columns.index('Кол-во')
        sides_idx = self.main_window.columns.index('Сторон') if 'Сторон' in self.main_window.columns else -1
        detail_idx = self.main_window.columns.index('Тип детали') if 'Тип детали' in self.main_window.columns else -1
        paint_idx = self.main_window.columns.index('Краска') if 'Краска' in self.main_window.columns else -1
        handle_idx = self.main_window.columns.index('Ручка') if 'Ручка' in self.main_window.columns else -1
        gluing_idx = self.main_window.columns.index('Склейка') if 'Склейка' in self.main_window.columns else -1

        # Результаты расчета
        total_area = 0
        total_paint_area = 0
        total_pieces = 0
        total_edge_length = 0
        total_plank_length = 0
        total_handle_length = 0
        total_gluing_area = 0  # добавляем счетчик для площади склейки
        detail_type_areas = {}
        detail_type_paint_areas = {}
        paint_areas = {}

        for row in range(self.table.rowCount()):
            try:
                # Основные размеры
                l_text = self.table.item(row, len_idx).text() if self.table.item(row, len_idx) else '0'
                w_text = self.table.item(row, wid_idx).text() if self.table.item(row, wid_idx) else '0'
                q_text = self.table.item(row, qty_idx).text() if self.table.item(row, qty_idx) else '0'
                
                l = float(l_text.replace(',', '.'))
                w = float(w_text.replace(',', '.'))
                q = int(float(q_text.replace(',', '.')))
                
                if l > 0 and w > 0 and q > 0:
                    # ОБЩЕЕ КОЛИЧЕСТВО ДЕТАЛЕЙ
                    total_pieces += q
                    
                    # ДЛИНА КРОМКИ (периметр всех деталей)
                    perimeter = 2 * (l + w)
                    total_edge_length += perimeter * q / 1000
                    
                    # Площадь детали в м² (одна сторона)
                    area = (l * w) / 1_000_000
                    total_area += area * q
                    
                    # Определяем количество сторон для покраски
                    detail_type = ''
                    if detail_idx != -1 and self.table.item(row, detail_idx):
                        detail_type = self.table.item(row, detail_idx).text().strip().lower()
                    
                    sides = 1
                    if sides_idx != -1 and self.table.item(row, sides_idx):
                        sides_text = self.table.item(row, sides_idx).text()
                        if sides_text.strip():
                            sides = int(float(sides_text.replace(',', '.')))
                    
                    # Парсим комбинированные типы
                    side_types = self._parse_combined_type(detail_type)
                    
                    # Если это комбинированный тип и 2 стороны, распределяем площадь
                    if len(side_types) > 1 and sides == 2:
                        for i, side_type in enumerate(side_types):
                            if i < 2:  # Максимум 2 стороны
                                paint_area = area * q
                                if side_type not in detail_type_paint_areas:
                                    detail_type_paint_areas[side_type] = 0
                                detail_type_paint_areas[side_type] += paint_area
                                total_paint_area += paint_area
                                paint_type = 'Без краски'
                                if paint_idx != -1 and self.table.item(row, paint_idx):
                                    paint_type = self.table.item(row, paint_idx).text().strip()
                                    if not paint_type:
                                        paint_type = 'Без краски'
                                if paint_type not in paint_areas:
                                    paint_areas[paint_type] = 0
                                paint_areas[paint_type] += paint_area
                    else:
                        paint_area = area * sides * q
                        total_paint_area += paint_area
                        display_detail_type = detail_type if detail_type else 'Без типа'
                        if display_detail_type not in detail_type_paint_areas:
                            detail_type_paint_areas[display_detail_type] = 0
                        detail_type_paint_areas[display_detail_type] += paint_area
                        paint_type = 'Без краски'
                        if paint_idx != -1 and self.table.item(row, paint_idx):
                            paint_type = self.table.item(row, paint_idx).text().strip()
                            if not paint_type:
                                paint_type = 'Без краски'
                        if paint_type not in paint_areas:
                            paint_areas[paint_type] = 0
                        paint_areas[paint_type] += paint_area
                    
                    # Добавляем общую площадь по типам (без учета сторон)
                    display_detail_type = detail_type if detail_type else 'Без типа'
                    if display_detail_type not in detail_type_areas:
                        detail_type_areas[display_detail_type] = 0
                    detail_type_areas[display_detail_type] += area * q
                    
                    # Ручки (в метрах)
                    if handle_idx != -1 and self.table.item(row, handle_idx):
                        handle_text = self.table.item(row, handle_idx).text()
                        if handle_text and handle_text.strip():
                            try:
                                handle_length_mm = float(handle_text.replace(',', '.'))
                                total_handle_length += handle_length_mm * q / 1000
                            except ValueError:
                                pass
                    
                    # Планки
                    is_plank = any(keyword in detail_type for keyword in ['планка', 'рейка', 'брус', 'профиль', 'молдинг'])
                    if is_plank:
                        plank_length = max(l, w)
                        total_plank_length += plank_length * q * sides / 1000

                    # Склейка
                    if gluing_idx != -1 and self.table.item(row, gluing_idx):
                        gluing_text = self.table.item(row, gluing_idx).text()
                        if gluing_text and gluing_text.strip():
                            try:
                                gluing_count = float(gluing_text.replace(',', '.'))
                                gluing_area = area * q * gluing_count
                                total_gluing_area += gluing_area
                            except ValueError:
                                pass
                            
            except Exception as e:
                continue

        # ПРОСТОЙ РАСЧЕТ ЗАМОТКИ ↓
        wrapping_cost = total_area * wrapping_rate  # Общая площадь × ставку

        # Возвращаем результат
        result_data = {
            'total_area': total_area,
            'total_paint_area': total_paint_area,
            'total_paint_kg': total_paint_area * paint_consumption,
            'total_pieces': total_pieces,
            'total_edge_length': total_edge_length,
            'total_plank_length': total_plank_length,
            'total_handle_length': total_handle_length,
            'total_gluing_area': total_gluing_area,  # добавлено
            'detail_type_areas': detail_type_areas,
            'detail_type_paint_areas': detail_type_paint_areas,
            'paint_areas': paint_areas,
            'wrapping_cost': wrapping_cost,
            'paint_consumption': paint_consumption
        }
        
        if return_data:
            return result_data
        else:
            self.main_window.update_calc_area(result_data)
            self.main_window.show_status_message("Расчет выполнен", 3000)





    def _parse_combined_type(self, detail_type):
        """Парсит комбинированные типы фасадов и возвращает список типов для каждой стороны"""
        if '+' in detail_type:
            # Разделяем по "+" и очищаем от пробелов
            types = [t.strip().lower() for t in detail_type.split('+')]
            return types
        return [detail_type.lower()]











