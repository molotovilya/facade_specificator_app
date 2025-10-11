class ClipboardManager:
    def __init__(self):
        self.value = None
    
    def copy(self, table, main_window):
        if not table: return
        item = table.currentItem()
        if not item:
            row, col = table.currentRow(), table.currentColumn()
            if row >= 0 and col >= 0:
                item = table.item(row, col) or QTableWidgetItem('')
        if item:
            self.value = item.text()
            main_window.show_status_message(f"Скопировано: {self.value}", 2000)
    
    def paste(self, table, history, main_window):
        if not self.value or not table: return
        
        ranges = table.selectedRanges()
        if ranges:
            history.start_batch()
            for r in ranges:
                for row in range(r.topRow(), r.bottomRow() + 1):
                    for col in range(r.leftColumn(), r.rightColumn() + 1):
                        item = table.item(row, col) or QTableWidgetItem('')
                        old_val = item.text()
                        item.setText(self.value)
                        history.add_to_batch(row, col, old_val, self.value)
            history.end_batch()
        else:
            row, col = table.currentRow(), table.currentColumn()
            if row >= 0 and col >= 0:
                item = table.item(row, col) or QTableWidgetItem('')
                old_val = item.text()
                item.setText(self.value)
                history.add_change(row, col, old_val, self.value)
        
        main_window.show_status_message(f"Вставлено: {self.value}", 2000)