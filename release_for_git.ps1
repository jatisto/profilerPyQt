$authFilePath = ".\auth.json"
$versionFilePath = ".\version.txt"
$fileToUpload = ".\dist\PgStatStatementsReaderQt5.exe"

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

# Проверка существования файла с версией
if (-not (Test-Path -Path $versionFilePath -PathType Leaf)) {
    Write-Host "File '$versionFilePath' not found."
    exit
}

$version = Get-Content -Raw -Path $versionFilePath

# Создание параметров релиза
$releaseTag = "v$version"
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

    # Создание релиза
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/$username/$repo/releases" -Method Post -Headers @{
        Authorization = "token $token"
    } -ContentType "application/json" -Body ($releaseParams | ConvertTo-Json)

    # Получение ID созданного релиза
    $releaseId = $release.id

    $uploadUrl = "https://uploads.github.com/repos/$username/$repo/releases/$releaseId/assets?name=PgStatStatementsReaderQt5.exe"

    # Загрузка файла в релиз
    $uploadResponse = Invoke-RestMethod -Uri $uploadUrl -Method Post -Headers @{
        Authorization = "token $token"
        "Content-Type" = "application/octet-stream"
    } -InFile $fileToUpload

    Write-Host "THE_FILE_WAS_SUCCESSFULLY_UPLOADED_TO_THE_RELEASE $releaseTag."
} catch {
    Write-Host "AN ERROR HAS OCCURRED: $_"
}
