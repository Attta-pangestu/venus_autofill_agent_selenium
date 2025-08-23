@echo off
echo ========================================
echo Venus AutoFill Desktop - Installation
echo ========================================
echo.

:: Check if Node.js is installed
echo Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed!
    echo.
    echo Please install Node.js first:
    echo 1. Go to https://nodejs.org/
    echo 2. Download and install the LTS version
    echo 3. Restart this script after installation
    echo.
    pause
    exit /b 1
)

echo ✓ Node.js is installed
node --version
echo.

:: Check npm
echo Checking npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: npm is not available
    echo Please reinstall Node.js
    pause
    exit /b 1
)

echo ✓ npm is available
npm --version
echo.

:: Install dependencies
echo Installing application dependencies...
echo This may take several minutes depending on your internet connection...
echo.

npm install
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure your Flask backend server is running
echo 2. Run 'start.bat' to launch the desktop application
echo 3. Or use 'npm start' command
echo.
echo Default Flask server URL: http://localhost:5000
echo You can change this in the application settings
echo.
echo ========================================
echo.
pause