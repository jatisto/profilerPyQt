param(
    [string]$newVersion_py
)

# Теперь $newVersion содержит переданную версию, которую вы можете использовать в скрипте
Write-Host "Received new version: $newVersion_py"

$authFilePath = ".\auth.json"
$versionFilePath = ".\version.txt"
$fileToUpload = ".\dist\PgSSR.exe"

# Проверка существования файла с данными авторизации
if (-not (Test-Path -Path $authFilePath -PathType Leaf)) {
    Write-Host "File '$authFilePath' not found."
    exit
}

$authData = Get-Content -Raw -Path $authFilePath | ConvertFrom-Json

# Извлечение авторизационных данных
$username = $authData.Auth.username
$token = $authData.Auth.token
$repo = $authData.Auth.repo

# Создание новой версии
$newVersion = "$newVersion_py"

# Запись новой версии обратно в файл
$newVersion | Set-Content -Path $versionFilePath

# Устанавливаем персональный токен для аутентификации
git config --global credential.helper "store --file=.git/credentials" # Это сохранит учетные данные в файл .git/credentials
git config --global credential.GitHub.com $token:x-oauth-basic

# Коммит измененного файла версии
try {
    git add $versionFilePath
    git commit -m "Update version to $newVersion"
    # Пушим изменения, токен будет использован для аутентификации
    git push origin main
} catch {
    Write-Host "Failed to commit version change: $_"
}

# Создание параметров релиза
$releaseTag = "v$newVersion"
$releaseParams = @{
    tag_name = $releaseTag
    target_commitish = "main"
    name = $releaseTag
    body = "A NEW VERSION $version"
    draft = $false
    prerelease = $false
}

try {
     # Проверка существования файла для загрузки
    if (-not (Test-Path -Path $fileToUpload -PathType Leaf)) {
        Write-Host "File '$fileToUpload' not found."
        exit
    }

     Write-Host "https://api.github.com/repos/$username/$repo/releases"

    # Создание релиза
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$username/$repo/releases" -Method Post -Headers @{
        Authorization = "token $token"
    } -ContentType "application/json" -Body ($releaseParams | ConvertTo-Json)

    # Получение ID созданного релиза
    $releaseId = $release.id

    $uploadUrl = "https://uploads.github.com/repos/$username/$repo/releases/$releaseId/assets?name=PgSSR.exe"

    # Загрузка файла в релиз
    $uploadResponse = Invoke-RestMethod -Uri $uploadUrl -Method Post -Headers @{
        Authorization = "token $token"
        "Content-Type" = "application/octet-stream"
    } -InFile $fileToUpload

    Write-Host "THE_FILE_WAS_SUCCESSFULLY_UPLOADED_TO_THE_RELEASE $releaseTag."
} catch {
    Write-Host "AN ERROR HAS OCCURRED: $_"
    $errorMessage = "ERROR: $_"
    $errorMessage
    $Error[0]
}
