@echo off
setlocal

set "LOG_FILE=%ProgramFiles%\PgStatStatementsReaderQt5\bat_update_log.txt"

echo Copying files from PgStatStatementsReaderQt5 to temporary folder >> %LOG_FILE%
mkdir %TMP%\tmp_update_folder
xcopy /s /y "%ProgramFiles%\PgStatStatementsReaderQt5\*" "%TMP%\tmp_install\"

echo Closing PgStatStatementsReaderQt5.exe processes >> %LOG_FILE%
taskkill /f /im PgStatStatementsReaderQt5.exe

echo Replacing files >> %LOG_FILE%
xcopy /s /y "%TMP%\tmp_update_folder\profilerPyQt\profilerPyQt-main\build\PgStatStatementsReaderQt5\*" "%ProgramFiles%\PgStatStatementsReaderQt5\"

echo Checking for successful file replacement >> %LOG_FILE%
if %error level%==0 (
    echo Deleting temporary files >> %LOG_FILE%
    rmdir /s /q %TMP%\tmp_update_folder
    rmdir /s /q %TMP%\tmp_install
) else (
    echo Restoring files from temporary folder >> %LOG_FILE%
    xcopy /s /y "%TMP%\tmp_update_folder\*" "%ProgramFiles%\PgStatStatementsReaderQt5\"
    echo Deleting temporary files >> %LOG_FILE%
    rmdir /s /q %TMP%\tmp_update_folder
)

echo Running PgStatStatementsReaderQt5.exe >> %LOG_FILE%
start "" "%ProgramFiles%\PgStatStatementsReaderQt5\PgStatStatementsReaderQt5.exe"

endlocal
