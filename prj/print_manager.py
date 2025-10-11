# print_manager.py
from imports import *
import os
import sys
from PyQt5.QtCore import QDateTime
from datetime import datetime
from cost_calculator import CostCalculator
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtGui import QTextDocument
from constants import SEPARATOR_WIDTH, SEPARATOR_COLOR, SEPARATOR_STYLE
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtGui import QTextDocument  # ← ДОБАВИТЬ ЭТОТ ИМПОРТ
import tempfile
import subprocess
import platform
import shutil
import os
from weasyprint import HTML
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtCore import QDateTime
import ctypes
import shutil
import subprocess
import platform
import os
import tempfile
from PyQt5.QtWidgets import QMessageBox

max_paint_length = 15 # Максимальная длина названия краски в ячейке


class PrintManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.calculator = CostCalculator()
        

    def _get_project_data(self):
        """Возвращает данные проекта (number, customer, date)"""
        return {
            'number': getattr(self.main_window, 'current_project_number', '') or 'Н/Д',
            'customer': getattr(self.main_window, 'customer_name', '') or 'Не указан',
            'date': getattr(self.main_window, 'project_date', '') or QDateTime.currentDateTime().toString('dd.MM.yyyy')
        }

    def _get_table_data(self):
        """Считывает данные из QTableWidget -> список списков"""
        table_data = []
        table = getattr(self.main_window, 'table', None)
        if table is None:
            return table_data
        for r in range(table.rowCount()):
            row = []
            for c in range(table.columnCount()):
                item = table.item(r, c)
                row.append(item.text() if item else '')
            table_data.append(row)
        return table_data

    def generate_specification_html(self):
        """Генерирует HTML спецификации (WeasyPrint) с обновлёнными стилями:
        - calc-table основной текст 10pt, детализация 8pt
        - симметричный padding
        - vertical-align: top только для calc-table
        - маленькие поля (@page margin 10mm)
        - шапка: проект слева, заказчик по центру, дата справа (метки жирные, значения обычные)
        - main-table выводится с remove_paint_column=True (комментарий расширен)
        """
        try:
            # Форсируем перерасчёт в основном окне (если есть)
            try:
                self.main_window.force_calculation()
            except Exception:
                pass

            project_data = self._get_project_data()

            # Получаем расчётные данные (table_manager может вернуть dict или list)
            try:
                calculation_data = self.main_window.table_manager.calculate(return_data=True)
            except Exception:
                calculation_data = {}

            # Стоимость
            try:
                cost_data = self.calculator.calculate_costs(
                    self._get_table_data(),
                    getattr(self.main_window, 'columns', []),
                    getattr(self.main_window, 'detail_types', [])
                )
            except Exception:
                cost_data = {}

            # Есть ли данные по ручкам
            handle_has_data = False
            if 'Ручка' in getattr(self.main_window, 'columns', []):
                for row in self._get_table_data():
                    try:
                        idx = self.main_window.columns.index('Ручка')
                        if idx < len(row) and str(row[idx]).strip():
                            handle_has_data = True
                            break
                    except Exception:
                        pass

            html = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        /* ПОЛЯ СТРАНИЦЫ */
        @page {{ size: A4; margin: 10mm; }}
        body {{ font-family: Arial, sans-serif; margin:0; padding:0; font-size:10pt; }}

        /* ШАПКА: подписи жирные, значения обычные */
        .project-header {{ display:flex; justify-content:space-between; align-items:flex-start; margin:6mm 0 4mm 0; }}
        .project-header .block {{ min-width:0; }}
        .project-header .label {{ font-weight: bold; margin-right:4px; }}
        .project-header .value {{ font-weight: normal; }}

        /* ОБЩИЕ ТАБЛИЦЫ */
        table {{ width:100%; border-collapse:collapse; margin-bottom:4mm; table-layout:auto; page-break-inside:auto; }}
        thead {{ display: table-header-group; }}  /* повтор заголовков при переносе */
        tfoot {{ display: table-footer-group; }}
        th, td {{
            border:1px solid #000;
            padding:6px;                 /* симметричный padding сверху/снизу/слева/справа */
            box-sizing: border-box;
        }}
        th {{ background:#f0f0f0; font-weight:bold; text-align:center; }}

        /* CALC-TABLE (верхний блок) */
        .calc-table th, .calc-table td {{ font-size:10pt; }}        /* основной текст 10pt */
        .calc-table td {{ vertical-align: top; }}                  /* только здесь - по верху */
        .calc-table .summary td {{ font-weight:bold; text-align:right; }}
        .calc-table .divider td {{ border-top:1px solid #ccc !important; padding:3px 0; height:6px; }}
        .calc-table .detail-list-item {{
            display:block;
            font-size:9pt;               /* детализация 8pt */
            line-height:1.25em;
            margin:2px 0;
            text-align:left;
        }}
        /* маркер: прозрачная середина (обводка + transparent фон) */
        .paint-marker {{
            display:inline-block;
            width:7px; height:7px;
            border-radius:50%;
            border:1px solid #000;
            background-color: transparent;
            margin-right:6px;
            vertical-align:middle;
        }}

        /* MAIN-TABLE: центруем по вертикали для симметрии */
        table.main-table th, table.main-table td {{
            font-size:9pt;
            vertical-align: middle;      /* среднее выравнивание для симметрии padding */
            white-space: nowrap;         /* запрет переноса */
            overflow: hidden;
            text-overflow: ellipsis;
            height:20px;
            text-align:center;
        }}
        table.main-table th {{ background:#f0f0f0; font-weight:bold; }}

        /* Класс для объединённой строки с краской (в main-table) */
        .paint-row td {{
            border-top:1px solid #000;
            border-bottom:1px solid #000;
            background:transparent;
            padding:6px 8px;
        }}

        /* COST-TABLE: избегаем разрыва таблицы по страницам целиком */
        table.cost-table {{ page-break-inside: avoid; break-inside: avoid; -webkit-column-break-inside: avoid; }}
        table.cost-table th, table.cost-table td {{ font-size:9pt; padding:6px; text-align:center; }}
        table.cost-table th {{ background:#f0f0f0; font-weight:bold; }}

        /* Мелкие вспомогательные стили */
        .detail-list-item {{ display:block; font-size:8pt; line-height:1.2em; margin:2px 0; }}
    </style>
    </head>
    <body>

    <!-- Шапка -->
    <div class="project-header">
    <div class="block" style="text-align:left;"><span class="label">Проект:</span> <span class="value">{project_data['number']}</span></div>
    <div class="block" style="text-align:center;"><span class="label">Заказчик:</span> <span class="value">{project_data['customer']}</span></div>
    <div class="block" style="text-align:right;"><span class="label">Дата:</span> <span class="value">{project_data['date']}</span></div>
    </div>

    <!-- Таблица расчётов -->
    {self._generate_calc_table(calculation_data)}

    <!-- Основная таблица (краска убрана, комментарий расширен) -->
    {self._generate_main_table(handle_has_data, remove_paint_column=True)}

    <!-- Таблица стоимости -->
    {self._generate_cost_table(cost_data)}

    </body>
    </html>
    """
            return html

        except Exception as e:
            print(f"[PrintManager] Ошибка генерации HTML: {e}")
            return f"<html><body><h1>Ошибка генерации спецификации</h1><p>{str(e)}</p></body></html>"




    def _generate_calc_table(self, calc_data):
        """
        Генерирует таблицу расчётов.
        calc_data может быть dict (предпочтительно) или список списков.
        Поведение:
        - выводит 4 колонки: площадь деталей, площадь покраски, расход краски, прочее
        - после суммарных значений вставляет тонкую серую линию (divider)
        - детализации (по типу деталей и по краскам) выводятся слева, мелким шрифтом, с маркерами
        """
        # Подготовка данных
        if isinstance(calc_data, dict):
            total_area = calc_data.get('total_area', 0) or 0
            total_paint_area = calc_data.get('total_paint_area', 0) or 0
            detail_areas = calc_data.get('detail_type_areas', {}) or {}
            paint_detail_areas = calc_data.get('detail_type_paint_areas', {}) or {}
            paint_areas = calc_data.get('paint_areas', {}) or {}
            paint_rate = calc_data.get('paint_consumption', 0.35) or 0.35
            total_pieces = calc_data.get('total_pieces', 0) or 0
            total_edge_length = calc_data.get('total_edge_length', 0) or 0
            total_handle_length = calc_data.get('total_handle_length', 0) or 0
            wrapping_cost = calc_data.get('wrapping_cost', 0) or 0
            total_plank_length = calc_data.get('total_plank_length', 0) or 0
            total_gluing_area = calc_data.get('total_gluing_area', 0) or 0
        else:
            # если список/невнятная структура — делаем безопасные пустые
            total_area = 0
            total_paint_area = 0
            detail_areas = {}
            paint_detail_areas = {}
            paint_areas = {}
            paint_rate = 0.35
            total_pieces = len(calc_data) if isinstance(calc_data, (list, tuple)) else 0
            total_edge_length = total_handle_length = wrapping_cost = 0

        # Формат детализации (левый выровненный список, 8pt)
        def format_list_items(dct, unit="м²"):
            if not dct:
                return "<div class='detail-list-item'>Нет данных</div>"
            out = ""
            for name, val in dct.items():
                try:
                    num = float(val)
                    val_text = f"{num:.2f} {unit}"
                except Exception:
                    val_text = f"{val} {unit}"
                out += f"<div class='detail-list-item'><span class='paint-marker'></span><span style='font-weight:normal'>{name}: {val_text}</span></div>"
            return out

        detail_html = format_list_items(detail_areas, "м²")
        paint_detail_html = format_list_items(paint_detail_areas, "м²")

        # Расход краски — список маркеров
        paint_html = ""
        if paint_areas:
            for pname, area in paint_areas.items():
                try:
                    a = float(area)
                except Exception:
                    a = 0
                kg = a * paint_rate
                paint_html += f"<div class='detail-list-item'><span class='paint-marker'></span><span style='font-weight:normal'>{pname}: <strong>{kg:.2f}</strong> кг</span></div>"
        else:
            paint_html = "<div class='detail-list-item'>Нет данных</div>"

        # Прочее
        other_html = f"<div class='detail-list-item'>Деталей: {int(total_pieces)}</div>"
        if total_edge_length:
            other_html += f"<div class='detail-list-item'>Кромка: {float(total_edge_length):.2f} м</div>"
        if total_handle_length:
            other_html += f"<div class='detail-list-item'>Ручки: {float(total_handle_length):.2f} м</div>"
        if wrapping_cost:
            other_html += f"<div class='detail-list-item'>Замотка: {float(wrapping_cost):.0f} ₽</div>"

        # Прочее
        other_html = ""

        if total_pieces:
            other_html += f"<div class='detail-list-item'>Деталей: {int(total_pieces)}</div>"
        if total_edge_length:
            other_html += f"<div class='detail-list-item'>Кромка: {float(total_edge_length):.2f} м</div>"
        if total_plank_length:
            other_html += f"<div class='detail-list-item'>Планки: {float(total_plank_length):.2f} м</div>"
        if total_handle_length:
            other_html += f"<div class='detail-list-item'>Ручки: {float(total_handle_length):.2f} м</div>"
        total_gluing_area = calc_data.get('total_gluing_area', 0) or 0
        if total_gluing_area:
            other_html += f"<div class='detail-list-item'>Склейка: {float(total_gluing_area):.2f} м²</div>"
        if wrapping_cost:
            other_html += f"<div class='detail-list-item'>Замотка: {float(wrapping_cost):.0f} ₽</div>"




        # Верхняя таблица (чёткие колонки)
        html = f"""
        <table class="calc-table" width="100%" cellpadding="0" cellspacing="0">
        <thead>
            <tr>
            <th style="width:25%;">Площадь деталей</th>
            <th style="width:25%;">Площадь покраски</th>
            <th style="width:25%;">Расход краски</th>
            <th style="width:25%;">Прочее</th>
            </tr>
        </thead>
        <tbody>
            <tr>
            <td style="text-align:center; font-weight:bold;">{float(total_area):.2f} м²<div style="margin-top:4px; border-top:1px solid #eee;"></div>{detail_html}</td>
            <td style="text-align:center; font-weight:bold;">{float(total_paint_area):.2f} м²<div style="margin-top:4px; border-top:1px solid #eee;"></div>{paint_detail_html}</td>
            <td style="vertical-align: top;">{paint_html}</td>
            <td style="text-align:left;">{other_html}</td>
            </tr>
        </tbody>
        </table>
        """
        return html

    def _generate_main_table(self, handle_has_data, remove_paint_column=False):
        """
        Генерирует основную таблицу. Поддержка remove_paint_column=True.
        В этой версии строки-разделители по краске выводятся как объединённая строка (colspan),
        чтобы справа в ней отображалась краска (как ты просил).
        """
        table_data = self._get_table_data()
        cols = getattr(self.main_window, 'columns', []) or []

        def col_idx(name):
            return cols.index(name) if name in cols else -1

        len_idx = col_idx('Длина'); wid_idx = col_idx('Ширина')
        qty_idx = col_idx('Кол-во'); thick_idx = col_idx('Толщина')
        sides_idx = col_idx('Сторон'); detail_idx = col_idx('Тип детали')
        paint_idx = col_idx('Краска'); comment_idx = col_idx('Комментарий')
        handle_idx = col_idx('Ручка'); gluing_idx = col_idx('Склейка')

        # Заголовки
        headers = ["№","Размер","Длина","Ширина","Кол-во","Кол-во","Толщина","Сторон","Тип детали"]
        if not remove_paint_column:
            headers.append("Краска")
        headers.append("Комментарий")
        headers_html = "".join(f"<th>{h}</th>" for h in headers)

        # Colgroup: если убираем краску — даём больше места комментарию
        if remove_paint_column:
            colgroup = """
            <colgroup>
                <col style="width:4%;">
                <col style="width:12%;">
                <col style="width:8%;">
                <col style="width:8%;">
                <col style="width:6%;">
                <col style="width:6%;">
                <col style="width:6%;">
                <col style="width:6%;">
                <col style="width:18%;">
                <col style="width:26%;">
            </colgroup>
            """
        else:
            colgroup = """
            <colgroup>
                <col style="width:4%;">
                <col style="width:10%;">
                <col style="width:8%;">
                <col style="width:8%;">
                <col style="width:6%;">
                <col style="width:6%;">
                <col style="width:6%;">
                <col style="width:6%;">
                <col style="width:15%;">
                <col style="width:8%;">
                <col style="width:23%;">
            </colgroup>
            """

        rows_html = ""
        previous_paint = None
        row_number = 1
        max_paint_length = 40

        for row in table_data:
            # пропускаем полностью пустые строки
            if not any(str(c).strip() for c in row):
                continue

            # текущая краска (если есть)
            current_paint = (str(row[paint_idx]).strip() if paint_idx != -1 and paint_idx < len(row) else '')

            # если краска поменялась — вставляем объединённую строку (colspan)
            if previous_paint is not None and current_paint and current_paint != previous_paint:
                # объединённая строка: colspan = len(headers)
                rows_html += f"<tr class='paint-row'><td colspan='{len(headers)}' style='text-align:right; font-weight:bold;'>{current_paint}</td></tr>"
            if previous_paint is None and current_paint:
                rows_html += f"<tr class='paint-row'><td colspan='{len(headers)}' style='text-align:right; font-weight:bold;'>{current_paint}</td></tr>"
            previous_paint = current_paint

            # строим обычную строку
            cells = ""
            # №
            cells += f"<td style='white-space:nowrap;'>{row_number}</td>"
            row_number += 1

            # Размер
            size = ""
            if len_idx != -1 and wid_idx != -1 and len_idx < len(row) and wid_idx < len(row):
                l = str(row[len_idx]).strip(); w = str(row[wid_idx]).strip()
                if l and w:
                    size = f"{l} × {w}"
            cells += f"<td style='white-space:nowrap;'>{size}</td>"

            # порядок колонок
            column_order = ["Длина","Ширина","Кол-во","Кол-во","Толщина","Сторон","Тип детали"]
            for cname in column_order:
                ci = cols.index(cname) if cname in cols else -1
                val = row[ci] if ci != -1 and ci < len(row) else ''
                cells += f"<td style='white-space:nowrap;'>{val}</td>"

            # краска
            if not remove_paint_column:
                paint_val = row[paint_idx] if paint_idx != -1 and paint_idx < len(row) else ''
                ptxt = str(paint_val)
                if len(ptxt) > max_paint_length:
                    ptxt = ptxt[:max_paint_length-3] + '...'
                cells += f"<td style='white-space:nowrap;'>{ptxt}</td>"

            # Комментарий + ручка + склейка
            comment = ""
            if comment_idx != -1 and comment_idx < len(row):
                comment = str(row[comment_idx]).strip()
            if handle_idx != -1 and handle_idx < len(row) and str(row[handle_idx]).strip():
                hv = str(row[handle_idx]).strip()
                comment += (", р" + hv) if comment else ("р" + hv)
            if gluing_idx != -1 and gluing_idx < len(row):
                gv = str(row[gluing_idx]).strip()
                if gv and gv != '0':
                    comment += (", скл" + gv) if comment else ("скл" + gv)

            # комментарий лево-выровненный, nowrap
            cells += f"<td style='text-align:left; white-space:nowrap; overflow:hidden;'>{comment}</td>"

            rows_html += f"<tr>{cells}</tr>"

        table_html = f"""
        <table class="main-table" width="100%" cellpadding="0" cellspacing="0">
            {colgroup}
            <thead><tr>{headers_html}</tr></thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        """
        return table_html

    def _generate_cost_table(self, cost_data):
        """
        Генерируем таблицу стоимости.
        Пропускаем строки с total_cost == 0 и дополнительные нули.
        Общий итог выводим объединённой ячейкой (colspan) под колонками работ/фасадов,
        сам итог числом (целым) располагается в колонке 'Итог'.
        Стараемся не разбивать таблицу по страницам целиком (page-break-inside: avoid).
        """
        if not cost_data:
            return "<div>Нет данных для расчета стоимости</div>"

        # --- Собираем только активные фасады (с ненулевыми значениями) ---
        active_facades = set()
        for data in cost_data.values():
            if not isinstance(data, dict):
                continue
            by_detail = data.get('by_detail', {}) or {}
            for f, val in by_detail.items():
                cost_value = 0
                if isinstance(val, dict):
                    cost_value = val.get('cost', 0) or 0
                else:
                    cost_value = val or 0
                if float(cost_value) != 0:
                    active_facades.add(f)
        facade_types = sorted(list(active_facades))

        # --- Проверяем, нужно ли выводить колонку "прочее" ---
        show_other = any(
            (data.get('additional_cost', 0) or 0) != 0
            for data in cost_data.values()
            if isinstance(data, dict)
        )

        # --- Заголовки таблицы ---
        headers = ["Работы"] + facade_types
        if show_other:
            headers.append("прочее")
        headers += ["Итог", "Исполнитель"]
        headers_html = "".join(f"<th>{h}</th>" for h in headers)

        rows_html = ""
        row_totals = []  # для расчета общего итога из целых

        for work, data in cost_data.items():
            if not isinstance(data, dict):
                continue

            by_detail = data.get('by_detail', {}) or {}
            additional = data.get('additional_cost', 0) or 0
            total = data.get('total_cost', 0) or 0

            # Пропускаем строки с нулевым итогом и нулевым "прочее"
            if float(total) == 0 and (additional == 0 or not show_other):
                continue

            # --- Формируем ячейки по фасадам ---
            facade_cells = ""
            row_sum = 0  # сумма по строке, целые числа
            for ft in facade_types:
                cost_value = 0
                val = by_detail.get(ft, {})
                if isinstance(val, dict):
                    cost_value = val.get('cost', 0) or 0
                else:
                    cost_value = val or 0
                int_cost = int(cost_value)
                facade_cells += f"<td>{int_cost}</td>"
                row_sum += int_cost

            # --- "прочее" ---
            if show_other:
                int_additional = int(additional)
                facade_cells += f"<td>{int_additional}</td>"
                row_sum += int_additional

            # добавляем сумму строки для общего итога
            row_totals.append(row_sum)

            # итог по строке
            row_total_display = row_sum

            # исполнитель
            worker = (self.calculator.workers.get(work) if hasattr(self.calculator, 'workers') else '') or ''

            rows_html += f"""
            <tr>
                <td>{work}</td>
                {facade_cells}
                <td>{row_total_display}</td>
                <td>{worker}</td>
            </tr>
            """

        # --- Общий итог из целых строк ---
        total_sum = sum(row_totals)

        # добавляем строку общего итога
        if headers:
            colspan_for_label = max(1, len(headers) - 2)  # до колонки "Итог"
            rows_html += f"""
            <tr>
                <td colspan="{colspan_for_label}" style="text-align:left;"><strong>ОБЩИЙ ИТОГ:</strong></td>
                <td style="text-align:center;"><strong>{total_sum}</strong></td>
                <td></td>
            </tr>
            """

        table_html = f"""
        <div style="page-break-inside: avoid; break-inside: avoid;">
        <table class="cost-table" width="100%" cellpadding="0" cellspacing="0">
            <thead><tr>{headers_html}</tr></thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
        </div>
        """
        return table_html










    def _write_pdf_file(self, html_string: str, output_path: str):
        """
        Записывает HTML->PDF через WeasyPrint. Бросает исключение при ошибке.
        """
        # HTML(string=html_string).write_pdf требует корректной среды (weasyprint настроен)
        HTML(string=html_string).write_pdf(output_path)

    def _open_file(self, path: str):
        """
        Открывает файл в системной программе (предпросмотр).
        Кроссплатформенно: Windows: os.startfile, macOS: open, Linux: xdg-open.
        """
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(path)  # откроет в приложении по умолчанию
                return True
            elif system == "Darwin":
                subprocess.run(["open", path], check=False)
                return True
            else:
                # Linux/Unix
                opener = shutil.which("xdg-open") or shutil.which("gio") or shutil.which("gnome-open")
                if opener:
                    subprocess.run([opener, path], check=False)
                    return True
                else:
                    return False
        except Exception:
            return False



    def _send_file_to_printer(self, path: str) -> bool:

        try:
            if not os.path.exists(path):
                print(f"[PrintManager] Файл для печати не найден: {path}")
                return False

            system = platform.system()

            if system == "Windows":
                # Попытка 1: ShellExecuteW через ctypes — часто надёжнее, чем os.startfile
                try:
                    # SEE_MASK_NO_CONSOLE = 0x00008000  # not strictly necessary
                    res = ctypes.windll.shell32.ShellExecuteW(None, "print", path, None, None, 0)
                    # Если > 32 — успешно, иначе код ошибки
                    if isinstance(res, int) and res > 32:
                        return True
                    # Иногда ShellExecuteW возвращает an integer-like >32 on success
                except Exception as e:
                    print(f"[PrintManager] ShellExecuteW failed: {e}")

                # Попытка 2: os.startfile
                try:
                    os.startfile(path, "print")
                    return True
                except Exception as e:
                    print(f"[PrintManager] os.startfile(print) failed: {e}")

                # Попытка 3: старт через cmd (start)
                try:
                    # Формируем команду безопасно — cmd /c start "" "path"
                    subprocess.run(["cmd", "/c", "start", "", "/min", path], check=False)
                    return True
                except Exception as e:
                    print(f"[PrintManager] cmd start fallback failed: {e}")
                    return False

            elif system == "Darwin":
                # macOS
                if shutil.which("lp"):
                    subprocess.run(["lp", path], check=True)
                    return True
                elif shutil.which("lpr"):
                    subprocess.run(["lpr", path], check=True)
                    return True
                else:
                    print("[PrintManager] lp/lpr not found on macOS")
                    return False
            else:
                # Linux/Unix
                if shutil.which("lp"):
                    subprocess.run(["lp", path], check=True)
                    return True
                elif shutil.which("lpr"):
                    subprocess.run(["lpr", path], check=True)
                    return True
                else:
                    print("[PrintManager] lp/lpr not found on Linux")
                    return False

        except subprocess.CalledProcessError as e:
            print(f"[PrintManager] Ошибка выполнения команды печати: {e}")
            return False
        except Exception as e:
            print(f"[PrintManager] Непредвиденная ошибка при отправке на печать: {e}")
            return False


    def save_pdf(self):
        """Сохраняет PDF через WeasyPrint (пользователь выбирает путь)."""
        try:
            html = self.generate_specification_html()

            # Определяем базовую папку save/pdf
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            save_dir = os.path.join(base_dir, 'save', 'pdf')
            os.makedirs(save_dir, exist_ok=True)

            # Формируем дефолтное имя
            project_number = getattr(self.main_window, 'current_project_number', '') or 'project'
            customer_name = getattr(self.main_window, 'customer_name', '') or 'unknown'
            date_str = getattr(self.main_window, 'project_date', QDateTime.currentDateTime().toString('dd.MM.yyyy'))
            safe_name = f"{project_number}_{customer_name}_{date_str}.pdf".replace("/", "-").replace("\\", "-")
            default_path = os.path.join(save_dir, safe_name)

            # Диалог выбора пути (дефолтный путь в save/pdf)
            filepath, _ = QFileDialog.getSaveFileName(self.main_window, "Сохранить PDF", default_path, "PDF Files (*.pdf)")
            if not filepath:
                return

            # Пишем PDF
            self._write_pdf_file(html, filepath)

            # Статус
            try:
                if hasattr(self.main_window, 'show_status_message'):
                    self.main_window.show_status_message(f'PDF сохранен: {filepath}', 3000)
            except Exception:
                pass

        except Exception as e:
            QMessageBox.critical(self.main_window, 'Ошибка', f'Ошибка сохранения PDF: {str(e)}')



    def preview_pdf(self):
        """Генерирует временный PDF и открывает его в внешнем просмотрщике (предпросмотр)."""
        try:
            html = self.generate_specification_html()
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp_path = tmp.name
            tmp.close()
            try:
                self._write_pdf_file(html, tmp_path)
            except Exception as e:
                # удалим временный файл, если запись не удалась
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                raise

            opened = self._open_file(tmp_path)
            if not opened:
                QMessageBox.information(self.main_window, 'Предпросмотр', f'PDF сохранён во временный файл: {tmp_path}')
            else:
                try:
                    if hasattr(self.main_window, 'show_status_message'):
                        self.main_window.show_status_message('Предпросмотр открыт в внешнем приложении', 3000)
                except Exception:
                    pass

        except Exception as e:
            QMessageBox.critical(self.main_window, 'Ошибка', f'Ошибка предпросмотра: {str(e)}')

    def print_pdf(self):
        """Генерирует временный PDF и пытается отправить его сразу на принтер."""
        try:
            html = self.generate_specification_html()

            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp_path = tmp.name
            tmp.close()

            try:
                # Пишем PDF
                self._write_pdf_file(html, tmp_path)
            except Exception as e:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка при генерации PDF: {e}")
                return

            # Проверяем существование файла
            if not os.path.exists(tmp_path):
                QMessageBox.critical(self.main_window, "Ошибка", "Временный PDF-файл не найден после генерации.")
                return

            # Пытаемся отправить на печать
            sent = self._send_file_to_printer(tmp_path)
            if sent:
                try:
                    if hasattr(self.main_window, 'show_status_message'):
                        self.main_window.show_status_message('Документ отправлен на печать', 3000)
                except Exception:
                    pass
                return
            else:
                # Не удалось — даём пользователю выбор: открыть предпросмотр или показать ошибку
                reply = QMessageBox.question(
                    self.main_window,
                    "Печать",
                    "Не удалось отправить документ на печать автоматически.\nОткрыть файл для ручной печати?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    opened = self._open_file(tmp_path)
                    if not opened:
                        QMessageBox.information(self.main_window, "Предпросмотр", f"Файл сохранён: {tmp_path}")
                else:
                    QMessageBox.warning(self.main_window, "Печать", "Отправка на печать отменена пользователем или не удалась.")
                return

        except Exception as e:
            QMessageBox.critical(self.main_window, "Ошибка", f"Ошибка печати: {e}")






    def _generate_project_header(self, project_data):
        """Генерирует шапку проекта в одну строку"""
        # Отвечаю на вопрос о дате: это текущая дата (дата генерации отчета)
        return f"""
        <div class="project-header">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td width="33%" align="left" valign="top"><strong>Проект №{project_data['number']}</strong></td>
                    <td width="34%" align="center" valign="top"><strong>Заказчик:</strong> {project_data['customer']}</td>
                    <td width="33%" align="right" valign="top"><strong>Дата:</strong> {project_data['date']}</td>
                </tr>
            </table>
        </div>
        """

    def _format_detail_list(self, details, unit):
        """Форматирует детализацию в виде списка"""
        if not details:
            return "<div class='detail-item'>Нет данных</div>"
        
        html = ""
        for name, value in details.items():
            if value > 0:
                display_name = name.title() if name != 'без типа' else 'Общие'
                html += f"<div class='detail-item'>{display_name}: {value:.2f} {unit}</div>"
        
        return html if html else "<div class='detail-item'>Нет данных</div>"

    def _format_paint_consumption(self, paint_areas):
        """Форматирует расход краски по типам с выделением цифр жирным"""
        if not paint_areas:
            return "<div class='detail-item'>Нет данных</div>"
        
        html = ""
        for paint_type, area in paint_areas.items():
            if area > 0 and paint_type != 'Без краски':
                paint_kg = area * self.main_window.table_manager.calculate(return_data=True).get('paint_consumption', 0.35)
                display_name = paint_type if paint_type != 'Без краски' else 'Без указания'
                
                # Разделяем число и единицы измерения, число делаем жирным
                kg_text = f"{paint_kg:.2f}"
                html += f"<div class='detail-item'>{display_name}: <strong>{kg_text}</strong> кг</div>"
        
        return html if html else "<div class='detail-item'>Нет данных</div>"







