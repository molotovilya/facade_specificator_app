# other_settings_dialog.py
from imports import *
from constants import *
from file_operations import load_other_settings, save_other_settings

class OtherSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Дополнительные настройки')
        self.resize(450, 350)  # Уменьшаем высоту, так как убрали группу
        
        # Загружаем текущие настройки
        self.settings = load_other_settings()
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Расход краски
        paint_group = QGroupBox('Настройка расхода краски')
        paint_layout = QVBoxLayout(paint_group)
        paint_layout.addWidget(QLabel('Расход краски (кг/м²):'))
        self.consumption_edit = QLineEdit(str(self.settings.get('paint_consumption', 0.35)))
        self.consumption_edit.setValidator(QDoubleValidator(0.1, 1.0, 3))
        paint_layout.addWidget(self.consumption_edit)
        layout.addWidget(paint_group)
        
        # Ставка за замотку
        wrap_group = QGroupBox('Настройка замотки')
        wrap_layout = QVBoxLayout(wrap_group)
        wrap_layout.addWidget(QLabel('Ставка за замотку (₽/м²):'))
        self.wrapping_edit = QLineEdit(str(self.settings.get('wrapping_rate', 120.0)))
        self.wrapping_edit.setValidator(QDoubleValidator(0, 1000, 2))
        wrap_layout.addWidget(self.wrapping_edit)
        layout.addWidget(wrap_group)
        
        # Ставка за склейку
        gluing_group = QGroupBox('Настройка склейки')
        gluing_layout = QVBoxLayout(gluing_group)
        gluing_layout.addWidget(QLabel('Ставка за склейку (₽/м² за склейку):'))
        self.gluing_rate_edit = QLineEdit(str(self.settings.get('gluing_rate', 30.0)))
        self.gluing_rate_edit.setValidator(QDoubleValidator(0, 1000, 2))
        gluing_layout.addWidget(self.gluing_rate_edit)
        layout.addWidget(gluing_group)
        
        # Ставка за ручку
        handle_group = QGroupBox('Настройка ручки')
        handle_layout = QVBoxLayout(handle_group)
        handle_layout.addWidget(QLabel('Ставка за ручку (₽/м):'))
        self.handle_rate_edit = QLineEdit(str(self.settings.get('handle_rate', 100.0)))
        self.handle_rate_edit.setValidator(QDoubleValidator(0, 1000, 2))
        handle_layout.addWidget(self.handle_rate_edit)
        layout.addWidget(handle_group)
        
        layout.addStretch()
        
        # Ставка за оклейку
        taping_group = QGroupBox('Настройка оклейки')
        taping_layout = QVBoxLayout(taping_group)
        taping_layout.addWidget(QLabel('Ставка за оклейку (₽/м² для одной стороны):'))
        self.taping_rate_edit = QLineEdit(str(self.settings.get('taping_rate', 50.0)))
        self.taping_rate_edit.setValidator(QDoubleValidator(0, 1000, 2))
        taping_layout.addWidget(self.taping_rate_edit)
        layout.addWidget(taping_group)  

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def save_settings(self):
        try:
            # Получаем значения из полей ввода
            new_settings = {
                'paint_consumption': float(self.consumption_edit.text().replace(',', '.')),
                'wrapping_rate': float(self.wrapping_edit.text().replace(',', '.')),
                'gluing_rate': float(self.gluing_rate_edit.text().replace(',', '.')),
                'handle_rate': float(self.handle_rate_edit.text().replace(',', '.')),
                'taping_rate': float(self.taping_rate_edit.text().replace(',', '.'))  # ← новая строка
            }
            
            # Проверяем валидность значений
            for key, value in new_settings.items():
                if value < 0:
                    raise ValueError(f"Значение {key} должно быть положительным")
            
            # Сохраняем настройки
            save_other_settings(new_settings)
            
            # Закрываем диалог
            self.accept()
            
        except ValueError as e:
            QMessageBox.warning(self, 'Ошибка', 'Введите корректные числовые значения')