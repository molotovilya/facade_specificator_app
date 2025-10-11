from imports import *
from constants import *
from file_operations import *
from table_manager import TableManager
from project_manager import ProjectManager
from table_structure_dialog import TableStructureDialog
from rates_dialog import RatesDialog
from facade_types_dialog import FacadeTypesDialog
from work_types_dialog import WorkTypesDialog
from combo_delegate import ComboDelegate
from PyQt5.QtWidgets import QSplitter, QGroupBox
from ui_config import *
import os
from border_delegate import BorderDelegate
from work_types_config import load_work_types
from print_manager import PrintManager
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtGui import QTextDocument  # ← ДОБАВИТЬ ЭТОТ ИМПОРТ

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()
        
        self.group_end_rows = set()
        
        # Сначала ВСЯ инициализация данных из КОНФИГОВ
        self.setWindowTitle('Спецификация')

        self.config = load_config()
        self.rates = load_rates()
        self.detail_types = load_facade_types()
        self.work_types = load_work_types()
        self.columns = load_columns_config()  # ← Колонки из конфига
        self.current_project_number = None
        self.customer_name = ""
        self.clip_value = None
        self.project_date = QDateTime.currentDateTime().toString('dd.MM.yyyy')
        self.is_modified = False  # Флаг изменений
        self.updating_style = False  # Флаг обновления стилей

        # Инициализируем менеджеры ПОСЛЕ загрузки конфигов
        self.table_manager = TableManager(self)
        self.project_manager = ProjectManager(self)
        self.print_manager = PrintManager(self)  # ← ПЕРЕМЕСТИТЬ ПОСЛЕ table_manager

        # Инициализируем UI
        self.init_ui()
        
        # УБЕДИТЕСЬ что колонки установлены ПЕРЕД загрузкой автосохранения
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        
        # Обновляем делегат
        self.update_detail_type_delegate()
        
        # Устанавливаем минимальный размер
        self.setMinimumSize(1000, 600)
        
        # Показываем окно
        self.show()
        
        # Немедленно максимизируем после показа
        self.showMaximized()
        
        # Принудительно активируем окно
        self.raise_()
        self.activateWindow()
        
        # Загружаем проект (после установки колонок!)
        self.load_last_project()



    def init_ui(self):


        # Главный вертикальный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Верхняя панель с информацией о проекте
        info_layout = QHBoxLayout()
        
        self.lbl_project_number = QLabel("Проект №: ")
        self.le_project_number = QLineEdit()
        self.le_project_number.setMaximumWidth(50)
        self.le_project_number.textChanged.connect(self.update_project_number)
        
        self.lbl_customer = QLabel("Заказчик: ")
        self.le_customer = QLineEdit()
        self.le_customer.setMaximumWidth(150)
        self.le_customer.textChanged.connect(self.update_customer_name)
        

        # Поле для даты
        self.lbl_date = QLabel("Дата: ")
        self.le_date = QLineEdit()
        self.le_date.setMaximumWidth(100)
        self.le_date.setText(self.project_date)  # Устанавливаем текущую дату
        self.le_date.textChanged.connect(self.update_date)  # Подключаем сигнал


        # Добавляем кнопку упорядочивания
        self.btn_sort = QPushButton("Sort")
        self.btn_sort.setMaximumWidth(100)
        self.btn_sort.setMinimumHeight(30)
        self.btn_sort.setStyleSheet("font-size: 9pt;")
        self.btn_sort.clicked.connect(self.sort_table)
        
        # Добавляем галочку для разделителей
        self.cb_show_separators = QCheckBox("Разделители")
        self.cb_show_separators.setChecked(True)
        self.cb_show_separators.setStyleSheet("font-size: 9pt;")

        info_layout.addWidget(self.lbl_project_number)
        info_layout.addWidget(self.le_project_number)
        info_layout.addWidget(self.lbl_customer)
        info_layout.addWidget(self.le_customer)
        info_layout.addWidget(self.lbl_date)
        info_layout.addWidget(self.le_date)
        info_layout.addWidget(self.btn_sort)
        info_layout.addWidget(self.cb_show_separators)
        info_layout.addStretch()

        # Основной горизонтальный layout для таблицы и правой панели
        content_layout = QHBoxLayout()
        
        # ЛЕВАЯ ЧАСТЬ - таблица
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        # Таблица - Устанавливаем колонки СРАЗУ
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.columns))  # ← ВАЖНО
        self.table.setHorizontalHeaderLabels(self.columns)  # ← ВАЖНО
        self.table.setRowCount(10)
        self.table.setFocusPolicy(Qt.StrongFocus)
        self.table.setFocus()



        # Добавляем обработчик изменений таблицы
        self.table.itemChanged.connect(self._handle_table_change)


        # Установите BorderDelegate как основной делегат для ВСЕХ ячеек
        self.border_delegate = BorderDelegate()
        self.table.setItemDelegate(self.border_delegate)
        
        # ТОЛЬКО потом устанавливайте комбо-делегат для конкретной колонки
        self.update_detail_type_delegate()

        # Заполняем пустые ячейки
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = QTableWidgetItem('')
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r, c, item)
        
        # ТОЛЬКО ПОСЛЕ этого устанавливаем менеджер таблицы
        self.table_manager.set_table(self.table)
        
        # Стиль для заголовка
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                border-bottom: 1px solid #c0c0c0;
                background-color: #f0f0f0;
                padding: 4px;
            }
        """)
        
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.installEventFilter(self)
        
        table_layout.addWidget(self.table)
        
        # ПРАВАЯ ЧАСТЬ - вертикальный splitter для кнопок и расчета
        right_splitter = QSplitter(Qt.Vertical)
        
        # ВЕРХ ПРАВОЙ ЧАСТИ - кнопки управления
        buttons_widget = QWidget()
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setSpacing(10)
        
        # Группа 1: Управление файлами
        file_group = QVBoxLayout()
        file_label = QLabel("📁 Управление")
        file_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        file_group.addWidget(file_label)
        
        self.btn_new = QPushButton('Новый проект')
        self.btn_save = QPushButton('Сохранить проект')
        self.btn_load = QPushButton('Загрузить проект')
        self.btn_clear = QPushButton('Очистить таблицу')
        
        for btn in [self.btn_new, self.btn_save, self.btn_load, self.btn_clear]:
            btn.setMinimumHeight(30)
            btn.setStyleSheet("font-size: 11pt;")
            file_group.addWidget(btn)
        
        file_group.addSpacing(5)
        
        # Группа 2: Настройки структуры
        structure_group = QVBoxLayout()
        structure_label = QLabel("⚙️ Структура")
        structure_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        structure_group.addWidget(structure_label)
        
        self.btn_structure = QPushButton('Колонки таблицы')
        self.btn_facades = QPushButton('Типы фасадов')
        self.btn_work_types = QPushButton('Типы работ')
        self.btn_other = QPushButton('Прочее')
        
        for btn in [self.btn_structure, self.btn_facades, self.btn_work_types, self.btn_other]:
            btn.setMinimumHeight(30)
            btn.setStyleSheet("font-size: 11pt;")
            structure_group.addWidget(btn)
        
        structure_group.addSpacing(5)
        
        # Группа 3: Вывод
        output_group = QVBoxLayout()
        output_label = QLabel("📊 Вывод")
        output_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        output_group.addWidget(output_label)
        
        # Создаем горизонтальный layout для двух кнопок
        rates_buttons_layout = QHBoxLayout()

        # Кнопка ставок
        self.btn_rates = QPushButton('Ставки')
        self.btn_rates.setMinimumHeight(30)
        self.btn_rates.setStyleSheet("font-size: 11pt; padding: 2px;")
        rates_buttons_layout.addWidget(self.btn_rates)

        # Кнопка стоимости работ
        self.btn_costs = QPushButton('Стоимость')
        self.btn_costs.setMinimumHeight(30)
        self.btn_costs.setStyleSheet("font-size: 11pt; padding: 2px;")
        rates_buttons_layout.addWidget(self.btn_costs)

        # Добавляем горизонтальный layout в вертикальный
        output_group.addLayout(rates_buttons_layout)

        # Кнопка расчета
        self.btn_calc = QPushButton('Рассчитать')
        self.btn_calc.setMinimumHeight(30)
        self.btn_calc.setStyleSheet("font-size: 11pt;")
        output_group.addWidget(self.btn_calc)

        # Создаем горизонтальный layout для двух кнопок печати
        print_buttons_layout = QHBoxLayout()

        # Кнопка сохранения PDF
        self.btn_save_pdf = QPushButton('Сохранить PDF')
        self.btn_save_pdf.setMinimumHeight(30)
        self.btn_save_pdf.setStyleSheet("font-size: 11pt; padding: 2px;")
        print_buttons_layout.addWidget(self.btn_save_pdf)

        # Кнопка предпросмотра печати
        self.btn_print_preview = QPushButton('Печать')
        self.btn_print_preview.setMinimumHeight(30)
        self.btn_print_preview.setStyleSheet("font-size: 11pt; padding: 2px;")
        print_buttons_layout.addWidget(self.btn_print_preview)

        # Добавляем горизонтальный layout в вертикальный
        output_group.addLayout(print_buttons_layout)
        
        # Добавляем все группы в правый layout
        buttons_layout.addLayout(file_group)
        buttons_layout.addLayout(structure_group)
        buttons_layout.addLayout(output_group)
        buttons_layout.addStretch()
        







        # НИЗ ПРАВОЙ ЧАСТИ - область расчета (4 КВАДРАНТА)
        calc_widget = QWidget()
        calc_widget.setStyleSheet(f"""
            QLabel {{
                padding: 2px;
                margin: 1px;
                font-size: {FONT_SIZE_LARGE}pt;
            }}
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {BORDER_COLOR};
                border-radius: 5px;
                margin-top: 1ex;
                font-size: {FONT_SIZE_GROUPBOX}pt;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            .content-label {{
                margin-top: {CONTENT_MARGIN_TOP};
            }}
        """)

        # Основная сетка 2x2
        main_calc_layout = QGridLayout(calc_widget)
        main_calc_layout.setContentsMargins(5, 5, 5, 5)
        main_calc_layout.setSpacing(10)

        # 1. Верхний левый - Площадь деталей по типам
        details_group = QGroupBox("📏 Площадь деталей")
        details_layout = QVBoxLayout(details_group)
        self.details_area = QLabel("")
        self.details_area.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.details_area.setWordWrap(True)
        details_layout.addWidget(self.details_area)
        main_calc_layout.addWidget(details_group, 0, 0)

        # 2. Нижний левый - Прочее (длины)
        other_group = QGroupBox("📐 Прочее")
        other_layout = QVBoxLayout(other_group)
        self.other_area = QLabel("")
        self.other_area.setAlignment(Qt.AlignRight | Qt.AlignTop)
        other_layout.addWidget(self.other_area)
        main_calc_layout.addWidget(other_group, 1, 0)

        # 3. Верхний правый - Площадь покраски по типам
        painting_group = QGroupBox("🎨 Площадь покраски")
        painting_layout = QVBoxLayout(painting_group)
        self.painting_area = QLabel("")
        self.painting_area.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.painting_area.setWordWrap(True)
        painting_layout.addWidget(self.painting_area)
        main_calc_layout.addWidget(painting_group, 0, 1)

        # 4. Нижний правый - Расход краски по типам
        paint_group = QGroupBox("🖌️ Расход краски")
        paint_layout = QVBoxLayout(paint_group)
        self.paint_area = QLabel("")
        self.paint_area.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.paint_area.setWordWrap(True)
        paint_layout.addWidget(self.paint_area)
        main_calc_layout.addWidget(paint_group, 1, 1)

        # После создания всех QLabel в расчетной области
        for label in [self.details_area, self.other_area, self.painting_area, self.paint_area]:
            label.setProperty("class", "content-label")

        # Настраиваем пропорции
        main_calc_layout.setRowStretch(0, 1)
        main_calc_layout.setRowStretch(1, 1)
        main_calc_layout.setColumnStretch(0, 1)
        main_calc_layout.setColumnStretch(1, 1)
        
        # Собираем правую часть
        right_splitter.addWidget(buttons_widget)
        right_splitter.addWidget(calc_widget)
        right_splitter.setSizes(SPLITTER_RATIO)
        
        # Добавляем таблицу и правую панель в горизонтальный layout
        content_layout.addWidget(table_widget, 7)
        content_layout.addWidget(right_splitter, 3)
        
        # Status bar
        self.status_bar = QStatusBar(self)
        
        # Собираем все вместе
        main_layout.addLayout(info_layout)
        main_layout.addLayout(content_layout)
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)


        # # ДОБАВЛЯЕМ СТИЛИ ДЛЯ ВСЕХ КНОПОК ПОСЛЕ ИХ СОЗДАНИЯ
        # buttons = [
        #     self.btn_new, self.btn_save, self.btn_load, self.btn_clear,
        #     self.btn_structure, self.btn_facades, self.btn_work_types, self.btn_other,
        #     self.btn_rates, self.btn_costs, self.btn_calc, self.btn_save_pdf,
        #     self.btn_print_preview, self.btn_sort
        # ]
        
        # for button in buttons:
        #     if button:  # Проверяем что кнопка существует
        #         button.setStyleSheet("""
        #             min-height: 25px; 
        #             padding: 3px; 
        #             font-size: 10pt;
        #             margin: 1px;
        #         """)



        # ПОДКЛЮЧАЕМ СИГНАЛЫ
        self.btn_new.clicked.connect(self.project_manager.new_project)
        self.btn_save.clicked.connect(self.project_manager.save_project)
        self.btn_load.clicked.connect(self.project_manager.load_project)
        self.btn_clear.clicked.connect(self.clear_table_completely)
        self.btn_structure.clicked.connect(self.open_structure_dialog)
        self.btn_facades.clicked.connect(self.open_facade_types_dialog)
        self.btn_work_types.clicked.connect(self.open_work_types_dialog)
        self.btn_rates.clicked.connect(self.open_rates_dialog)
        self.btn_calc.clicked.connect(self.table_manager.calculate)
        self.btn_other.clicked.connect(self.open_other_settings)
        self.btn_costs.clicked.connect(self.show_costs_table)

        # ДОБАВИТЬ ЭТИ ДВЕ СТРОКИ ↓
        self.btn_save_pdf.clicked.connect(self.print_manager.save_pdf)
        # self.btn_print_preview.clicked.connect(self.print_manager.preview_pdf)
        self.btn_print_preview.clicked.connect(self.print_manager.print_pdf)

        
        

        self.table.itemChanged.connect(self.table_manager.handle_item_change)
        self.cb_show_separators.stateChanged.connect(self.toggle_separators)







    def force_calculation(self):
        """Принудительно выполняет расчет и обновляет интерфейс"""
        try:
            # Проверяем, что table_manager существует и инициализирован
            if not hasattr(self, 'table_manager') or not self.table_manager:
                print("Table manager not initialized")
                return False
                
            # Выполняем расчет
            calculation_data = self.table_manager.calculate(return_data=True)
            if calculation_data:
                self.update_calc_area(calculation_data)
                return True
            return False
        except Exception as e:
            print(f"Ошибка при расчете: {e}")
            import traceback
            traceback.print_exc()
            return False

    def block_signals(self, block):
        """Блокирует или разблокирует сигналы полей ввода"""
        self.le_project_number.blockSignals(block)
        self.le_customer.blockSignals(block)
        self.le_date.blockSignals(block)

    def mark_as_modified(self):
        """Пометить проект как измененный"""
        self.is_modified = True
        self.update_window_title()

    def mark_as_saved(self):
        """Пометить проект как сохраненный"""
        self.is_modified = False
        self.update_window_title()

    def show_costs_table(self):
        from cost_table_dialog import CostTableDialog
        dlg = CostTableDialog(self)
        dlg.exec_()

    def show_print_menu(self):
        """Показывает меню печати"""
        menu = QMenu(self)
        
        preview_action = QAction('Предпросмотр PDF', self)
        preview_action.triggered.connect(self.print_manager.preview_pdf)
        menu.addAction(preview_action)
        
        save_action = QAction('Сохранить PDF', self)
        save_action.triggered.connect(self.print_manager.save_pdf)
        menu.addAction(save_action)
        
        # Показываем меню под кнопкой
        menu.exec_(self.btn_print.mapToGlobal(self.btn_print.rect().bottomLeft()))


    def update_project_number(self, text):
        try:
            if text.strip():
                self.current_project_number = int(text.strip())
            else:
                self.current_project_number = None
            self.mark_as_modified()  # Добавляем эту строку
        except ValueError:
            self.le_project_number.setText(str(self.current_project_number) if self.current_project_number else "")

    def update_customer_name(self, text):
        self.customer_name = text.strip()
        self.mark_as_modified()  # Добавляем эту строку

    def update_date(self, text):
        self.project_date = text.strip()
        self.mark_as_modified()  # Добавляем эту строку

        
    def update_detail_type_delegate(self):
        try:
            if 'Тип детали' in self.columns:
                idx = self.columns.index('Тип детали')
                # Создаем комбинированный делегат и передаем ему border_delegate как parent
                combo_delegate = ComboDelegate(lambda: self.detail_types, self.table)
                
                # Устанавливаем border_delegate как родительский для комбо-делегата
                combo_delegate.parent_delegate = self.border_delegate
                
                self.table.setItemDelegateForColumn(idx, combo_delegate)
        except Exception as e:
            print(f"Ошибка в update_detail_type_delegate: {str(e)}")

    def refresh_delegates(self):
        """Принудительно обновляет все делегаты"""
        self.update_detail_type_delegate()


    def set_bottom_border(self, row, col):
        """Устанавливает флаг для отрисовки границы"""
        item = self.table.item(row, col)
        if item:
            item.setData(Qt.UserRole, "bottom_border")
        # НЕ вызываем update здесь - это замедлит работу

    def test_underline(self):
        """Тестовый метод - устанавливает подчеркивание для первых 5 ячеек"""
        for row in range(5):
            for col in range(self.table.columnCount()):
                self.set_bottom_border(row, col)



    def _delayed_show(self):
        """Показывает окно после полной инициализации"""
        self.showMaximized()
        self.load_last_project()

    def _load_autosave_data(self, autosave_data):
        """Загружает данные из автосохранения"""
        try:
            # Восстанавливаем данные
            self.columns = autosave_data.get('columns', self.columns)
            self.detail_types = autosave_data.get('detail_types', self.detail_types)
            self.current_project_number = autosave_data.get('project_number')
            self.customer_name = autosave_data.get('customer_name', '')
            
            # Обновляем поле заказчика в UI
            self.le_customer.setText(self.customer_name)
            
            # Обновляем структуру таблицы
            self.table.setColumnCount(len(self.columns))
            self.table.setHorizontalHeaderLabels(self.columns)
            
            # Очищаем таблицу перед загрузкой новых данных
            self.table.setRowCount(0)
            
            # Загружаем данные таблицы
            table_data = autosave_data.get('table_data', [])
            
            if table_data:
                self.table.setRowCount(len(table_data))
                for row, row_data in enumerate(table_data):
                    for col, value in enumerate(row_data):
                        if col < self.table.columnCount():
                            item = QTableWidgetItem(str(value))
                            item.setTextAlignment(Qt.AlignCenter)
                            self.table.setItem(row, col, item)
            
            # Обновляем делегат для типа детали
            self.update_detail_type_delegate()
            
            # Обновляем заголовок окна
            self.update_window_title()
            
            self.show_status_message('Загружено автосохранение', 3000)
            
        except Exception as e:
            print(f"Ошибка при загрузке автосохранения: {e}")
            QMessageBox.warning(self, 'Ошибка', 'Не удалось загрузить автосохранение')

    def load_last_project(self):
        """Загружает автосохранение или последний проект"""
        # Пытаемся загрузить автосохранение
        self.load_autosave()  # <- ПРАВИЛЬНОЕ имя метода
        
        # Если автосохранение не загрузилось, пробуем последний проект
        last_project = self.config.get('last_project')
        if last_project and os.path.exists(last_project):
            try:
                project_data = load_project_data(last_project)
                self.project_manager._load_project_data(project_data, last_project)
                self.show_status_message(f'Загружен последний проект', 3000)
            except Exception as e:
                print(f"Ошибка загрузки последнего проекта: {str(e)}")

    # def closeEvent(self, event):
    #     """Сохраняем настройки при закрытии"""
    #     try:
    #         # Удаляем пустые строки перед закрытием (если менеджер существует)
    #         if hasattr(self, 'table_manager') and self.table_manager and hasattr(self.table_manager, 'remove_empty_rows'):
    #             self.table_manager.remove_empty_rows()
            
    #         if self.is_modified:
    #             reply = QMessageBox.question(self, 'Сохранение проекта',
    #                                         'Проект был изменен. Сохранить изменения?',
    #                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                
    #             if reply == QMessageBox.Save:
    #                 # Сохраняем проект через менеджер (если существует)
    #                 if hasattr(self, 'project_manager') and self.project_manager:
    #                     self.project_manager.save_project()
    #                     # Если сохранение прошло успешно, закрываем
    #                     if not self.is_modified:
    #                         event.accept()
    #                     else:
    #                         event.ignore()
    #                 else:
    #                     event.ignore()
    #             elif reply == QMessageBox.Discard:
    #                 event.accept()
    #             else:
    #                 event.ignore()
    #                 return
    #         else:
    #             event.accept()
                
    #     except Exception as e:
    #         print(f"Ошибка при закрытии: {e}")
    #         event.accept()  # Все равно закрываем при ошибке
        
    #     # Сохраняем текущий проект если он открыт
    #     if hasattr(self, 'current_project_path') and self.current_project_path:
    #         self.config['last_project'] = self.current_project_path
        
    #     # Сохраняем геометрию окна
    #     self.config['window_geometry'] = {
    #         'x': self.x(),
    #         'y': self.y(),
    #         'width': self.width(),
    #         'height': self.height()
    #     }
        
    #     # Сохраняем состояние окна (развернуто/не развернуто)
    #     self.config['window_maximized'] = self.isMaximized()
        
    #     save_config(self.config)
        
    #     # Сохраняем текущее состояние таблицы
    #     self._save_current_state()
        
    #     event.accept()

    def closeEvent(self, event):
        """Сохраняем настройки при закрытии с диалогом на русском"""
        try:
            # Удаляем пустые строки перед закрытием (если менеджер существует)
            if hasattr(self, 'table_manager') and self.table_manager and hasattr(self.table_manager, 'remove_empty_rows'):
                self.table_manager.remove_empty_rows()

            if self.is_modified:
                # Создаем диалог на русском
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Сохранение проекта")
                msg_box.setText("Проект был изменен. Сохранить изменения?")
                save_btn = msg_box.addButton("Сохранить", QMessageBox.YesRole)
                discard_btn = msg_box.addButton("Нет", QMessageBox.NoRole)
                cancel_btn = msg_box.addButton("Отмена", QMessageBox.RejectRole)
                msg_box.setDefaultButton(save_btn)
                msg_box.exec_()

                if msg_box.clickedButton() == save_btn:
                    # Сохраняем проект через менеджер (если существует)
                    if hasattr(self, 'project_manager') and self.project_manager:
                        self.project_manager.save_project()
                        if not self.is_modified:
                            event.accept()
                        else:
                            event.ignore()
                    else:
                        event.ignore()
                elif msg_box.clickedButton() == discard_btn:
                    event.accept()
                else:  # Отмена
                    event.ignore()
                    return
            else:
                event.accept()

        except Exception as e:
            print(f"Ошибка при закрытии: {e}")
            event.accept()  # Все равно закрываем при ошибке

        # Сохраняем текущий проект если он открыт
        if hasattr(self, 'current_project_path') and self.current_project_path:
            self.config['last_project'] = self.current_project_path

        # Сохраняем геометрию окна
        self.config['window_geometry'] = {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height()
        }

        # Сохраняем состояние окна (развернуто/не развернуто)
        self.config['window_maximized'] = self.isMaximized()

        save_config(self.config)

        # Сохраняем текущее состояние таблицы
        self._save_current_state()
        
        event.accept()



    def clear_table_completely(self):
        """Полная очистка таблицы с удалением разделителей"""
        # Очищаем все данные о разделителях
        self.group_end_rows.clear()
        
        # Сбрасываем все пользовательские данные в ячейках (включая разделители)
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, None)  # Удаляем все пользовательские данные
        self.table.blockSignals(False)
        
        # Вызываем очистку через менеджер таблицы
        if hasattr(self, 'table_manager') and self.table_manager:
            self.table_manager.clear_table()
        
        # Принудительно перерисовываем таблицу
        self.table.viewport().update()
        
        # Сбрасываем расчетную область
        self.update_calc_area({})
        
        self.show_status_message('Таблица полностью очищена', 2000)


    def _save_current_state(self):
        """Сохраняет текущее состояние таблицы"""
        try:
            print("Собираем данные для автосохранения...")
            
            # Берем актуальные данные прямо сейчас
            table_data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    text = item.text() if item else ''
                    row_data.append(text)
                    if text:  # Логируем непустые ячейки
                        print(f"Ячейка [{row},{col}]: '{text}'")
                table_data.append(row_data)
            
            autosave_data = {
                'project_number': self.current_project_number,
                'customer_name': self.customer_name,
                'project_date': self.project_date,  # Добавляем дату
                'columns': self.columns,
                'table_data': table_data,
                'detail_types': self.detail_types
            }
            
            save_autosave(autosave_data)
            print("Текущее состояние сохранено в автосохранение")
            
        except Exception as e:
            print(f"Ошибка при сохранении: {e}")

    def load_autosave(self):
        """Загружает автосохранение если есть"""
        autosave_data = load_autosave()
        if not autosave_data:
            print("Автосохранение не найдено")
            return
        
        # Восстанавливаем ТОЛЬКО данные проекта
        self.current_project_number = autosave_data.get('project_number')
        self.customer_name = autosave_data.get('customer_name', '')
        self.project_date = autosave_data.get('project_date', QDateTime.currentDateTime().toString('dd.MM.yyyy'))
        
        # Обновляем поля ввода
        self.le_customer.setText(self.customer_name)
        self.le_date.setText(self.project_date)
        
        # Восстанавливаем таблицу
        table_data = autosave_data.get('table_data', [])
        if table_data:
            self.table.setRowCount(len(table_data))
            for row, row_data in enumerate(table_data):
                for col, value in enumerate(row_data):
                    if col < self.table.columnCount():
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)
                        
                        # НЕМЕДЛЕННО применяем стиль с проверкой ошибок
                        if hasattr(self, 'table_manager') and self.table_manager:
                            self.table_manager._update_cell_style(item, value)
        
        self.update_window_title()
        print("Автосохранение загружено")
        

    def _autosave_current_state(self):
        """Сохраняет текущее состояние в автосохранение"""
        try:
            # Собираем актуальные данные таблицы
            table_data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else '')
                table_data.append(row_data)
            
            # Используем ФОРМАТ dd.MM.yyyy для даты проекта
            autosave_data = {
                'project_number': self.current_project_number,
                'customer_name': self.customer_name,
                'project_date': QDateTime.currentDateTime().toString('dd.MM.yyyy'),  # ПРАВИЛЬНЫЙ ФОРМАТ
                'last_modified': QDateTime.currentDateTime().toString('dd-MM-yyy HH:mm:ss'),
                'columns': self.columns,
                'table_data': table_data,
                'detail_types': self.detail_types,
                'is_autosave': True
            }
            
            save_autosave(autosave_data)
            
        except Exception as e:
            print(f"Ошибка при автосохранении: {e}")

    def update_group_lines(self):
        """Обновляет линии между группами"""
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    if item.data(Qt.UserRole) == "group_end":
                        # Принудительно обновляем стиль через таблицу
                        self.table.setProperty("group_end_row", row)
                    else:
                        self.table.setProperty("group_end_row", -1)
        
        # Перезагружаем стили
        self.table.style().unpolish(self.table)
        self.table.style().polish(self.table)







    def format_number(self, value):
        """Форматирует число убирая .0 если не нужно"""
        if not value.strip():
            return value
        
        try:
            num = float(value.replace(',', '.'))
            if num == int(num):
                return str(int(num))  # 1000.0 → "1000"
            else:
                return str(num)       # 950.5 → "950.5"
        except ValueError:
            return value

    # метод для ограничения разделителей 
    def _get_separator_limit_index(self, separator_type):
        """Возвращает индекс колонки, до которой доходит разделитель"""
        if separator_type == 'detail_type' and 'Тип детали' in self.columns:
            return self.columns.index('Тип детали')
        elif separator_type == 'paint' and 'Краска' in self.columns:
            return self.columns.index('Краска')
        return -1  # Если колонка не найдена, разделитель идет до конца

    def toggle_separators(self):
        """Включает/выключает отображение разделителей"""
        # Просто перерисовываем таблицу
        self.table.viewport().update()
        
        # Если есть отсортированные данные - перерисовываем с текущими настройками
        if hasattr(self, 'last_sorted_data'):
            self.sort_table()


    def sort_table(self):
        """Сортирует таблицу и добавляет разделители только для краски и типа фасада"""
        if not self.table.rowCount():
            self.show_status_message("Таблица пуста", 2000)
            return
        
        self.normalize_sizes()
        self.table_manager._save_current_state()
        
        try:
            # Получаем индексы колонок
            len_idx = self.columns.index('Длина') if 'Длина' in self.columns else -1
            wid_idx = self.columns.index('Ширина') if 'Ширина' in self.columns else -1
            thick_idx = self.columns.index('Толщина') if 'Толщина' in self.columns else -1
            detail_idx = self.columns.index('Тип детали') if 'Тип детали' in self.columns else -1
            paint_idx = self.columns.index('Краска') if 'Краска' in self.columns else -1
            sides_idx = self.columns.index('Сторон') if 'Сторон' in self.columns else -1
            qty_idx = self.columns.index('Кол-во') if 'Кол-во' in self.columns else -1
            
            if -1 in [len_idx, wid_idx, thick_idx, detail_idx, paint_idx, sides_idx, qty_idx]:
                self.show_status_message("Не все необходимые колонки присутствуют", 3000)
                return
            
            # Собираем данные
            rows_data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else '')
                rows_data.append(row_data)
            
            # Сортируем и получаем разделители только для краски и типа
            sorted_data, paint_seps, detail_seps, _, _ = self._sort_rows(
                rows_data, len_idx, wid_idx, thick_idx, detail_idx, paint_idx, sides_idx)
            
            # Обновляем таблицу
            self.table.blockSignals(True)
            self.table.setRowCount(len(sorted_data))
            
            # ОЧИСТКА ГРАНИЦ - ДОЛЖНА БЫТЬ ЗДЕСЬ, ПЕРЕД ЗАПОЛНЕНИЕМ ДАННЫХ
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setData(Qt.UserRole, "")  # Очищаем ВСЕ границы
            
            # Проверяем включены ли разделители
            show_separators = self.cb_show_separators.isChecked()

            # Определяем ограничивающие индексы для разделителей
            detail_limit_idx = self._get_separator_limit_index('detail_type')
            paint_limit_idx = self._get_separator_limit_index('paint')

            for row, row_data in enumerate(sorted_data):
                for col, value in enumerate(row_data):
                    if col < self.table.columnCount():
                        item = self.table.item(row, col)
                        formatted_value = self.format_number(value) if col in [len_idx, wid_idx, thick_idx, sides_idx] else value
                        
                        if not item:
                            item = QTableWidgetItem(formatted_value)
                            self.table.setItem(row, col, item)
                        else:
                            item.setText(formatted_value)
                        
                        self.table_manager._update_cell_style(item, formatted_value)
                        
                        if show_separators:
                            # Разделители для краски (только до колонки "Краска")
                            if row in paint_seps:
                                if paint_limit_idx == -1 or col <= paint_limit_idx:
                                    item.setData(Qt.UserRole, "bottom_border")
                            
                            # Разделители для типа (только до колонки "Тип детали")
                            elif row in detail_seps:
                                if detail_limit_idx == -1 or col <= detail_limit_idx:
                                    item.setData(Qt.UserRole, "bottom_border")

            self.table.blockSignals(False)
            self.show_status_message("Таблица упорядочена", 2000)
            
        except Exception as e:
            print(f"Ошибка при сортировке: {e}")
            self.show_status_message("Ошибка при сортировке", 3000)          
        
        # Принудительная перерисовка ВСЕЙ таблицы
        self.table.viewport().update()


    def _sort_rows(self, rows_data, len_idx, wid_idx, thick_idx, detail_idx, paint_idx, sides_idx):
        """Сортирует строки согласно новым требованиям: по количеству позиций, порядку типов, толщине и размеру"""
        
        def is_row_empty(row):
            return all(not cell.strip() for cell in row)
        
        def has_essential_data(row):
            return any(row[i].strip() for i in [len_idx, wid_idx, thick_idx, detail_idx, paint_idx, sides_idx])
        
        def get_max_size(row):
            """Возвращает максимальный размер из длины и ширины"""
            try:
                length = float(row[len_idx].replace(',', '.')) if len_idx < len(row) and row[len_idx].strip() else 0
                width = float(row[wid_idx].replace(',', '.')) if wid_idx < len(row) and row[wid_idx].strip() else 0
                return max(length, width)
            except:
                return 0
        
        # Фильтруем пустые строки
        non_empty_rows = [row for row in rows_data if has_essential_data(row)]
        
        # Группируем по краске
        paint_groups = {}
        for row in non_empty_rows:
            paint = row[paint_idx].strip().lower() if paint_idx != -1 and paint_idx < len(row) and row[paint_idx].strip() else 'без краски'
            
            if paint not in paint_groups:
                paint_groups[paint] = []
            paint_groups[paint].append(row)
        
        # Сортируем группы краски по количеству позиций (от меньшего к большему)
        sorted_paints = sorted(paint_groups.keys(), key=lambda x: len(paint_groups[x]))
        
        # Создаем новый отсортированный список
        new_sorted_data = []
        
        # Для каждой краски
        for paint in sorted_paints:
            paint_rows = paint_groups[paint]
            
            # Группируем по типу фасада внутри группы краски
            detail_groups = {}
            for row in paint_rows:
                detail_type = row[detail_idx].strip().lower() if detail_idx != -1 and detail_idx < len(row) and row[detail_idx].strip() else 'без типа'
                
                if detail_type not in detail_groups:
                    detail_groups[detail_type] = []
                detail_groups[detail_type].append(row)
            
            # Сортируем группы типа фасада согласно порядку в self.detail_types
            # Создаем порядок сортировки на основе self.detail_types
            detail_order = {detail.lower(): i for i, detail in enumerate(self.detail_types)}
            
            # Сортируем: сначала те, что есть в списке, затем остальные
            sorted_details = sorted(
                detail_groups.keys(),
                key=lambda x: detail_order.get(x, len(self.detail_types))  # Те, кого нет в списке, идут последними
            )
            
            # Для каждого типа фасада
            for detail_type in sorted_details:
                detail_rows = detail_groups[detail_type]
                
                # Группируем по толщине внутри группы типа фасада
                thickness_groups = {}
                for row in detail_rows:
                    try:
                        thickness_text = row[thick_idx].strip() if thick_idx != -1 and thick_idx < len(row) and row[thick_idx].strip() else '0'
                        thickness = float(thickness_text.replace(',', '.'))
                    except:
                        thickness = 0.0
                    
                    if thickness not in thickness_groups:
                        thickness_groups[thickness] = []
                    thickness_groups[thickness].append(row)
                
                # Сортируем группы толщины от меньшей к большей
                sorted_thicknesses = sorted(thickness_groups.keys())
                
                # Для каждой толщины
                for thickness in sorted_thicknesses:
                    thickness_rows = thickness_groups[thickness]
                    
                    # Сортируем по размеру (от большего к меньшему)
                    thickness_rows.sort(key=lambda row: -get_max_size(row))
                    
                    # Добавляем в итоговый список
                    new_sorted_data.extend(thickness_rows)
        
        # Добавляем пустые строки в конец
        for row in rows_data:
            if is_row_empty(row) or not has_essential_data(row):
                new_sorted_data.append(row)
        
        # Находим разделители для нового порядка
        paint_separators = set()
        detail_separators = set()
        
        previous_paint = None
        previous_detail = None
        
        for i, row in enumerate(new_sorted_data):
            if is_row_empty(row) or not has_essential_data(row):
                continue
                
            current_paint = row[paint_idx].strip().lower() if paint_idx != -1 and paint_idx < len(row) and row[paint_idx].strip() else ''
            current_detail = row[detail_idx].strip().lower() if detail_idx != -1 and detail_idx < len(row) and row[detail_idx].strip() else ''
            
            # Разделитель для краски
            if previous_paint is not None and current_paint != previous_paint:
                paint_separators.add(i - 1)
            
            # Разделитель для типа (только если краска не менялась)
            if (previous_paint is not None and current_paint == previous_paint and 
                previous_detail is not None and current_detail != previous_detail):
                detail_separators.add(i - 1)
            
            previous_paint = current_paint
            previous_detail = current_detail
        
        # Добавляем разделители после последних строк
        if len(new_sorted_data) > 0 and not is_row_empty(new_sorted_data[-1]) and has_essential_data(new_sorted_data[-1]):
            paint_separators.add(len(new_sorted_data) - 1)
            if previous_detail is not None:
                detail_separators.add(len(new_sorted_data) - 1)
        
        return new_sorted_data, paint_separators, detail_separators, set(), set()



    def get_table_separators(self):
        """Возвращает разделители таблицы для использования в печати"""
        if not self.table.rowCount():
            return [], [], [], []
        
        # Получаем индексы колонок
        len_idx = self.columns.index('Длина') if 'Длина' in self.columns else -1
        wid_idx = self.columns.index('Ширина') if 'Ширина' in self.columns else -1
        thick_idx = self.columns.index('Толщина') if 'Толщина' in self.columns else -1
        detail_idx = self.columns.index('Тип детали') if 'Тип детали' in self.columns else -1
        paint_idx = self.columns.index('Краска') if 'Краска' in self.columns else -1
        sides_idx = self.columns.index('Сторон') if 'Сторон' in self.columns else -1
        
        # Собираем данные
        table_data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else '')
            table_data.append(row_data)
        
        # Получаем разделители
        sorted_data, paint_seps, detail_seps, sides_seps, thick_seps = self._sort_rows(
            table_data, len_idx, wid_idx, thick_idx, detail_idx, paint_idx, sides_idx
        )
        
        return paint_seps, detail_seps, sides_seps, thick_seps

    def clear_all_borders(self):
        """Очищает все границы в таблице"""
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setData(Qt.UserRole, "")  # Очищаем стиль
        self.table.viewport().update()  # ← ДОБАВЬТЕ перерисовку


    def update_cell_style_with_separators(self, item, value, row):
        """Обновляет стиль ячейки с учетом разделителей"""
        if not item:
            return
            
        value = str(value).strip()
        item.setTextAlignment(Qt.AlignCenter)
        
        # Устанавливаем серый фон для разделителей
        if row in self.group_end_rows:
            item.setBackground(QColor(220, 220, 220))  # Серый фон
            return
        
        # Стандартная логика
        if value:
            item.setBackground(QColor('#fffbe6'))
        else:
            item.setBackground(Qt.white)





    def normalize_sizes(self):
        """Нормализует размеры - делает большее значение длиной, меньшее - шириной"""
        if not self.table.rowCount():
            return
        
        try:
            len_idx = self.columns.index('Длина') if 'Длина' in self.columns else -1
            wid_idx = self.columns.index('Ширина') if 'Ширина' in self.columns else -1
            
            if len_idx == -1 or wid_idx == -1:
                return
            
            self.table_manager._save_current_state()
            self.table.blockSignals(True)
            
            for row in range(self.table.rowCount()):
                len_item = self.table.item(row, len_idx)
                wid_item = self.table.item(row, wid_idx)
                
                if len_item and wid_item:
                    try:
                        length_val = len_item.text().replace(',', '.')
                        width_val = wid_item.text().replace(',', '.')
                        
                        if length_val and width_val:
                            length = float(length_val)
                            width = float(width_val)
                            
                            # Если ширина больше длины - меняем местами
                            if width > length:
                                # Форматируем числа правильно
                                len_item.setText(self.format_number(str(width)))
                                wid_item.setText(self.format_number(str(length)))
                                self.table_manager._update_cell_style(len_item, str(width))
                                self.table_manager._update_cell_style(wid_item, str(length))
                    except:
                        continue
            
            self.table.blockSignals(False)
            
        except Exception as e:
            print(f"Ошибка при нормализации размеров: {e}")





    def open_other_settings(self):
        from other_settings_dialog import OtherSettingsDialog
        dlg = OtherSettingsDialog(self)
        if dlg.exec_():
            self.show_status_message('Настройки сохранены', 2000)

    def update_calc_area(self, calculation_data):
        """Обновляет область расчета на основе данных из table_manager.calculate()"""
        
        # 1. Площадь деталей по типам + общая площадь выделенная
        details_text = ""
        total_area = calculation_data.get('total_area', 0)
        detail_type_areas = calculation_data.get('detail_type_areas', {})
        
        if total_area > 0:
            details_text += f"<b>ОБЩАЯ: {total_area:.2f} м²</b><br>"
        
        for detail_type, area in detail_type_areas.items():
            if area > 0:
                details_text += f"{detail_type}: {area:.2f} м²<br>"
        
        self.details_area.setText(details_text if details_text else "Нет данных")
        
        # 2. Прочее (замотка сверху, длины, ручки, планки, склейка)
        other_text = ""
        
        # ЗАМОТКА - ВПЕРЕД
        wrapping_cost = calculation_data.get('wrapping_cost', 0)
        if wrapping_cost > 0:
            other_text += f"Замотка: {wrapping_cost:.0f} ₽<br>"

        # ОБЩЕЕ КОЛИЧЕСТВО ДЕТАЛЕЙ
        total_pieces = calculation_data.get('total_pieces', 0)
        if total_pieces > 0:
            other_text += f"Деталей: {total_pieces} шт<br>"
        
        # ДЛИНА КРОМКИ
        total_edge_length = calculation_data.get('total_edge_length', 0)
        if total_edge_length > 0:
            other_text += f"Кромка: {total_edge_length:.2f} м<br>"
        
        # Планки
        total_plank_length = calculation_data.get('total_plank_length', 0)
        if total_plank_length > 0:
            other_text += f"Планки: {total_plank_length:.2f} м<br>"
        
        # Ручки
        total_handle_length = calculation_data.get('total_handle_length', 0)
        if total_handle_length > 0:
            other_text += f"Ручки: {total_handle_length:.2f} м<br>"
        
        # Склейка
        total_gluing_area = calculation_data.get('total_gluing_area', 0)
        if total_gluing_area > 0:
            other_text += f"Склейка: {total_gluing_area:.2f} м²<br>"

        self.other_area.setText(other_text if other_text else "Нет данных")
        
        # 3. Площадь покраски по типам - верхний правый
        painting_text = ""
        total_paint_area = calculation_data.get('total_paint_area', 0)
        detail_type_paint_areas = calculation_data.get('detail_type_paint_areas', {})
        
        if total_paint_area > 0:
            painting_text += f"<b>ОБЩАЯ: {total_paint_area:.2f} м²</b><br>"
        
        for detail_type, paint_area in detail_type_paint_areas.items():
            if paint_area > 0:
                painting_text += f"{detail_type}: {paint_area:.2f} м²<br>"
        
        self.painting_area.setText(painting_text if painting_text else "Нет данных")
        
        # 4. Расход краски по типам - нижний правый
        paint_text = ""
        paint_areas = calculation_data.get('paint_areas', {})
        
        for paint_type, area in paint_areas.items():
            if area > 0 and paint_type != 'Без краски':
                paint_kg = area * calculation_data.get('paint_consumption', 0.35)
                paint_text += f"{paint_type}: {paint_kg:.2f} кг<br>"
        
        self.paint_area.setText(paint_text if paint_text else "Нет данных")


    def update_window_title(self):
        title = f"Спецификация"
        if self.current_project_number:
            title += f" - №{self.current_project_number}"
        if self.customer_name:
            title += f" - {self.customer_name}"
        if self.is_modified:
            title += " *"  # Добавляем звездочку для измененных проектов
        self.setWindowTitle(title)
        self.le_project_number.setText(str(self.current_project_number) if self.current_project_number else "")

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
            
            # Удаляем старые ставки
            for work in self.work_types:
                old_key = f"{work}_{old_name}"
                if old_key in self.rates:
                    del self.rates[old_key]
            
            # Добавляем новые ставки
            self.rates.update(new_rates)
            
            # НЕМЕДЛЕННО сохраняем изменения
            save_facade_types(self.types)
            save_rates(self.rates)
            
            self.update_list()
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).text() == new_name:
                    self.list_widget.setCurrentRow(i)
                    break





    def open_work_types_dialog(self):
        # Загружаем свежие данные из конфига
        from work_types_config import load_work_types
        from file_operations import load_rates
        current_work_types = load_work_types()
        current_rates = load_rates()
        
        dlg = WorkTypesDialog(current_work_types, current_rates, self.detail_types, self)
        if dlg.exec_():
            # Обновляем данные в главном окне
            from work_types_config import load_work_types
            self.work_types = load_work_types()
            self.rates = load_rates()
            self.refresh_delegates()
            self.show_status_message('Типы работ обновлены', 2000)

    def open_rates_dialog(self):
        # Загружаем свежие данные из конфига
        from work_types_config import load_work_types
        from file_operations import load_rates
        current_work_types = load_work_types()
        current_rates = load_rates()
        
        dlg = RatesDialog(current_rates, lambda: current_work_types, lambda: self.detail_types, self)
        if dlg.exec_():
            # Загружаем свежие ставки и исполнителей один раз
            updated_rates = load_rates()
            updated_workers = load_workers()

            # Обновляем главный объект и калькулятор
            self.rates = updated_rates
            if hasattr(self, "print_manager"):
                self.print_manager.calculator.rates = updated_rates
                self.print_manager.calculator.workers = updated_workers

            self.refresh_delegates()
            self.show_status_message('Ставки обновлены', 2000)

    def open_structure_dialog(self):
        """
        Открывает диалог редактирования структуры таблицы.
        Любые изменения колонок сохраняются в конфиг сразу при добавлении/переименовании/удалении.
        После закрытия диалога обновляются колонки таблицы и данные.
        """
        from file_operations import load_columns_config, save_columns_config

        # Загружаем актуальные колонки из конфига
        current_columns = load_columns_config()

        # Открываем диалог структуры
        dlg = TableStructureDialog(current_columns, self)
        if dlg.exec_():
            # Получаем свежие колонки из диалога
            self.columns = dlg.get_columns()

            # Сохраняем обновленные колонки в конфиг сразу
            save_columns_config(self.columns)

            # Пересоздаем таблицу с новыми колонками
            self.table.setColumnCount(len(self.columns))
            self.table.setHorizontalHeaderLabels(self.columns)

            # Сохраняем текущие данные таблицы
            current_data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else '')
                current_data.append(row_data)

            # Восстанавливаем данные в таблице, обрезая лишние или добавляя пустые ячейки
            self.table.setRowCount(len(current_data))
            for row, row_data in enumerate(current_data):
                for col, value in enumerate(row_data):
                    if col < self.table.columnCount():
                        item = QTableWidgetItem(value)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)
                    else:
                        # Новые колонки пустые
                        item = QTableWidgetItem('')
                        item.setTextAlignment(Qt.AlignCenter)
                        self.table.setItem(row, col, item)

            # Обновляем делегат для типа детали (если используется)
            self.update_detail_type_delegate()

            self.show_status_message('Структура таблицы обновлена', 2000)



    def open_facade_types_dialog(self):
        dlg = FacadeTypesDialog(self.detail_types, self.rates, DEFAULT_WORK_TYPES, self)
        if dlg.exec_():
            new_detail_types, new_rates = dlg.get_types()
            self.detail_types = new_detail_types
            self.rates = new_rates
            self.update_detail_type_delegate()
            # Теперь данные уже сохранены в диалоге, не нужно сохранять здесь
            self.show_status_message('Типы фасадов обновлены', 2000)


    # В методе eventFilter заменяем вызовы:
    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and source is self.table:
            key = event.key()
            mods = event.modifiers()
            
            # Обработка навигационных клавиш
            if key in [Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right]:
                # Сохраняем текущую ячейку через table_manager
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.save_current_cell()
                
                # Для стрелки вниз проверяем, нужно ли добавить строки
                if key == Qt.Key_Down:
                    current_row = self.table.currentRow()
                    if current_row >= self.table.rowCount() - 3:
                        if hasattr(self, 'table_manager') and self.table_manager:
                            self.table_manager.add_more_rows()
                
                return False
                
            elif key == Qt.Key_Tab:
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.save_current_cell()
                    self.table_manager.handle_tab_press()
                return True
                
            elif key == Qt.Key_Backtab:  # Shift+Tab
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.save_current_cell()
                    self.table_manager.handle_shift_tab_press()
                return True
                
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                # ТОЛЬКО сохраняем ячейку, НЕ переходим дальше
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.save_current_cell()
                return True
                
            elif key == Qt.Key_Z and (mods & Qt.ControlModifier):
                if mods & Qt.ShiftModifier:
                    if hasattr(self, 'table_manager') and self.table_manager:
                        return self.table_manager.redo()
                else:
                    if hasattr(self, 'table_manager') and self.table_manager:
                        return self.table_manager.undo()
            elif key == Qt.Key_Y and (mods & Qt.ControlModifier):
                if hasattr(self, 'table_manager') and self.table_manager:
                    return self.table_manager.redo()
            elif key == Qt.Key_Delete:
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.clear_selected_cells()
                return True
            elif key == Qt.Key_C and (mods & Qt.ControlModifier):
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.copy_clip_value()
                return True
            elif key == Qt.Key_V and (mods & Qt.ControlModifier):
                if hasattr(self, 'table_manager') and self.table_manager:
                    self.table_manager.paste_clip_value()
                return True
                    
        # Обработка клика мыши
        elif event.type() == QEvent.MouseButtonPress and source is self.table:
            # Сохраняем текущую ячейку перед переходом на новую
            if hasattr(self, 'table_manager') and self.table_manager:
                self.table_manager.save_current_cell()
            return False
            
        return False


    def show_status_message(self, message, timeout=0):
        self.status_bar.showMessage(message, timeout)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            if event.modifiers() & Qt.ShiftModifier:
                self.table_manager.redo()
            else:
                self.table_manager.undo()
            event.accept()
        elif event.key() == Qt.Key_Y and (event.modifiers() & Qt.ControlModifier):
            self.table_manager.redo()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _handle_table_change(self, item):
        """Обработчик изменения ячейки таблицы"""
        # Убираем проверку на updating_style
        self.mark_as_modified()