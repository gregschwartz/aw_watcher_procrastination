#!/usr/bin/env python3

import json
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

class ActivityCategory(Enum):
    PROCRASTINATING = "Procrastinating"
    UNCLEAR = "Unclear"
    PRODUCTIVE = "Productive"

class RuleType(Enum):
    APP = "app"
    URL = "url"
    TITLE = "title"

@dataclass
class ActivityRule:
    pattern: str  # String to match in app name, URL, or title
    category: ActivityCategory
    rule_type: RuleType = RuleType.APP

class ActivityCategorizer:
    def __init__(self, rules_file: str = "activity_rules.json"):
        """Initialize the ActivityCategorizer with rules from a JSON file.
        
        Args:
            rules_file: Path to the JSON file containing categorization rules
        """
        self.rules: Dict[str, ActivityRule] = {}
        self.rules_file = rules_file
        self.load_rules()
        
    def load_rules(self):
        """Load categorization rules from the JSON file.
        
        Each rule is loaded independently, so if one rule fails to load,
        it won't affect other rules. Errors are logged but don't stop execution.
        """
        try:
            with open(self.rules_file, 'r') as f:
                rules_data = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Rules file {self.rules_file} not found. Starting with empty rules.")
            return
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in {self.rules_file}: {e}. Starting with empty rules.")
            return

        # Clear existing rules before loading new ones
        self.rules.clear()
        
        # Map of internal category names to ActivityCategory enum values
        categories = {
            "procrastination": ActivityCategory.PROCRASTINATING,
            "productive": ActivityCategory.PRODUCTIVE
        }
        
        # Map of rule types in JSON to RuleType enum values
        rule_types = {
            "titles": RuleType.TITLE,
            "urls": RuleType.URL,
            "apps": RuleType.APP
        }
        
        # Load all rules using a nested loop
        for category_name, category_enum in categories.items():
            category_data = rules_data.get(category_name, {})
            for rule_type_name, rule_type_enum in rule_types.items():
                patterns = category_data.get(rule_type_name, [])
                for pattern in patterns:
                    try:
                        if not isinstance(pattern, str):
                            logging.warning(f"Skipping invalid pattern {pattern} (not a string)")
                            continue
                        if not pattern.strip():
                            logging.warning(f"Skipping empty pattern in {category_name}/{rule_type_name}")
                            continue
                        self.add_rule(pattern, category_enum, rule_type_enum)
                    except Exception as e:
                        logging.error(f"Failed to add rule {pattern} ({category_name}/{rule_type_name}): {e}")
        
        if not self.rules:
            logging.warning("No valid rules were loaded")
        
    def add_rule(self, pattern: str, category: ActivityCategory, rule_type: RuleType = RuleType.APP):
        """Add a new categorization rule.
        
        Args:
            pattern: String to match in app name, URL, or title
            category: Category to assign when pattern matches
            rule_type: Type of rule (APP, URL, or TITLE)
        """
        # Store patterns in lowercase for case-insensitive matching
        self.rules[pattern.lower()] = ActivityRule(pattern.lower(), category, rule_type)
        
    def _find_best_match(self, text: str, rule_type: Optional[RuleType] = None) -> Optional[ActivityRule]:
        """Find the longest matching rule for the given text."""
        text = text.lower()
        best_match = None
        best_length = 0
        
        for rule in self.rules.values():
            if rule_type and rule.rule_type != rule_type:
                continue
            if rule.pattern in text and len(rule.pattern) > best_length:
                best_match = rule
                best_length = len(rule.pattern)
                
        return best_match
        
    def categorize_activity(self, app_name: str, url: Optional[str] = None, title: Optional[str] = None) -> ActivityCategory:
        """Categorize an activity based on app name, URL, and window/tab title.
        
        Args:
            app_name: Name of the application
            url: Optional URL if it's a browser activity
            title: Optional window/tab title from event.data["title"]
            
        Returns:
            ActivityCategory indicating if the activity is productive, procrastinating, or unclear
        """
        # Handle None values
        app_name = app_name or ""
        url = url or ""
        title = title or ""
        
        # First check URL rules if URL is provided
        if url:
            url_rule = self._find_best_match(url, RuleType.URL)
            if url_rule:
                return url_rule.category

        # Then check title rules if title is provided
        if title:
            title_rule = self._find_best_match(title, RuleType.TITLE)
            if title_rule:
                return title_rule.category

        # Finally check app name rules
        app_rule = self._find_best_match(app_name, RuleType.APP)
        if app_rule:
            return app_rule.category

        return ActivityCategory.UNCLEAR

    def status_to_emoji(self, category: ActivityCategory) -> str:
        if category == ActivityCategory.PROCRASTINATING:
            return "😭"
        elif category == ActivityCategory.UNCLEAR:
            return "❓"
        elif category == ActivityCategory.PRODUCTIVE:
            return "✅"
        return "🤷‍♂️"
