@echo off
setlocal

echo Copying files from PgStatStatementsReaderQt5 to temporary folder
mkdir tmp
xcopy /s /y "%ProgramFiles%\PgStatStatementsReaderQt5\*" "tmp\"

echo Closing PgStatStatementsReaderQt5.exe processes
taskkill /f /im PgStatStatementsReaderQt5.exe

echo Replacing files
xcopy /s /y "build\PgStatStatementsReaderQt5\*" "%ProgramFiles%\PgStatStatementsReaderQt5\"

echo Checking for successful file replacement
if %errorlevel%==0 (
    echo Deleting temporary files
    rmdir /s /q tmp
    echo Deleting temporary folder two levels up
    rmdir /s /q "..\..\tmp_update_folder"
) else (
    echo Restoring files from temporary folder
    xcopy /s /y "tmp\*" "%ProgramFiles%\PgStatStatementsReaderQt5\"
    echo Deleting temporary files
    rmdir /s /q tmp
)

endlocal
