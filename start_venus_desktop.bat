@echo off
REM Venus AutoFill Desktop System Launcher
REM Double-click this file to start the complete system

echo ========================================
echo VENUS AUTOFILL DESKTOP SYSTEM
echo ========================================
echo.
echo Starting system...
echo.

REM Change to the project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js and try again
    pause
    exit /b 1
)

REM Install desktop app dependencies if needed
if not exist "desktop-app\node_modules" (
    echo Installing desktop app dependencies...
    cd desktop-app
    npm install
    cd ..
)

REM Launch the system
echo Launching Venus AutoFill Desktop System...
python launch_desktop_system.py

echo.
echo System has been stopped.
pause