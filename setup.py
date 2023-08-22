from sys import platform
from cx_Freeze import setup, Executable

from update_version import get_local_version

base = None

if platform == 'win32':
    base = "Win32GUI"

# Получите новую версию
new_version: str = get_local_version()

# Параметры для исполняемого файла
executables = [
    Executable(
        "main.py",
        base=base,
        target_name=f"PgProfilerQt5_{new_version}.exe",
        icon='icons/icon.ico',
        shortcut_name='PgProfilerQt5',
        shortcut_dir="ProgramMenuFolder"
    )]

# Список файлов для включения в сборку
include_files = [
    ("themes", "themes"),
    ("icons", "icons"),
    ("Constants.py", "Constants.py"),
    ("database.py", "database.py"),
    ("main.py", "main.py"),
    ("settings.py", "settings.py"),
    ("setup.py", "setup.py"),
    ("sql_highlighter.py", "sql_highlighter.py"),
    ("ui.py", "ui.py"),
    ("utility_function.py", "utility_function.py"),
    ("sql_highlighter.py", "sql_highlighter.py"),
    ("setup.cfg", "setup.cfg"),
    ("update_version.py", "update_version.py"),
    ("version.txt", "version.txt"),
    ("update_version.py", "update_version.py"),
]

# Параметры для создания установщика
options = {
    "build_exe": {
        "include_files": include_files,
        "packages": ["os"],
    },
}

setup(
    name="PgProfilerQt5",
    version=new_version,  # Используйте новую версию
    description="Profiler for PG",
    options=options,
    executables=executables
)
