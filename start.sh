#!/bin/bash
set -e

# The script directory is where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_DIR="$PROJECT_ROOT/.venv"

# Helpers
command_exists() {
    command -v "$1" >/dev/null 2>&1
}


# Check if Python 3 is installed
if ! command_exists python3; then
    echo "Error: Python 3 isn't installed. Please install it first: https://www.python.org/downloads/"
    exit 1
fi


# Check if ActivityWatch is running
if ! curl -s http://localhost:5600 &> /dev/null; then
    echo "Error: ActivityWatch is not running. Please start ActivityWatch first. If it is not installed, see https://activitywatch.net/docs/installation/ If you're running it in a container, make sure to expose the port (e.g. -p 5600:5600)"
    exit 1
fi


# Create and setup virtual environment if needed
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install requirements if they exist
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies. Please check your internet connection and try again."
        exit 1
    fi
fi


# TODO: check for updates
# git pull --force


# Backup the existing settings file
if [ -f "$PROJECT_ROOT/settings.json" ] && ! diff "$PROJECT_ROOT/settings.json" "$PROJECT_ROOT/settings.backup.1.json" > /dev/null 2>&1; then
    echo "Backing up existing settings file..."

    # Keep 2 old backups
    if [ -f "$PROJECT_ROOT/settings.backup.2.json" ]; then
        mv "$PROJECT_ROOT/settings.backup.2.json" "$PROJECT_ROOT/settings.backup.3.json"
    fi
    if [ -f "$PROJECT_ROOT/settings.backup.1.json" ]; then
        mv "$PROJECT_ROOT/settings.backup.1.json" "$PROJECT_ROOT/settings.backup.2.json"
    fi

    cp "$PROJECT_ROOT/settings.json" "$PROJECT_ROOT/settings.backup.1.json"
elif [ ! -f "$PROJECT_ROOT/settings.json" ]; then
    echo "No settings file found, creating a new one..."
    cp "$PROJECT_ROOT/settings.example.json" "$PROJECT_ROOT/settings.json"
fi


# Check and install Qt dependencies based on platform
# if [[ "$(uname)" == "Darwin" ]]; then
#     if ! command_exists brew; then
#         echo "Homebrew not found. Please install Homebrew first: https://brew.sh"
#         exit 1
#     fi

#     # Check if Qt is installed via brew
#     if ! brew list qt@6 &>/dev/null; then
#         echo "Qt6 not found. Installing via Homebrew..."
#         brew install qt@6
#         if [ $? -ne 0 ]; then
#             echo "Error installing Qt6. Please try installing manually: brew install qt@6"
#             exit 1
#         fi
#     fi
# elif [[ "$(uname)" == "Linux" ]]; then
#     if ! command_exists apt-get; then
#         echo "This script currently only supports Debian/Ubuntu-based Linux distributions. You would usually do this with sudo apt-get install qt6-webengine-dev but your system is not using apt-get. So please install qt6-webengine-dev manually."
#         exit 1
#     fi
    
#     # check if Qt WebEngine is installed on Linux
#     if ! dpkg -l | grep -q "qt6-webengine-dev"; then
#         echo "Qt6 WebEngine not found. Installing via apt..."
#         sudo apt-get update
#         sudo apt-get install -y qt6-webengine-dev
#         if [ $? -ne 0 ]; then
#             echo "Error installing Qt6 WebEngine. Please try installing manually: sudo apt-get install qt6-webengine-dev"
#             exit 1
#         fi
#     fi
# else
#     echo "Unsupported operating system"
#     exit 1
# fi


# Run the application
python -m src.aw_watcher_procrastination.main

# Handle any errors
if [ $? -ne 0 ]; then
    echo "Error: Application exited with an error."
    exit 1
fi