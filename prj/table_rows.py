class RowManager:
    def add(self, table, main_window):
        if not table: return
        new_row = table.rowCount()
        table.setRowCount(new_row + 1)
        for col in range(table.columnCount()):
            if not table.item(new_row, col):
                table.setItem(new_row, col, QTableWidgetItem(''))
        main_window.show_status_message(f'Добавлена строка {new_row + 1}', 1500)
    
    def handle_enter(self, table, manager, main_window):
        if not table: return
        row, col = table.currentRow(), table.currentColumn()
        if col < table.columnCount() - 1:
            table.setCurrentCell(row, col + 1)
        elif row < table.rowCount() - 1:
            table.setCurrentCell(row + 1, 0)
        else:
            manager.add_row()
            table.setCurrentCell(row + 1, 0)