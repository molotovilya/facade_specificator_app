from imports import *
from PyQt5.QtGui import QPen  # ← ДОБАВЬТЕ ЭТОТ ИМПОРТ
from PyQt5.QtCore import Qt

class ComboDelegate(QStyledItemDelegate):
    def __init__(self, items_getter, parent=None):
        super().__init__(parent)
        self.items_getter = items_getter

    def paint(self, painter, option, index):
            # Сначала стандартная отрисовка
            super().paint(painter, option, index)
            
            # Затем рисуем границу если нужно
            border_style = index.data(Qt.UserRole)
            if border_style == "bottom_border":
                painter.save()
                pen = QPen(Qt.darkGray, 3)
                painter.setPen(pen)
                rect = option.rect
                painter.drawLine(rect.bottomLeft(), rect.bottomRight())
                painter.restore()

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items_getter())
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value:
            idx = editor.findText(value)
            if idx >= 0:
                editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)