class CalculationManager:
    def calculate(self, table, columns, main_window):
        if not table or 'Длина' not in columns or 'Ширина' not in columns or 'Кол-во' not in columns:
            main_window.show_status_message('Ошибка расчета', 3000); return
        
        len_idx = columns.index('Длина')
        wid_idx = columns.index('Ширина')
        qty_idx = columns.index('Кол-во')
        sides_idx = columns.index('Сторон') if 'Сторон' in columns else -1
        
        total_area = paint_area = 0
        
        for row in range(table.rowCount()):
            try:
                l = float((table.item(row, len_idx).text() or '0').replace(',','.'))
                w = float((table.item(row, wid_idx).text() or '0').replace(',','.'))
                q = int(float((table.item(row, qty_idx).text() or '0').replace(',','.')))
                
                if l and w and q:
                    area = (l * w * q) / 1_000_000
                    total_area += area
                    sides = int(float((table.item(row, sides_idx).text() or '1').replace(',','.'))) if sides_idx != -1 else 1
                    paint_area += area * sides
            except: pass
        
        paint_kg = paint_area * 0.35
        result = f"Общая: {total_area:.2f} м²\nПокраска: {paint_area:.2f} м²\nКраска: {paint_kg:.2f} кг"
        main_window.update_calc_area(result)
        main_window.show_status_message("Расчет выполнен", 3000)