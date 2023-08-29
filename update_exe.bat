@echo off

set "LOG_FILE=%ProgramFiles%\PgStatStatementsReaderQt5\bat_update_log.txt"

echo Copying files from PgStatStatementsReaderQt5 to temporary folder >> %LOG_FILE%
set "TMP_UPDATE_FOLDER=%TMP%\tmp_update_folder"
set "TMP_INSTALL=%TMP%\tmp_install"

xcopy "%ProgramFiles%\PgStatStatementsReaderQt5\*" "%TMP_INSTALL%\" /E /C /Y

echo Closing PgStatStatementsReaderQt5.exe processes >> %LOG_FILE%
taskkill /F /IM "PgStatStatementsReaderQt5.exe"

echo Replacing files >> %LOG_FILE%
xcopy "%TMP_UPDATE_FOLDER%\profilerPyQt\profilerPyQt-main\build\PgStatStatementsReaderQt5\*" "%ProgramFiles%\PgStatStatementsReaderQt5\" /E /C /Y

echo Checking for successful file replacement >> %LOG_FILE%
if %ERRORLEVEL% EQU 0 (
    echo Deleting temporary files >> %LOG_FILE%
    rmdir /S /Q %TMP_UPDATE_FOLDER%
    rmdir /S /Q %TMP_INSTALL%
) else (
    echo Restoring files from temporary folder >> %LOG_FILE%
    xcopy "%TMP_INSTALL%\*" "%ProgramFiles%\PgStatStatementsReaderQt5\" /E /C /Y
    echo Deleting temporary files after recovery >> %LOG_FILE%
    rmdir /S /Q %TMP_INSTALL%
)

echo Running PgStatStatementsReaderQt5.exe >> %LOG_FILE%
start "" "%ProgramFiles%\PgStatStatementsReaderQt5\PgStatStatementsReaderQt5.exe"
