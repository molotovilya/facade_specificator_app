import sys
import json
import re
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QDialog, QHeaderView, QStatusBar,
    QComboBox, QStyledItemDelegate, QMessageBox, QInputDialog, QListWidget,
    QListWidgetItem, QFrame, QLineEdit, QDialogButtonBox, QAbstractItemView, QLabel,
    QFileDialog, QMenu, QAction, QGroupBox, QGridLayout  # <-- Добавь QGridLayout
)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QDialog, QHeaderView, QStatusBar,
    QComboBox, QStyledItemDelegate, QMessageBox, QInputDialog, QListWidget,
    QListWidgetItem, QFrame, QLineEdit, QDialogButtonBox, QAbstractItemView, QLabel,
    QFileDialog, QMenu, QAction, QGroupBox, QGridLayout, QCheckBox  # ← ДОБАВЬ QCheckBox
)

from PyQt5.QtCore import Qt, QTimer, QEvent, pyqtSignal, QDateTime
from PyQt5.QtGui import QColor, QIcon, QDoubleValidator, QIntValidator  # ← ДОБАВИТЬ QIntValidator