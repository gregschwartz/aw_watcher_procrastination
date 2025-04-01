@echo off
setlocal enabledelayedexpansion

:: Set up paths
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"
set "VENV_DIR=%PROJECT_ROOT%\.venv"

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python isn't installed. Please install it first: https://www.python.org/downloads/
    exit /b 1
)

:: Check if ActivityWatch is running
curl -s http://localhost:5600 >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: ActivityWatch is not running. Please start ActivityWatch first. If it is not installed, see https://activitywatch.net/docs/installation/ If you're running it in a container, make sure to expose the port ^(e.g. -p 5600:5600^)
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to create virtual environment. Please check your Python installation.
        exit /b 1
    )
)

:: Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to activate virtual environment. Try deleting the .venv directory and running this script again.
    exit /b 1
)

:: Install requirements if they exist
if exist "%PROJECT_ROOT%\requirements.txt" (
    echo Installing dependencies...
    pip install -r "%PROJECT_ROOT%\requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo Error: Failed to install dependencies. Please check your internet connection and try again.
        exit /b 1
    )
)

:: Backup the existing settings file
if exist "%PROJECT_ROOT%\settings.json" (
    echo Backing up existing settings file...

    :: Keep 2 old backups
    if exist "%PROJECT_ROOT%\settings.backup.2.json" (
        move "%PROJECT_ROOT%\settings.backup.2.json" "%PROJECT_ROOT%\settings.backup.3.json"
    )
    if exist "%PROJECT_ROOT%\settings.backup.1.json" (
        move "%PROJECT_ROOT%\settings.backup.1.json" "%PROJECT_ROOT%\settings.backup.2.json"
    )

    copy "%PROJECT_ROOT%\settings.json" "%PROJECT_ROOT%\settings.backup.1.json"
) else (
    echo No settings file found, creating a new one...
    copy "%PROJECT_ROOT%\settings.example.json" "%PROJECT_ROOT%\settings.json"
)

:: TODO: check for updates

:: Run the application
python -m src.aw_watcher_procrastination.main
if %ERRORLEVEL% NEQ 0 (
    echo Error: Application exited with an error.
    exit /b 1
)

endlocal 