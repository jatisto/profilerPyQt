@echo off
setlocal

REM Копирование файлов из PgStatStatementsReaderQt5 во временную папку
robocopy "%ProgramFiles%\PgStatStatementsReaderQt5" "tmp" /e /copyall /purge

REM Закрытие процессов PgStatStatementsReaderQt5.exe
taskkill /f /im PgStatStatementsReaderQt5.exe

REM Замена файлов
robocopy "build\PgStatStatementsReaderQt5" "%ProgramFiles%\PgStatStatementsReaderQt5" /e /copyall /purge

REM Проверка на успешную замену файлов
if %errorlevel%==0 (
    REM Удаление временных файлов
    rmdir /s /q tmp
    REM Удаление временной папки два уровня ниже
    rmdir /s /q "..\..\tmp_update_folder"
) else (
    REM Восстановление файлов из временной папки
    robocopy "tmp" "%ProgramFiles%\PgStatStatementsReaderQt5" /e /copyall /purge
    REM Удаление временных файлов
    rmdir /s /q tmp
)

endlocal
