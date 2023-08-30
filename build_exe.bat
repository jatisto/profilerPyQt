@echo off
setlocal

rem Переменные
set installer_script=installer_script.iss
set dist_dir=dist

rem Запуск скрипта инсталлятора
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" %installer_script%

rem Удаление папки build
rem rmdir /s /q "build"

echo Successful!

endlocal
