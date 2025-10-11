class HistoryManager:
    def __init__(self):
        self.history = []
        self.index = -1
        self.batch = None
        
    def add_change(self, row, col, old_val, new_val):
        action = {'type': 'cell', 'changes': [{'cell': (row, col), 'old': old_val, 'new': new_val}]}
        if self.index < len(self.history) - 1:
            self.history = self.history[:self.index + 1]
        self.history.append(action)
        self.index = len(self.history) - 1
        if len(self.history) > 50: self.history.pop(0); self.index -= 1
    
    def add_clear_action(self, old_data):
        action = {'type': 'clear', 'old_data': old_data}
        if self.index < len(self.history) - 1:
            self.history = self.history[:self.index + 1]
        self.history.append(action)
        self.index = len(self.history) - 1
    
    def start_batch(self):
        self.batch = {'type': 'cell', 'changes': []}
    
    def add_to_batch(self, row, col, old_val, new_val):
        if self.batch:
            self.batch['changes'].append({'cell': (row, col), 'old': old_val, 'new': new_val})
    
    def end_batch(self):
        if self.batch and self.batch['changes']:
            self.add_change(0, 0, '', '')  # Используем add_change для добавления батча
            self.history[-1] = self.batch  # Заменяем последнее действие на батч
        self.batch = None
    
    def undo(self, main_window):
        if self.index < 0:
            main_window.show_status_message("Нечего отменять", 1500); return False
        self._apply(self.history[self.index], 'undo')
        self.index -= 1
        main_window.show_status_message("Отменено", 1500); return True
    
    def redo(self, main_window):
        if self.index >= len(self.history) - 1:
            main_window.show_status_message("Нечего повторить", 1500); return False
        self.index += 1
        self._apply(self.history[self.index], 'redo')
        main_window.show_status_message("Повторено", 1500); return True
    
    def _apply(self, action, mode):
        from main_window import MainWindow  # Импортируем здесь чтобы избежать циклического импорта
        main_window = MainWindow.instance if hasattr(MainWindow, 'instance') else None
        if not main_window or not main_window.table_manager.table: return
        
        table = main_window.table_manager.table
        table.blockSignals(True)
        
        if action['type'] == 'cell':
            for change in action['changes']:
                row, col = change['cell']
                value = change['old'] if mode == 'undo' else change['new']
                item = table.item(row, col) or QTableWidgetItem(value)
                item.setText(value)
                main_window.table_manager._update_cell_style(item, value)
        
        elif action['type'] == 'clear':
            if mode == 'undo':
                for r, c, val in action['old_data']:
                    item = table.item(r, c) or QTableWidgetItem(val)
                    item.setText(val)
                    main_window.table_manager._update_cell_style(item, val)
            else:
                for r in range(table.rowCount()):
                    for c in range(table.columnCount()):
                        item = table.item(r, c) or QTableWidgetItem('')
                        item.setText('')
                        main_window.table_manager._update_cell_style(item, '')
        
        table.blockSignals(False)