@echo off
REM ==============================================================================
REM Polylog - Portable Windows Launcher
REM ==============================================================================
REM This wrapper enables portable execution of Polylog.exe from any location
REM with proper error handling and argument forwarding.
REM
REM Usage:
REM   Double-click:           Launches GUI
REM   polylog-launcher.bat    Launches GUI
REM   polylog-launcher.bat --mode api --port 8080    Launches API server
REM   polylog-launcher.bat --help                      Shows help
REM ==============================================================================

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to the script directory to ensure Polylog.exe can find its dependencies
cd /d "%SCRIPT_DIR%"

REM Launch Polylog.exe with all passed arguments
REM If no arguments, defaults to GUI mode
if "%~1"=="" (
    REM No arguments: launch GUI (default)
    Polylog.exe
) else (
    REM Pass all arguments to Polylog.exe
    Polylog.exe %*
)

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM If error occurred and we're not in a terminal context, pause to show error
if %EXIT_CODE% neq 0 (
    if not defined PROMPT (
        echo.
        echo Error: Polylog exited with code %EXIT_CODE%
        pause
    )
    exit /b %EXIT_CODE%
)

exit /b 0
