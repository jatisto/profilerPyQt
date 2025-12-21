@echo off
REM PgSSR v2.0 - Quick Start Script
REM Automatic launcher with all dependencies

echo ========================================
echo   PgSSR v2.0 - PostgreSQL Monitor
echo ========================================
echo.

REM Check if virtual environment exists
if exist venv\Scripts\activate.bat (
    echo [OK] Virtual environment found
    call venv\Scripts\activate.bat
) else (
    echo [INFO] Virtual environment not found
    echo [INFO] Using global Python
)

REM Check if dependencies are installed
python -c "import PySide6" 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] Dependencies not installed!
    echo [INFO] Installing dependencies...
    python -m pip install -q PySide6 loguru psycopg[binary,pool] cryptography pydantic pydantic-settings qt-material keyring
    echo [OK] Dependencies installed
)

echo.
echo [INFO] Starting application...
echo.

REM Run application
python main.py

pause
