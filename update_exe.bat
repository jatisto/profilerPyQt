@echo off
:: BatchGotAdmin
:-------------------------------------
REM  --> Check for permissions
    IF "%PROCESSOR_ARCHITECTURE%" EQU "amd64" (
>nul 2>&1 "%SYSTEMROOT%\SysWOW64\cacls.exe" "%SYSTEMROOT%\SysWOW64\config\system"
    ) ELSE (
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
    )

REM --> If error flag set, we do not have admin.
    if '%errorlevel%' NEQ '0' (
        echo Requesting administrative privileges...
        goto UACPrompt
    ) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"

    "%temp%\getadmin.vbs"
    del "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    pushd "%CD%"
    CD /D "%~dp0"
:--------------------------------------

:: Your original script goes here
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
