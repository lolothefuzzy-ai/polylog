@echo off
REM Polylog6 Desktop Launcher for Windows
REM Single command to launch the complete desktop application

echo ========================================
echo Polylog6 Desktop Application Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Run the unified launcher
python scripts\unified_launcher.py desktop

if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch desktop application
    echo.
    echo Troubleshooting:
    echo 1. Run: python scripts\unified_launcher.py install
    echo 2. Check that all dependencies are installed
    echo 3. Verify API server can start
    pause
    exit /b 1
)

pause

