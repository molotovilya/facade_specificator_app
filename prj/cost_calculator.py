from imports import *
from constants import *
from file_operations import load_other_settings  
from work_types_config import load_work_types
from file_operations import load_rates, load_workers

class CostCalculator:
    def __init__(self):
        self.rates = load_rates()
        self.workers = load_workers()
    
    def calculate_costs(self, table_data, columns, detail_types):
        """Расчёт стоимости работ по всем типам"""
        results = {}
        
        other_settings = load_other_settings()
        taping_rate = other_settings.get('taping_rate', 50.0)
        gluing_rate = other_settings.get('gluing_rate', 30.0)
        handle_rate = other_settings.get('handle_rate', 100.0)
        
        # Индексы колонок
        len_idx = columns.index('Длина') if 'Длина' in columns else -1
        wid_idx = columns.index('Ширина') if 'Ширина' in columns else -1
        qty_idx = columns.index('Кол-во') if 'Кол-во' in columns else -1
        sides_idx = columns.index('Сторон') if 'Сторон' in columns else -1
        detail_idx = columns.index('Тип детали') if 'Тип детали' in columns else -1
        paint_idx = columns.index('Краска') if 'Краска' in columns else -1
        handle_idx = columns.index('Ручка') if 'Ручка' in columns else -1
        gluing_idx = columns.index('Склейка') if 'Склейка' in columns else -1
        
        if -1 in [len_idx, wid_idx, qty_idx, detail_idx]:
            return results
        
        work_types = load_work_types()
        
        for work_type in work_types:
            results[work_type] = {
                'total_area': 0,
                'total_cost': 0,
                'additional_cost': 0,
                'by_detail': {},
                'by_paint': {}
            }
        
        total_additional_cost = 0
        
        for row_data in table_data:
            try:
                # Основные размеры
                l_text = row_data[len_idx] if len_idx < len(row_data) else '0'
                w_text = row_data[wid_idx] if wid_idx < len(row_data) else '0'
                q_text = row_data[qty_idx] if qty_idx < len(row_data) else '0'
                
                l = float(l_text.replace(',', '.')) if l_text else 0
                w = float(w_text.replace(',', '.')) if w_text else 0
                q = int(float(q_text.replace(',', '.'))) if q_text else 0
                
                if l == 0 or w == 0 or q == 0:
                    continue
                
                detail_type = (row_data[detail_idx] if detail_idx < len(row_data) else '').strip().lower()
                sides = 1
                if sides_idx != -1 and sides_idx < len(row_data) and row_data[sides_idx]:
                    try:
                        sides = int(float(row_data[sides_idx].replace(',', '.')))
                    except:
                        sides = 1
                
                if any(term in detail_type for term in ['2ст', 'двухстор', '2 стороны', '2сторон']):
                    sides = 2
                elif any(term in detail_type for term in ['1ст', 'одностор', '1 сторона']):
                    sides = 1
                




                additional_cost = 0

                # 1. Ручка
                if handle_idx != -1 and handle_idx < len(row_data) and row_data[handle_idx]:
                    try:
                        handle_length = float(row_data[handle_idx].replace(',', '.'))
                        additional_cost += handle_length * q * handle_rate / 1000
                    except:
                        pass

                # 2. Склейка
                if gluing_idx != -1 and gluing_idx < len(row_data) and row_data[gluing_idx]:
                    try:
                        area = (l * w) / 1_000_000
                        gluing_count = float(row_data[gluing_idx].replace(',', '.'))
                        additional_cost += area * q * gluing_count * gluing_rate
                    except:
                        pass

                # 3. Оклейка (только для двусторонних фасадов)
                if sides == 2:
                    try:
                        area = (l * w) / 1_000_000
                        additional_cost += area * q * taping_rate  # берём только одну сторону
                    except:
                        pass

                # После этого total_additional_cost += additional_cost
                total_additional_cost += additional_cost
                




                
                # Комбинированные типы
                if '+' in detail_type:
                    side_types = [t.strip() for t in detail_type.split('+')]
                    for i, side_type in enumerate(side_types):
                        if i < 2:
                            self._add_to_results(results, side_type, l, w, q, sides=1, row_data=row_data, paint_idx=paint_idx, work_types=work_types)
                else:
                    self._add_to_results(results, detail_type, l, w, q, sides, row_data, paint_idx, work_types)
                    
            except Exception as e:
                print(f"Ошибка расчета для строки: {e}")
                continue
        
        if 'Подготовка' in results:
            results['Подготовка']['additional_cost'] = total_additional_cost
            results['Подготовка']['total_cost'] += total_additional_cost
        
        return results

    def _add_to_results(self, results, detail_type, l, w, q, sides, row_data, paint_idx, work_types):
        """Добавляет данные в результаты с учётом типа детали и количества"""
        is_plank = any(keyword in detail_type for keyword in ['планка', 'рейка', 'брус', 'профиль', 'молдинг'])
        
        if is_plank:
            paint_area = max(l, w) * q * sides / 1000
        else:
            area = l * w / 1_000_000
            paint_area = area * q * sides
        
        paint_type = 'Без краски'
        if paint_idx != -1 and row_data[paint_idx]:
            paint_type = row_data[paint_idx].strip() or 'Без краски'
        
        for work_type in work_types:
            if work_type == 'Замотка':
                continue
            
            if work_type not in results:
                results[work_type] = {'total_area': 0, 'total_cost': 0, 'by_detail': {}, 'by_paint': {}}
            
            rate_key = f"{work_type}_{detail_type}"
            rate = self.rates.get(rate_key, 0)
            
            cost = paint_area * rate
            results[work_type]['total_area'] += paint_area
            results[work_type]['total_cost'] += cost
            
            if detail_type not in results[work_type]['by_detail']:
                results[work_type]['by_detail'][detail_type] = {'area': 0, 'cost': 0}
            results[work_type]['by_detail'][detail_type]['area'] += paint_area
            results[work_type]['by_detail'][detail_type]['cost'] += cost
            
            if paint_type not in results[work_type]['by_paint']:
                results[work_type]['by_paint'][paint_type] = {'area': 0, 'cost': 0}
            results[work_type]['by_paint'][paint_type]['area'] += paint_area
            results[work_type]['by_paint'][paint_type]['cost'] += cost





