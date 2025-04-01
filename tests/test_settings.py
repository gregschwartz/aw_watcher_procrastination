"""Tests for settings functionality."""

import os
import json
import pytest
from src.settings import (
    load_settings,
    save_settings,
    update_setting,
    get_setting,
    fix_json_content,
    update_dict_recursively,
    DEFAULT_SETTINGS
)

@pytest.fixture
def temp_settings_file(tmp_path):
    """Create a temporary settings file for testing."""
    settings_file = tmp_path / "test_settings.json"
    return str(settings_file)

def test_load_settings_new_file(temp_settings_file):
    """Test loading settings when file doesn't exist."""
    settings = load_settings(temp_settings_file)
    assert settings == DEFAULT_SETTINGS
    assert os.path.exists(temp_settings_file)

def test_load_settings_existing_file(temp_settings_file):
    """Test loading settings from existing file."""
    test_settings = {"test_key": "test_value"}
    with open(temp_settings_file, 'w') as f:
        json.dump(test_settings, f)
    
    settings = load_settings(temp_settings_file)
    assert "test_key" in settings
    assert settings["test_key"] == "test_value"
    # Should also have default settings
    for key in DEFAULT_SETTINGS:
        assert key in settings

def test_save_settings(temp_settings_file):
    """Test saving settings to file."""
    test_settings = {"test_key": "test_value"}
    save_settings(test_settings, temp_settings_file)
    
    with open(temp_settings_file, 'r') as f:
        loaded = json.load(f)
    assert loaded == test_settings

def test_update_setting(temp_settings_file):
    """Test updating a single setting."""
    save_settings(DEFAULT_SETTINGS, temp_settings_file)
    
    # Test updating top-level setting
    update_setting("check_interval", 600, temp_settings_file)
    assert get_setting("check_interval", temp_settings_file) == 600
    
    # Test updating nested setting
    update_setting("window_sizes.notification.default.width", 800, temp_settings_file)
    assert get_setting("window_sizes.notification.default.width", temp_settings_file) == 800

def test_get_setting(temp_settings_file):
    """Test getting settings using dot notation."""
    save_settings(DEFAULT_SETTINGS, temp_settings_file)
    
    # Test getting top-level setting
    assert get_setting("check_interval", temp_settings_file) == DEFAULT_SETTINGS["check_interval"]
    
    # Test getting nested setting
    assert get_setting("window_sizes.notification.default.width", temp_settings_file) == \
           DEFAULT_SETTINGS["window_sizes"]["notification"]["default"]["width"]

def test_update_dict_recursively():
    """Test recursive dictionary updating."""
    target = {
        "a": 1,
        "b": {
            "c": 2
        }
    }
    source = {
        "a": 1,
        "b": {
            "c": 2,
            "d": 3
        },
        "e": 4
    }
    
    result, updated = update_dict_recursively(target, source)
    assert updated is True
    assert result["b"]["d"] == 3
    assert result["e"] == 4
    assert result["a"] == 1
    assert result["b"]["c"] == 2

def test_fix_json_content():
    """Test fixing common JSON formatting issues."""
    test_cases = [
        # Test trailing commas in objects
        (
            '''{
  "a": 1,
  "b": 2,
}''',
            '''{
  "a": 1,
  "b": 2
}'''
        ),
        # Test multiple trailing commas in objects
        (
            '''{
  "a": 1,,
  "b": 2,,
}''',
            '''{
  "a": 1,
  "b": 2
}'''
        ),
        # Test trailing commas in arrays
        (
            '''{
  "array": [
    1,
    2,
    3,
  ]
}''',
            '''{
  "array": [
    1,
    2,
    3
  ]
}'''
        ),
        # Test multiple trailing commas in arrays
        (
            '''{
  "array": [
    1,,
    2,,
    3,,
  ]
}''',
            '''{
  "array": [
    1,
    2,
    3
  ]
}'''
        ),
        # Test nested structures
        (
            '''{
  "array": [
    1,
    2,
  ],
  "object": {
    "a": 1,
  },
}''',
            '''{
  "array": [
    1,
    2
  ],
  "object": {
    "a": 1
  }
}'''
        ),
        # Test multiple levels of nesting
        (
            '''{
  "a": {
    "b": [
      1,
      2,
    ],
    "c": {
      "d": 3,
    },
  },
}''',
            '''{
  "a": {
    "b": [
      1,
      2
    ],
    "c": {
      "d": 3
    }
  }
}'''
        )
    ]
    
    for input_json, expected_json in test_cases:
        fixed, changed = fix_json_content(input_json)
        # Remove whitespace for comparison
        fixed_normalized = ''.join(fixed.split())
        expected_normalized = ''.join(expected_json.split())
        assert fixed_normalized == expected_normalized
        assert changed is True
        # Verify the fixed JSON is valid
        assert json.loads(fixed) is not None

def test_fix_json_content_no_changes():
    """Test that valid JSON is not modified."""
    valid_json = '''{
  "array": [
    1,
    2,
    3
  ],
  "object": {
    "a": 1
  }
}'''
    fixed, changed = fix_json_content(valid_json)
    assert changed is False
    assert ''.join(fixed.split()) == ''.join(valid_json.split())

def test_load_settings_with_invalid_json(temp_settings_file):
    """Test loading settings with invalid JSON that can be fixed."""
    invalid_json = '''{
  "check_interval": 300,
  "notification_timeout": 30,
}'''
    with open(temp_settings_file, 'w') as f:
        f.write(invalid_json)
    
    # Should not raise an exception
    settings = load_settings(temp_settings_file)
    assert settings["check_interval"] == 300
    assert settings["notification_timeout"] == 30

def test_update_setting_invalid_path(temp_settings_file):
    """Test updating setting with invalid path."""
    save_settings(DEFAULT_SETTINGS, temp_settings_file)
    
    with pytest.raises(KeyError):
        update_setting("invalid.path", "value", temp_settings_file)

def test_get_setting_invalid_path(temp_settings_file):
    """Test getting setting with invalid path."""
    save_settings(DEFAULT_SETTINGS, temp_settings_file)
    
    with pytest.raises(KeyError):
        get_setting("invalid.path", temp_settings_file)

def test_update_setting_type_error(temp_settings_file):
    """Test updating setting with wrong type."""
    save_settings(DEFAULT_SETTINGS, temp_settings_file)
    
    with pytest.raises(TypeError):
        # Try to update a non-dict path
        update_setting("check_interval.invalid", "value", temp_settings_file) 