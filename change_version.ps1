$authFilePath = ".\auth.json"
$versionFilePath = ".\version.txt"

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

# Чтение текущей версии из файла
$currentVersion = Get-Content -Raw -Path $versionFilePath

# Разбиение версии на компоненты
$versionComponents = $currentVersion -split '\.'
$major = [int]$versionComponents[0]
$minor = [int]$versionComponents[1]
$patch = [int]$versionComponents[2]

# Инкремент компонента версии
$patch += 1

# Создание новой версии
$newVersion = "$major.$minor.$patch"

# Запись новой версии обратно в файл
$newVersion | Set-Content -Path $versionFilePath

# Устанавливаем персональный токен для аутентификации
git config --global credential.helper "store --file=.git/credentials" # Это сохранит учетные данные в файл .git/credentials
git config --global credential.GitHub.com $token:x-oauth-basic

# Коммит измененного файла версии
try {
    git add $versionFilePath
    git commit -m "Update version to $newVersion"
} catch {
    Write-Host "Failed to commit version change: $_"
}