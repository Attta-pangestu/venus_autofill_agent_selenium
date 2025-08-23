@echo off
echo ========================================
echo Venus AutoFill Desktop Application
echo ========================================
echo.

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Node.js version:
node --version
echo.

:: Check if package.json exists
if not exist "package.json" (
    echo ERROR: package.json not found
    echo Please make sure you're in the correct directory
    pause
    exit /b 1
)

:: Check if node_modules exists, if not install dependencies
if not exist "node_modules" (
    echo Installing dependencies...
    echo This may take a few minutes...
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed successfully!
    echo.
)

:: Start the application
echo Starting Venus AutoFill Desktop Application...
echo.
echo Note: Make sure the Flask backend server is running
echo Default Flask server: http://localhost:5000
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

npm start

echo.
echo Application closed.
pause