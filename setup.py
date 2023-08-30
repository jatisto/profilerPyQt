import argparse
import os
import subprocess
from sys import platform
from cx_Freeze import setup, Executable
import Constants
from update_version import Updater

name_app = 'PgSSR'

# Создаем парсер аргументов
parser = argparse.ArgumentParser(description='Build script with version type')
parser.add_argument('--ver', dest='version_type', choices=['major', 'minor', 'patch'],
                    help='Version type to increment: major, minor, or patch')
args, remaining_argv = parser.parse_known_args()

# Если аргумент --ver не был передан, то установить по умолчанию "patch"
if not args.version_type:
    args.version_type = 'patch'

base = None

if platform == 'win32':
    base = "Win32GUI"

# Получить текущую версию
current_version = Updater.get_local_version()

# Разбить версию на компоненты
major, minor, patch = map(int, current_version.split('.'))

# Увеличить версию в соответствии с выбранным типом
if args.version_type == 'major':
    major += 1
    minor = 0
    patch = 0
elif args.version_type == 'minor':
    minor += 1
    patch = 0
else:
    patch += 1

# Собрать новую версию
new_version = f"{major}.{minor}.{patch}"

# Параметры для исполняемого файла
executables: list[Executable] = [
    Executable(
        "main.py",
        base=base,
        target_name=f"{name_app}.exe",
        icon='icons/icon.ico',
        copyright='Copyright © 2023 iam@eabdyushev@ru Eugene Abdyushev',
        shortcut_name=f"{name_app}",
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
    name=f"{name_app}",
    version=new_version,  # Используйте новую версию
    description=f"Интерфейс для работы с pg_stat_statements. v.{new_version}",
    author="Евгений Абдюшев",
    options=options,
    executables=executables
)

# Записать новую версию в файл build/version.txt
with open("build/version.txt", "w") as version_file:
    version_file.write(new_version)

# Creating an installation file
bat_file_path = os.path.join(os.path.dirname(__file__), "build_exe.bat")
subprocess.call(bat_file_path, shell=True)

# Passing a new version to a PowerShell script
ps1_file_path_version = os.path.join(os.path.dirname(__file__), "release_for_git.ps1")
subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", ps1_file_path_version, new_version],
               shell=True)
