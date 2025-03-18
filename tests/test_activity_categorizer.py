#!/usr/bin/env python3

import pytest
from activity_categorizer import ActivityCategorizer, ActivityCategory, ActivityRule, RuleType

@pytest.fixture
def categorizer():
    """Fixture providing a fresh ActivityCategorizer instance."""
    return ActivityCategorizer()

@pytest.fixture
def url_rules(categorizer):
    """Fixture providing common URL rules."""
    categorizer.add_rule("facebook.com", ActivityCategory.PROCRASTINATING, RuleType.URL)
    categorizer.add_rule("twitter.com", ActivityCategory.PROCRASTINATING, RuleType.URL)
    categorizer.add_rule("github.com", ActivityCategory.PRODUCTIVE, RuleType.URL)
    return categorizer

@pytest.fixture
def app_rules(categorizer):
    """Fixture providing common app rules."""
    categorizer.add_rule("Visual Studio Code", ActivityCategory.PRODUCTIVE)
    categorizer.add_rule("Solitaire", ActivityCategory.PROCRASTINATING)
    categorizer.add_rule("slack", ActivityCategory.UNCLEAR)
    return categorizer

def test_add_rule(categorizer):
    """Test adding rules to the categorizer."""
    # Test adding a URL rule
    categorizer.add_rule("facebook.com", ActivityCategory.PROCRASTINATING, RuleType.URL)
    rule = categorizer.rules["facebook.com"]
    assert rule.pattern == "facebook.com"
    assert rule.category == ActivityCategory.PROCRASTINATING
    assert rule.rule_type == RuleType.URL

    # Test adding an app rule
    categorizer.add_rule("Visual Studio Code", ActivityCategory.PRODUCTIVE)
    rule = categorizer.rules["visual studio code"]
    assert rule.pattern == "visual studio code"
    assert rule.category == ActivityCategory.PRODUCTIVE
    assert rule.rule_type == RuleType.APP

    # Test adding a title rule
    categorizer.add_rule("procrastination_monitor.py", ActivityCategory.PRODUCTIVE, RuleType.TITLE)
    rule = categorizer.rules["procrastination_monitor.py"]
    assert rule.pattern == "procrastination_monitor.py"
    assert rule.category == ActivityCategory.PRODUCTIVE
    assert rule.rule_type == RuleType.TITLE

@pytest.mark.parametrize("url,expected_category", [
    ("https://www.facebook.com", ActivityCategory.PROCRASTINATING),
    ("https://github.com/user/repo", ActivityCategory.PRODUCTIVE),
    ("https://messenger.facebook.com", ActivityCategory.PROCRASTINATING),
    ("https://gist.github.com", ActivityCategory.PRODUCTIVE),
    ("https://example.com", ActivityCategory.UNCLEAR),
])
def test_url_categorization(url_rules, url, expected_category):
    """Test URL-based activity categorization."""
    assert url_rules.categorize_activity("Chrome", url) == expected_category

@pytest.mark.parametrize("app_name,expected_category", [
    ("Visual Studio Code", ActivityCategory.PRODUCTIVE),
    ("Solitaire", ActivityCategory.PROCRASTINATING),
    ("Microsoft Visual Studio Code", ActivityCategory.PRODUCTIVE),  # Partial match
    ("VISUAL STUDIO CODE", ActivityCategory.PRODUCTIVE),  # Case insensitive
    ("visual studio code", ActivityCategory.PRODUCTIVE),  # Case insensitive
    ("solitaire", ActivityCategory.PROCRASTINATING),  # Case insensitive
    ("SOLITAIRE", ActivityCategory.PROCRASTINATING),  # Case insensitive
    ("Unknown App", ActivityCategory.UNCLEAR),  # Unknown app
    ("UNKNOWN APP", ActivityCategory.UNCLEAR),  # Unknown app case insensitive
])
def test_app_categorization(app_rules, app_name, expected_category):
    """Test app-based activity categorization."""
    assert app_rules.categorize_activity(app_name) == expected_category

def test_edge_cases(categorizer):
    """Test edge cases and potential error conditions."""
    # Test empty strings
    assert categorizer.categorize_activity("") == ActivityCategory.UNCLEAR
    assert categorizer.categorize_activity("Chrome", "") == ActivityCategory.UNCLEAR
    
    # Test None values
    assert categorizer.categorize_activity("Chrome", None) == ActivityCategory.UNCLEAR
    
    # Test case sensitivity
    categorizer.add_rule("GitHub.com", ActivityCategory.PRODUCTIVE, RuleType.URL)
    assert (
        categorizer.categorize_activity("Chrome", "https://github.com/user")
        == ActivityCategory.PRODUCTIVE
    )
    
    # Test multiple matching rules (longer/more specific match should win)
    categorizer.add_rule("github.com", ActivityCategory.PRODUCTIVE, RuleType.URL)
    categorizer.add_rule("github", ActivityCategory.PROCRASTINATING, RuleType.URL)
    assert (
        categorizer.categorize_activity("Chrome", "https://github.com")
        == ActivityCategory.PRODUCTIVE
    )

def test_more_categorization(categorizer):
    """Test categorization."""
    # Test VSCode with a URL
    assert categorizer.categorize_activity("Cursor", "", 'procrastination_monitor.py — aw-watcher-ask', RuleType.APP) == ActivityCategory.PRODUCTIVE
    
    # window    │ Brave Browser │ theverge.com/movie-reviews/629787/the-electric-s
    assert categorizer.categorize_activity("Brave Browser", "theverge.com/movie-reviews/629787/the-electric-s", RuleType.APP) == ActivityCategory.PROCRASTINATING
    assert categorizer.categorize_activity("Brave Browser", "tiktok.com blah", RuleType.TITLE) == ActivityCategory.PROCRASTINATING
    assert categorizer.categorize_activity("Brave Browser", "Tiktok | Test video", RuleType.TITLE) == ActivityCategory.PROCRASTINATING