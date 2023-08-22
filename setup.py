from sys import platform
from cx_Freeze import setup, Executable

# Определите начальную версию вашего приложения
initial_version = "1.1"

base = None


# Автоматически увеличивайте версию на единицу
def increment_version(version):
    major, minor = version.split(".")
    new_version_increment = f"{major}.{int(minor) + 1}"
    return new_version_increment


if platform == 'win32':
    base = "Win32GUI"

# Получите текущую версию
current_version: str = initial_version

# Получите новую версию
new_version: str = increment_version(current_version)

# Параметры для исполняемого файла
executables: list[Executable] = [
    Executable(
        "main.py",
        base=base,
        target_name=f"PgProfilerQt5_{new_version}.exe",
        icon='icons/icon.ico',
        shortcut_name='PgProfilerQt5',
        shortcut_dir="ProgramMenuFolder"
    )]

# Список файлов для включения в сборку
include_files: list[tuple[str, str]] = [
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
    ("sql_highlighter.py", "sql_highlighter.py")
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
