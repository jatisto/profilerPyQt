$LOG_FILE = "$env:ProgramFiles\PgStatStatementsReaderQt5\bat_update_log.txt"

Write-Output "Copying files from PgStatStatementsReaderQt5 to temporary folder" >> $LOG_FILE
$TMP_UPDATE_FOLDER = Join-Path $env:TMP "tmp_update_folder"
$TMP_INSTALL = Join-Path $env:TMP "tmp_install"

Copy-Item -Path "$env:ProgramFiles\PgStatStatementsReaderQt5\*" -Destination $TMP_INSTALL -Recurse -Force

Write-Output "Closing PgStatStatementsReaderQt5.exe processes" >> $LOG_FILE
Get-Process -Name "PgStatStatementsReaderQt5" | ForEach-Object {
    $_.CloseMainWindow()
    $_.WaitForExit()
    if (!$_.HasExited) {
        $_ | Stop-Process -Force
    }
}

Write-Output "Replacing files" >> $LOG_FILE
Copy-Item -Path "$TMP_UPDATE_FOLDER\profilerPyQt\profilerPyQt-main\build\PgStatStatementsReaderQt5\*" -Destination "$env:ProgramFiles\PgStatStatementsReaderQt5\" -Recurse -Force

Write-Output "Checking for successful file replacement" >> $LOG_FILE
if ($LASTEXITCODE -eq 0) {
    Write-Output "Deleting temporary files" >> $LOG_FILE
    Remove-Item -Path $TMP_UPDATE_FOLDER -Recurse -Force
    Remove-Item -Path $TMP_INSTALL -Recurse -Force
} else {
    Write-Output "Restoring files from temporary folder" >> $LOG_FILE
    Copy-Item -Path "$TMP_INSTALL\*" -Destination "$env:ProgramFiles\PgStatStatementsReaderQt5\" -Recurse -Force
    Write-Output "Deleting temporary files" >> $LOG_FILE
    Remove-Item -Path $TMP_INSTALL -Recurse -Force
}

Write-Output "Running PgStatStatementsReaderQt5.exe" >> $LOG_FILE
Start-Process -FilePath "$env:ProgramFiles\PgStatStatementsReaderQt5\PgStatStatementsReaderQt5.exe"

