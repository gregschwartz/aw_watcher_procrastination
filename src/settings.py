"""Settings management functionality."""

import json
import os
import sys
import re
from typing import Dict, Any, Tuple

DEFAULT_SETTINGS = {
    "bucket_ids_to_skip": [
        "aw-watcher-afk_",
        "aw-watcher-input_"
    ],
    "thresholds": {
        "procrastination_threshold": 30.0,
        "active_threshold": 70.0,
    },
    "check_interval": 300,
    "notification_timeout": 30,
    "window_sizes": {
        "notification": {
        "default": {
            "width": 600,
            "height": 500
        },
        "expanded": {
            "width": 600,
            "height": 700
        }
        },
        "browser": {
        "width": 1200,
        "height": 800
        }
    },
    "activity_rules": {
        "procrastination": {
            "titles": [],
            "apps": [],
            "urls": []
        },
        "productive": {
            "titles": [],
            "apps": [],
            "urls": []
        }
    }
}

def update_dict_recursively(target: Dict[str, Any], source: Dict[str, Any]) -> bool:
    """Recursively update a dictionary with values from another dictionary.
    
    Args:
        target: Dictionary to update
        source: Dictionary to copy values from
        
    Returns:
        True if any values were updated, False otherwise
    """
    updated = False
    for key, value in source.items():
        if key not in target:
            target[key] = value
            updated = True
        elif isinstance(value, dict) and isinstance(target[key], dict):
            target[key], updated = update_dict_recursively(target[key], value)
    return target, updated

def fix_json_content(content: str) -> Tuple[str, bool]:
    """Fix common JSON formatting issues.
    
    Args:
        content: JSON content string
        
    Returns:
        Tuple of (fixed content, whether changes were made)
    """
    original = content
    
    # Fix trailing commas in objects (handles multi-line and single-line)
    content = re.sub(r',(\s*})(?=[^}]*$)', r'\1', content, count=0, flags=re.MULTILINE)
    
    # Fix trailing commas in arrays (handles multi-line and single-line)
    content = re.sub(r',(\s*\])(?=[^\]]*$)', r'\1', content, count=0, flags=re.MULTILINE)
    
    # Remove multiple trailing commas in objects
    content = re.sub(r',+(\s*})(?=[^}]*$)', r'\1', content, count=0, flags=re.MULTILINE)
    
    # Remove multiple trailing commas in arrays
    content = re.sub(r',+(\s*\])(?=[^\]]*$)', r'\1', content, count=0, flags=re.MULTILINE)
    
    # Fix trailing commas after values in objects
    content = re.sub(r',([\s\n]*)(}|\])', r'\1\2', content, count=0)
    
    # Fix multiple consecutive commas between values
    content = re.sub(r',\s*,+', ',', content, count=0)
    
    return content, content != original

def try_load_json(file_path: str) -> Dict[str, Any]:
    """Try to load and fix JSON if needed.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        SystemExit: If JSON cannot be parsed even after fixes
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Try to fix common JSON issues
        fixed_content, made_changes = fix_json_content(content)
        try:
            result = json.loads(fixed_content)
            if made_changes:
                # Only save if the fixes worked
                with open(file_path, 'w') as f:
                    f.write(fixed_content)
            return result
        except json.JSONDecodeError:
            # If still can't parse, show the error location
            print(f"Error in settings file {file_path}:")
            lines = fixed_content.splitlines()
            for i, line in enumerate(lines, 1):
                print(f"{i}: {line}")
            print("\nJSON parsing error. Please check the file format.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading settings file {file_path}:")
            print(e)
            sys.exit(1)

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
    
    settings = try_load_json(settings_file)
    
    # Update settings with any missing defaults recursively
    settings, updated = update_dict_recursively(settings, DEFAULT_SETTINGS)
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
    # use dot notation to update the setting
    keys = key.split(".")
    current = settings
    for k in keys[:-1]:  # Iterate through all but last key
        if not isinstance(current, dict):
            raise ValueError(f"Setting {key} is not a dictionary")
        current = current[k]
    current[keys[-1]] = value  # Set value at final key
    save_settings(settings, settings_file)

def get_setting(key: str, settings_file: str = "settings.json") -> Any:
    """Get a single setting value using dot notation for nested settings.
    
    Args:
        key: The setting key to retrieve using dot notation (e.g. "thresholds.procrastination_threshold")
        settings_file: Path to the settings JSON file
        
    Returns:
        The value of the requested setting
        
    Examples:
        >>> get_setting("thresholds.procrastination_threshold")
        30.0
        >>> get_setting("window_sizes.notification.default.width")
        600
    """
    settings = load_settings(settings_file)
    keys = key.split(".")
    current = settings
    for k in keys:
        current = current[k]
    return current
