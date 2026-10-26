@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo Couldn't start the application. Install Python 3.10 or newer,
    echo and enable "Add python.exe to PATH" during installation.
    pause
)
