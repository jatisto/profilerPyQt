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
        target_name=f"PgStatStatementsReaderQt5.exe",
        icon='icons/icon.ico',
        shortcut_name='PgStatStatementsReaderQt5',
        shortcut_dir="ProgramMenuFolder"
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
    name="PgStatStatementsReaderQt5",
    version=new_version,  # Используйте новую версию
    description=f"Интерфейс для работы с pg_stat_statements. v.{new_version}",
    author="Eugene Abdyushev",
    options=options,
    executables=executables
)

# Creating an installation file
bat_file_path = os.path.join(os.path.dirname(__file__), "build_exe.bat")
subprocess.call(bat_file_path, shell=True)

# Release
ps1_file_path = os.path.join(os.path.dirname(__file__), "release_for_git.ps1")
subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", ps1_file_path],
               shell=True)
