#!/bin/bash
set -e

# The script directory is where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
VENV_DIR="$PROJECT_ROOT/.venv"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
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

# Backup the existing settings file
if [ -f "$PROJECT_ROOT/settings.json" ]; then
    echo "Backing up existing settings file..."

    # Keep 2 old backups
    if [ -f "$PROJECT_ROOT/settings.backup.2.json" ]; then
        mv "$PROJECT_ROOT/settings.backup.2.json" "$PROJECT_ROOT/settings.backup.3.json"
    fi
    if [ -f "$PROJECT_ROOT/settings.backup.1.json" ]; then
        mv "$PROJECT_ROOT/settings.backup.1.json" "$PROJECT_ROOT/settings.backup.2.json"
    fi

    cp "$PROJECT_ROOT/settings.json" "$PROJECT_ROOT/settings.backup.1.json"
else
    echo "No settings file found, creating a new one..."
    cp "$PROJECT_ROOT/settings.example.json" "$PROJECT_ROOT/settings.json"
fi

# TODO: check for updates

# Run the application
python -m src.aw_watcher_procrastination.main

# Handle any errors
if [ $? -ne 0 ]; then
    echo "Error: Application exited with an error."
    exit 1
fi