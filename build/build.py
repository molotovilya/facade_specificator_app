# build/build.py
import os
import shutil
from PyInstaller.__main__ import run

def main():
    build_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(build_dir)
    app_dir = os.path.join(project_dir, 'App')
    save_src_dir = os.path.join(project_dir, 'save')
    weasy_bin_src = os.path.join(build_dir, 'weasy_bin')  # твои бинарники weasy

    # Очищаем App
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)
    os.makedirs(app_dir, exist_ok=True)

    main_py_path = os.path.join(project_dir, 'prj', 'main.py')
    icon_path = os.path.join(build_dir, 'icon.ico')

    opts = [
        main_py_path,
        '--name=specific',
        '--onefile',
        '--windowed',
        '--icon=' + icon_path if os.path.exists(icon_path) else '',
        '--distpath=' + app_dir,
        '--workpath=' + os.path.join(project_dir, 'build_temp'),
        '--noconsole',
        '--add-data', f'{os.path.join(project_dir, "prj")}{os.pathsep}prj',
        '--hidden-import=PyQt5.QtPrintSupport',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=json',
        '--hidden-import=re',
        '--hidden-import=os',
        '--hidden-import=sys',
        '--hidden-import=pathlib',
        '--hidden-import=weasyprint',
        '--hidden-import=cairocffi',
        '--hidden-import=cffi',
        '--hidden-import=tinycss2',
        '--hidden-import=cssselect2',
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=matplotlib',
        '--exclude-module=pandas'
    ]

    opts = [o for o in opts if o]

    print("🚀 Собираю проект...")
    print(f"Корневая папка проекта: {project_dir}")
    print(f"Целевая папка: {app_dir}")

    try:
        run(opts)
        print("✅ Сборка завершена успешно!")

        # Копируем save
        save_dst_dir = os.path.join(app_dir, 'save')
        if os.path.exists(save_src_dir):
            shutil.copytree(save_src_dir, save_dst_dir)
            print("✅ Папка save скопирована в App")

        # Копируем weasy_bin внутрь App/bin
        if os.path.exists(weasy_bin_src):
            weasy_dst_dir = os.path.join(app_dir, 'bin')
            shutil.copytree(weasy_bin_src, weasy_dst_dir)
            print("✅ Папка weasy_bin скопирована в App/bin")
        else:
            print("⚠️ Папка build/weasy_bin не найдена — WeasyPrint может не работать в собранном exe.")

        # Удаляем временные папки
        build_temp_dir = os.path.join(project_dir, 'build_temp')
        if os.path.exists(build_temp_dir):
            shutil.rmtree(build_temp_dir)
            print("✅ Временная папка сборки удалена")
        
        spec_file = os.path.join(project_dir, 'specific.spec')
        if os.path.exists(spec_file):
            os.remove(spec_file)
            print("✅ Файл .spec удален")

        print("\n📦 Сборка готова!")
        print(f"📁 Исполняемый файл: {os.path.join(app_dir, 'specific.exe')}")
        print(f"📁 Папка с конфигами: {save_dst_dir}")
        print(f"📁 Папка с бинарниками: {weasy_dst_dir}")
        print("➡️ Запустите 'specific.exe' из папки App")

    except Exception as e:
        print(f"❌ Ошибка сборки: {e}")
        import traceback
        traceback.print_exc()

        build_temp_dir = os.path.join(project_dir, 'build_temp')
        if os.path.exists(build_temp_dir):
            shutil.rmtree(build_temp_dir)
        spec_file = os.path.join(project_dir, 'specific.spec')
        if os.path.exists(spec_file):
            os.remove(spec_file)

    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
