$LOG_FILE = "$env:TMP\log_tmp\tmp_bat_update_log.txt"
Try
{
    Write-Output "-----------------------------------------------------------------" >> $LOG_FILE

    Write-Output "Copying files from PgStatStatementsReaderQt5 to temporary folder" >> $LOG_FILE
    $TMP_UPDATE_FOLDER = Join-Path $env:TMP "tmp_update_folder"
    $TMP_INSTALL = Join-Path $env:TMP "tmp_install"

    # Проверка наличия папки tmp_install
    if (-not(Test-Path -Path $TMP_INSTALL))
    {
        Write-Output "Creating tmp_install folder" >> $LOG_FILE
        New-Item -ItemType Directory -Path $TMP_INSTALL
    }

    Copy-Item -Path "$env:ProgramFiles\PgStatStatementsReaderQt5\*" -Destination $TMP_INSTALL -Recurse -Force

    $processName = "PgStatStatementsReaderQt5.exe"

    $matchingProcesses = Get-Process | Where-Object { $_.Path -like "*$processName" }

    if ($matchingProcesses.Count -gt 0)
    {
        Write-Host "Найдено процессов: $( $matchingProcesses.Count )"
        foreach ($process in $matchingProcesses)
        {
            Write-Host "Закрытие процесса с ID $( $process.Id ), Имя: $( $process.Name ), Путь: $( $process.Path )"
            $process.Kill()
        }
    }
    else
    {
        Write-Host "Процессы с именем $processName не найдены."
    }

    $filesExist = Test-Path -Path "$TMP_UPDATE_FOLDER\profilerPyQt\profilerPyQt-main\build\*"

    if ($filesExist)
    {
        Write-Output "Replacing files" >> $LOG_FILE
        Copy-Item -Path "$TMP_UPDATE_FOLDER\profilerPyQt\profilerPyQt-main\build\*" -Destination "$env:ProgramFiles\PgStatStatementsReaderQt5\" -Recurse -Force
    }
    else
    {
        Write-Output "No files to copy" >> $LOG_FILE
    }

    Write-Output "Checking for successful file replacement" >> $LOG_FILE
    if ($LASTEXITCODE -eq 0)
    {
        Write-Output "Deleting temporary files" >> $LOG_FILE
        Remove-Item -Path $TMP_UPDATE_FOLDER -Recurse -Force
        Remove-Item -Path $TMP_INSTALL -Recurse -Force
    }
    else
    {
        Write-Output "Restoring files from temporary folder" >> $LOG_FILE
        Copy-Item -Path "$TMP_INSTALL\*" -Destination "$env:ProgramFiles\PgStatStatementsReaderQt5\" -Recurse -Force
        Write-Output "Deleting temporary files after recovery" >> $LOG_FILE
        Remove-Item -Path $TMP_INSTALL -Recurse -Force
        Remove-Item -Path $TMP_UPDATE_FOLDER -Recurse -Force
    }

    Write-Output "Running PgStatStatementsReaderQt5.exe" >> $LOG_FILE
    Start-Process -FilePath "$env:ProgramFiles\PgStatStatementsReaderQt5\PgStatStatementsReaderQt5.exe"

}
Catch
{
    Write-Output "Ошибка: $_" >> $LOG_FILE
    Write-Output "Ошибка: $_"
    # Дополнительная обработка ошибки
}