@echo off
echo Building SmartFurnace...

:: Kill any running instances
taskkill /F /IM SmartFurnace*.exe 2>NUL

:: Wait a moment for processes to close
timeout /t 2 /nobreak >NUL

:: Get version from version.py
for /f "tokens=2 delims=''" %%a in ('findstr "VERSION" version.py') do set VERSION=%%a

:: Clean previous builds
rmdir /s /q build dist
del /f /q *.spec

:: Create executable with minimal options
pyinstaller --name="SmartFurnace-%VERSION%" ^
            --onefile ^
            --windowed ^
            --hidden-import schedule_window ^
            --hidden-import database ^
            --hidden-import custom_combobox ^
            --hidden-import constants ^
            --hidden-import styles ^
            --exclude-module jupyter_rfb ^
            --log-level ERROR ^
            Main.py

echo Build complete! Version: %VERSION%
pause 