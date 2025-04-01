"""Tests for settings functionality."""

import os
import json
import pytest
from src.aw_watcher_procrastination.settings import (
    Settings,
    DEFAULT_SETTINGS
)

@pytest.fixture
def settings_filename(tmp_path):
    """Create a temporary settings file for testing."""
    settings_file = tmp_path / "test_settings.json"
    return str(settings_file)

@pytest.fixture
def settings_object(settings_filename):
    """Create a temporary settings file for testing."""
    return Settings(settings_filename)

def test_load_settings_new_file(settings_filename):
    """Test loading settings when file doesn't exist."""
    settings = Settings(settings_filename)
    assert settings._settings == DEFAULT_SETTINGS
    assert os.path.exists(settings_filename)

def test_load_settings_existing_file(settings_filename, settings_object):
    """Test loading settings from existing file."""
    with open(settings_filename, 'w') as f:
        json.dump(DEFAULT_SETTINGS, f)
    
    settings = Settings(settings_filename)
    for key in DEFAULT_SETTINGS:
        assert settings.get(key) == DEFAULT_SETTINGS[key]

def test_get_setting(settings_object):
    """Test getting settings using dot notation."""
    # Test getting top-level setting
    assert settings_object.get("check_interval") == DEFAULT_SETTINGS["check_interval"]
    
    # Test getting nested setting
    assert settings_object.get("activity_rules.procrastination.titles") == DEFAULT_SETTINGS["activity_rules"]["procrastination"]["titles"]

    # Test getting nested setting that doesn't exist
    with pytest.raises(ValueError):
        settings_object.get("badPath")

    # Test getting nested setting that is not a dict
    with pytest.raises(ValueError):
        settings_object.get("activity_rules.badPath")

def test_update_settings_value(settings_filename, settings_object):
    """Test updating a setting value and reloading from file."""
    # Test updating top-level setting
    test_key = "favorite_number"
    test_value = 42
    settings_object.update(test_key, test_value) # will save to file too

    settings2 = Settings(settings_filename)
    assert settings2.get(test_key) == test_value

    # Test updating nested setting
    test_key = "thresholds.min_procrastination_percent"
    test_value = 10
    settings_object.update(test_key, test_value) # will save to file too

    settings3 = Settings(settings_filename)
    assert settings3.get(test_key) == test_value

def test_update_settings_dict_or_list(settings_filename, settings_object):
    """Test updating a nested setting value and reloading from file."""
    test_key = "bucket_ids_to_skip"
    test_value = ["aw-watcher-afk_", "aw-watcher-input_"]
    settings_object.update(test_key, test_value) # will save to file too

    settings2 = Settings(settings_filename)
    assert settings2.get(test_key) == test_value

    # Test updating nested setting
    test_key = "activity_rules.procrastination"
    test_value = {
        "titles": ["news", "sports"],
        "urls": ["reddit.com", "espn.com"],
        "apps": ["CNN", "ESPN"]
    }
    settings_object.update(test_key, test_value) # will save to file too

    settings3 = Settings(settings_filename)
    assert settings3.get(test_key) == test_value


def test_update_dict_recursively():
    """Test recursive dictionary updating."""
    target = {
        "a": 10,
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
    
    result, updated = Settings._update_recursively(target, source)
    assert updated is True
    assert result["a"] == 10 # 
    assert result["b"]["d"] == 3
    assert result["e"] == 4
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
        fixed, changed = Settings._fix_json_content(input_json)
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
    fixed, changed = Settings._fix_json_content(valid_json)
    assert changed is False
    assert ''.join(fixed.split()) == ''.join(valid_json.split())

def test_update_setting_type_error(settings_object):
    """Test updating setting with wrong type."""
    with pytest.raises(ValueError):
        # Try to update a path that doesn't exist
        settings_object.update("activity_rules.badPath.apps", "value")

    with pytest.raises(ValueError):
        # Try to update a path that is not a dict
        settings_object.update("thresholds.min_procrastination_percent.badPath", "value")