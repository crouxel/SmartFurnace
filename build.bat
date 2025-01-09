@echo off
echo Building SmartFurnace...

:: Get version from version.py
for /f "tokens=2 delims=''" %%a in ('findstr "VERSION" version.py') do set VERSION=%%a

:: Clean previous builds
rmdir /s /q build dist
del /f /q *.spec

:: Create executable
pyinstaller --name="SmartFurnace-%VERSION%" ^
            --onefile ^
            --windowed ^
            --hidden-import schedule_window ^
            --hidden-import database ^
            --hidden-import custom_combobox ^
            --hidden-import constants ^
            --hidden-import styles ^
            --add-data "version.py;." ^
            Main.py

echo Build complete! Version: %VERSION%
pause 