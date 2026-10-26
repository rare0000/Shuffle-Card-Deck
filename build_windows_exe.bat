@echo off
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :error
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "Shuffle Card Deck" app.py
if errorlevel 1 goto :error
echo.
echo Build complete! Find your Windows executable in the dist folder.
pause
exit /b 0
:error
echo.
echo Build failed. Check that Python and pip are installed.
pause
exit /b 1
