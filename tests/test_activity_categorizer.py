"""Unit tests for activity categorizer."""

import json
import pytest
from src.aw_watcher_procrastination.settings import Settings
from src.aw_watcher_procrastination.activity_categorizer import ActivityCategorizer, ActivityCategory

@pytest.fixture
def temp_rules_file(tmp_path):
    """Create a temporary settings file for testing."""
    filename = tmp_path / "test_settings.json"
    settings = Settings(filename) # will create a new file since it doesn't exist in test environment

    settings.update("activity_rules.productive", {
        "titles": ["work", "coding"],
        "urls": ["github.com", "gitlab.com"],
        "apps": ["vscode", "terminal"]
    })
    settings.update("activity_rules.procrastination", {
        "titles": ["gaming", "social"],
        "urls": ["facebook.com", "twitter.com"],
        "apps": ["steam", "discord"]
    })
    # settings = load_settings(filename) # reload settings to get the new rules
    print("settings with new rules: ", settings.get("activity_rules"))
    return str(filename)

@pytest.fixture
def categorizer(temp_rules_file):
    """Create a categorizer instance with test rules."""
    return ActivityCategorizer(rules_file=temp_rules_file)

def test_categorize_productive_app(categorizer):
    """Test categorizing a productive app."""
    print("categorizer: ", categorizer.rules)
    category = categorizer.categorize_activity("vscode", "", "")
    assert category == ActivityCategory.PRODUCTIVE

def test_categorize_procrastination_app(categorizer):
    """Test categorizing a procrastination app."""
    category = categorizer.categorize_activity("steam", "", "")
    assert category == ActivityCategory.PROCRASTINATING

def test_categorize_productive_url(categorizer):
    """Test categorizing a productive URL."""
    category = categorizer.categorize_activity("chrome", "github.com/user/repo", "")
    assert category == ActivityCategory.PRODUCTIVE

def test_categorize_procrastination_url(categorizer):
    """Test categorizing a procrastination URL."""
    category = categorizer.categorize_activity("chrome", "facebook.com/feed", "")
    assert category == ActivityCategory.PROCRASTINATING

def test_categorize_productive_title(categorizer):
    """Test categorizing a productive title."""
    category = categorizer.categorize_activity("", "", "coding project")
    assert category == ActivityCategory.PRODUCTIVE

def test_categorize_procrastination_title(categorizer):
    """Test categorizing a procrastination title."""
    category = categorizer.categorize_activity("", "", "gaming stream")
    assert category == ActivityCategory.PROCRASTINATING

def test_categorize_unclear(categorizer):
    """Test categorizing an unclear activity."""
    category = categorizer.categorize_activity("unknown", "example.com", "random title")
    assert category == ActivityCategory.UNCLEAR

def test_add_rule(categorizer):
    """Test adding a new rule."""
    categorizer.add_rule(ActivityCategory.PRODUCTIVE, "apps", "intellij")
    assert "intellij" in categorizer.rules["productive"]["apps"]

def test_remove_rule(categorizer):
    """Test removing a rule."""
    categorizer.remove_rule(ActivityCategory.PRODUCTIVE, "apps", "vscode")
    assert "vscode" not in categorizer.rules["productive"]["apps"]

def test_status_to_emoji():
    """Test emoji conversion."""
    assert ActivityCategorizer.status_to_emoji(ActivityCategory.PRODUCTIVE) == "✅"
    assert ActivityCategorizer.status_to_emoji(ActivityCategory.PROCRASTINATING) == "❌"
    assert ActivityCategorizer.status_to_emoji(ActivityCategory.UNCLEAR) == "❓"

def test_case_insensitive_matching(categorizer):
    """Test that rule matching is case insensitive."""
    category = categorizer.categorize_activity("VSCode", "GITHUB.COM", "CODING")
    assert category == ActivityCategory.PRODUCTIVE 