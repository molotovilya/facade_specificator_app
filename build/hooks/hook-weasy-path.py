# build/hooks/hook-weasy-path.py
import os
import sys

if getattr(sys, 'frozen', False):
    meipass = getattr(sys, '_MEIPASS', None)
    if meipass:
        weasy_bin = os.path.join(meipass, 'weasy_bin')
        if os.path.isdir(weasy_bin):
            os.environ['PATH'] = weasy_bin + os.pathsep + os.environ.get('PATH', '')
