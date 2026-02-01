@echo off
setlocal EnableDelayedExpansion

REM Move to script folder
cd /d "%~dp0"
if not exist "main.py" (
    echo [ERROR] main.py not found. Run this from project folder.
    echo Path: %CD%
    goto :END
)

echo ========================================
echo 33m2 Crawler - EXE Build
echo ========================================
echo.
echo Folder: %CD%
echo.

REM Check venv and PyInstaller
set "PYI=venv\Scripts\pyinstaller.exe"
if not exist "%PYI%" (
    echo [ERROR] venv or PyInstaller not found.
    echo Run in CMD:
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo   pip install pyinstaller
    echo.
    goto :END
)

REM Clean
echo Cleaning dist and build...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Icon
if not exist "assets\icon.ico" (
    echo Creating icon...
    if exist "venv\Scripts\python.exe" (
        venv\Scripts\pip install pillow -q 2>nul
        venv\Scripts\python.exe create_icon.py 2>nul
    )
)

REM Check spec
if not exist "build.spec" (
    echo [ERROR] build.spec not found.
    goto :END
)

REM Build
echo.
echo Building... may take 2-5 min.
echo.
call "%PYI%" build.spec --noconfirm

echo.
set "EXEOUT="
for %%F in (dist\*.exe) do set "EXEOUT=%%F"
if defined EXEOUT (
    echo ========================================
    echo   BUILD OK: dist\*.exe
    echo ========================================
) else (
    echo ========================================
    echo   BUILD FAILED - check build folder
    echo ========================================
)

:END
echo.
pause
