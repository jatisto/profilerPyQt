import os
import subprocess
from sys import platform
from cx_Freeze import setup, Executable

import Constants
from update_version import Updater

base = None

if platform == 'win32':
    base = "Win32GUI"

# Получите новую версию
new_version: str = Updater.get_local_version()

# Параметры для исполняемого файла
executables: list[Executable] = [
    Executable(
        "main.py",
        base=base,
        target_name=f"PgSSR.exe",
        icon='icons/icon.ico',
        shortcut_name='PgSSR',
        shortcut_dir="ProgramMenuFolder",
        uac_admin=True
    )]

# Список файлов для включения в сборку
include_files = Constants.list_include()

# Параметры для создания установщика
options = {
    "build_exe": {
        "include_files": include_files,
        "packages": ["os"],
        "build_exe": "build"  # Замените "build_folder_name" на желаемое название папки
    },
}

setup(
    name="PgSSR",
    version=new_version,  # Используйте новую версию
    description=f"Интерфейс для работы с pg_stat_statements. v.{new_version}",
    options=options,
    executables=executables
)

# Путь к файлу update_exe.ps1
ps1_file_path = os.path.join(os.path.dirname(__file__), "update_exe.ps1")

# Запуск PowerShell скрипта с правами администратора и скрытым окном
subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", ps1_file_path], shell=True)
