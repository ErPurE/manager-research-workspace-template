@echo off
setlocal

cd /d "%~dp0"

echo.
echo ========================================
echo    Manager Dashboard
echo ========================================
echo.

rem Check Python.
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found.
    echo Please install Python 3.x: https://www.python.org/downloads/
    pause
    exit /b 1
)

rem Check Flask dependencies.
python -c "import flask, flask_cors" >nul 2>&1
if errorlevel 1 (
    echo Installing Flask dependencies...
    python -m pip install flask flask-cors
    if errorlevel 1 (
        echo ERROR: Failed to install Flask dependencies.
        pause
        exit /b 1
    )
)

echo Starting server...
echo.
echo URL: http://127.0.0.1:5000
echo Press Ctrl+C to stop the server.
echo.

start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process 'http://127.0.0.1:5000'"
python server.py

endlocal
