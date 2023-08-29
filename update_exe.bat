@echo off

rem Путь к файлу update_exe.ps1
set "ps1_file_path=%~dp0update_exe.ps1"

rem Запуск PowerShell скрипта с правами администратора
powershell -ExecutionPolicy Bypass -File "%ps1_file_path%"
