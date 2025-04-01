"""Settings management functionality."""

import json
import os
from typing import Dict, Any

DEFAULT_SETTINGS = {
    "bucket_ids_to_skip": [
        "aw-watcher-afk_",
        "aw-watcher-input_"
    ],
    "procrastination_threshold": 30.0,  # Percentage threshold for procrastination alerts
    "active_threshold": 70.0,           # Percentage threshold for considering time as active
    "check_interval": 300,              # Check interval in seconds (5 minutes)
    "notification_timeout": 30,         # Notification timeout in seconds
}

def load_settings(settings_file: str = "settings.json") -> Dict[str, Any]:
    """Load settings from the settings file.
    
    If the settings file doesn't exist, create it with default settings.
    If it exists but is missing some settings, update it with defaults for those settings.
    
    Args:
        settings_file: Path to the settings JSON file
        
    Returns:
        Dictionary containing the settings
    """
    if not os.path.exists(settings_file):
        save_settings(DEFAULT_SETTINGS, settings_file)
        return DEFAULT_SETTINGS.copy()
        
    with open(settings_file, 'r') as f:
        settings = json.load(f)
        
    # Update settings with any missing defaults
    updated = False
    for key, value in DEFAULT_SETTINGS.items():
        if key not in settings:
            settings[key] = value
            updated = True
            
    if updated:
        save_settings(settings, settings_file)
        
    return settings

def save_settings(settings: Dict[str, Any], settings_file: str = "settings.json") -> None:
    """Save settings to the settings file.
    
    Args:
        settings: Dictionary containing the settings to save
        settings_file: Path to the settings JSON file
    """
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=2)

def update_setting(key: str, value: Any, settings_file: str = "settings.json") -> None:
    """Update a single setting value.
    
    Args:
        key: The setting key to update
        value: The new value for the setting
        settings_file: Path to the settings JSON file
    """
    settings = load_settings(settings_file)
    settings[key] = value
    save_settings(settings, settings_file)

def get_setting(key: str, settings_file: str = "settings.json") -> Any:
    """Get a single setting value.
    
    Args:
        key: The setting key to retrieve
        settings_file: Path to the settings JSON file
        
    Returns:
        The value of the requested setting
    """
    settings = load_settings(settings_file)
    return settings.get(key, DEFAULT_SETTINGS.get(key))