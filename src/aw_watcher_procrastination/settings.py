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
    "delay_showing_popup_again_seconds": 300,  # 5 minutes minimum between popups
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

class Settings:
    """Manages application settings with automatic loading and saving."""
    
    def __init__(self, settings_file: str = "settings.json"):
        """Initialize settings manager.
        
        Args:
            settings_file: Path to the settings JSON file
        """
        self._settings_file = settings_file
        self._settings = None
        self.load()
    
    def load(self) -> None:
        """Load settings from file, creating with defaults if needed."""
        if not os.path.exists(self._settings_file):
            self._settings = DEFAULT_SETTINGS.copy()
            self.save()
            return

        try:
            with open(self._settings_file, 'r') as f:
                content = f.read()
                
            # Try to load and fix JSON if needed
            try:
                self._settings = json.loads(content)
            except json.JSONDecodeError:
                fixed_content, made_changes = self._fix_json_content(content)
                try:
                    self._settings = json.loads(fixed_content)
                    if made_changes:
                        # Save the fixed content
                        with open(self._settings_file, 'w') as f:
                            f.write(fixed_content)
                except Exception as e:
                    print(f"tried to fix {self._settings_file} but failed: {e}")
                    raise
            
            # Update with any missing defaults
            self._settings, updated = self._update_recursively(self._settings, DEFAULT_SETTINGS)
            if updated:
                self.save()
                
        except Exception as e:
            print(f"Error loading settings from {self._settings_file}:", file=sys.stderr)
            print(e, file=sys.stderr)
            print("Using default settings", file=sys.stderr)
            self._settings = DEFAULT_SETTINGS.copy()
    
    def save(self) -> None:
        """Save current settings to file."""
        try:
            with open(self._settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings to {self._settings_file}:", file=sys.stderr)
            print(e, file=sys.stderr)
    
    def get(self, key: str) -> Any:
        """Get a setting value using dot notation.
        
        Args:
            key: Setting key using dot notation (e.g. "thresholds.procrastination_threshold")
            
        Returns:
            The setting value
            
        Examples:
            >>> settings.get("thresholds.procrastination_threshold")
            30.0
            >>> settings.get("window_sizes.notification.default.width")
            600
        """
        if self._settings is None:
            self.load()
            
        keys = key.split('.')
        current = self._settings
        for k in keys[:-1]:
            if k not in current:
                raise ValueError(f"Can't find {key}, because along that path {key} does not exist")
            elif not isinstance(current[k], dict):
                raise ValueError(f"Can't find {key}, because along that path {key} is not a dictionary")
            current = current[k]
        
        final_key = keys[-1]
        if final_key not in current:
            raise ValueError(f"Final key {final_key} in {key} does not exist")
        return current[final_key]
    
    def update(self, key: str, value: Any) -> None:
        """Update a setting value using dot notation.
        
        Args:
            key: Setting key using dot notation (e.g. "thresholds.procrastination_threshold")
            value: New value for the setting
        """
        if self._settings is None:
            self.load()
        
        # Navigate to the correct nested dict
        keys = key.split('.')
        current = self._settings
        for k in keys[:-1]:
            if k not in current:
                raise ValueError(f"Can't find {key}, because along that path {key} does not exist")
            elif not isinstance(current[k], dict):
                raise ValueError(f"Can't find {key}, because along that path {key} is not a dictionary")
            current = current[k]
            
        # Update the value
        final_key = keys[-1]
        current[final_key] = value
        self.save()
    
    @staticmethod
    def _fix_json_content(content: str) -> Tuple[str, bool]:
        """Fix common JSON formatting issues.
        
        Args:
            content: JSON content string
            
        Returns:
            Tuple of (fixed content, whether changes were made)
        """
        original = content
        
        # Fix trailing commas in objects
        content = re.sub(r',(\s*})(?=[^}]*$)', r'\1', content, count=0, flags=re.MULTILINE)
        
        # Fix trailing commas in arrays
        content = re.sub(r',(\s*\])(?=[^\]]*$)', r'\1', content, count=0, flags=re.MULTILINE)
        
        # Fix trailing commas after values
        content = re.sub(r',([\s\n]*)(}|\])', r'\1\2', content, count=0)
        
        return content, content != original
    
    @staticmethod
    def _update_recursively(target: Dict[str, Any], source: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Update target dict with missing values from source dict.
        
        Args:
            target: Dict to update
            source: Dict to copy missing values from
            
        Returns:
            Tuple of (updated dict, whether any values were updated)
        """
        updated = False
        for key, value in source.items():
            if key not in target:
                target[key] = value
                updated = True
            elif isinstance(value, dict) and isinstance(target[key], dict):
                _, sub_updated = Settings._update_recursively(target[key], value)
                updated = updated or sub_updated
        return target, updated
