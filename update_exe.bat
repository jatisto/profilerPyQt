@echo off
setlocal

REM Копирование файлов из PgStatStatementsReaderQt5 во временную папку
mkdir tmp
xcopy /s /y "%ProgramFiles%\PgStatStatementsReaderQt5\*" "tmp\"

REM Закрытие процессов PgStatStatementsReaderQt5.exe
taskkill /f /im PgStatStatementsReaderQt5.exe

REM Замена файлов
xcopy /s /y "build\PgStatStatementsReaderQt5\*" "%ProgramFiles%\PgStatStatementsReaderQt5\"

REM Проверка на успешную замену файлов
if %errorlevel%==0 (
    REM Удаление временных файлов
    rmdir /s /q tmp
    REM Удаление временной папки два уровня ниже
    rmdir /s /q "..\..\tmp_update_folder"
) else (
    REM Восстановление файлов из временной папки
    xcopy /s /y "tmp\*" "%ProgramFiles%\PgStatStatementsReaderQt5\"
    REM Удаление временных файлов
    rmdir /s /q tmp
)

endlocal
