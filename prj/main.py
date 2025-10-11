import ensure_dirs
import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt  # ← ДОБАВИТЬ
from main_window import MainWindow

def setup_weasy_bin():
    base_dir = os.path.dirname(os.path.abspath(sys.executable))
    bin_path = os.path.join(base_dir, 'bin')
    if os.path.isdir(bin_path):
        os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')

setup_weasy_bin()

if getattr(sys, 'frozen', False):
    import ctypes
    from pathlib import Path
    icon_path = Path(sys.executable).parent / 'icon.ico'
    if icon_path.exists():
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('SpecificationApp')


if __name__ == '__main__':
    # ← ТОЛЬКО ЭТИ 2 СТРОКИ ДЛЯ DPI
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    
    ensure_dirs.ensure_dirs()
    app = QApplication(sys.argv)
    window = MainWindow()   
    window.load_autosave()
    window.show()
    sys.exit(app.exec_())