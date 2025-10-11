# border_delegate.py
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPen, QPainter
from constants import SEPARATOR_WIDTH, SEPARATOR_COLOR, SEPARATOR_STYLE  # ← ДОБАВИТЬ ИМПОРТ

class BorderDelegate(QStyledItemDelegate):
    def __init__(self, parent_delegate=None):
        super().__init__()
        self.parent_delegate = parent_delegate

    def paint(self, painter, option, index):
        # Сначала вызываем родительский делегат
        if self.parent_delegate:
            self.parent_delegate.paint(painter, option, index)
        else:
            super().paint(painter, option, index)
        
        # Проверяем включены ли разделители
        main_window = self.get_main_window()
        if main_window and hasattr(main_window, 'cb_show_separators'):
            if not main_window.cb_show_separators.isChecked():
                return
        
        # Рисуем границу поверх всего
        border_style = index.data(Qt.UserRole)
        if border_style == "bottom_border":
            painter.save()
            # ИСПОЛЬЗУЕМ КОНСТАНТЫ вместо жестких значений ↓
            pen = QPen(SEPARATOR_COLOR, SEPARATOR_WIDTH)
            painter.setPen(pen)
            rect = option.rect
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
            painter.restore()
    
    def get_main_window(self):
        """Находит главное окно через цепочку parent()"""
        widget = self.parent()
        while widget:
            if hasattr(widget, 'isWindow') and widget.isWindow():
                return widget
            widget = widget.parent()
        return None

    # ВАЖНО: Добавляем методы для создания редактора комбо-бокса
    def createEditor(self, parent, option, index):
        if self.parent_delegate:
            return self.parent_delegate.createEditor(parent, option, index)
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if self.parent_delegate:
            self.parent_delegate.setEditorData(editor, index)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if self.parent_delegate:
            self.parent_delegate.setModelData(editor, model, index)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        if self.parent_delegate:
            self.parent_delegate.updateEditorGeometry(editor, option, index)
        else:
            super().updateEditorGeometry(editor, option, index)