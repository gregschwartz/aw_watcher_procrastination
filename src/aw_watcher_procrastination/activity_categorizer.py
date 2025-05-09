"""Activity categorization functionality."""

from enum import Enum
from typing import Dict
from .settings import Settings

class ActivityCategory(Enum):
    """Enumeration of possible activity categories."""
    PRODUCTIVE = "productive"
    PROCRASTINATING = "procrastinating"
    UNCLEAR = "unclear"

class ActivityCategorizer:
    """Categorizes activities based on rules."""
    
    def __init__(self, rules_file: str = "settings.json"):
        """Initialize the activity categorizer.
        
        Args:
            rules_file: Path to the settings JSON file
        """
        self.settings = Settings(rules_file)
        self.load_rules()

    def load_rules(self) -> Dict:
        """Load categorization rules from the settings file.
        
        Returns:
            Dictionary containing the rules
        """
        # Reload settings file
        self.settings.load()
        self.rules = self.settings.get("activity_rules")
        return self.rules

    def save_rules(self) -> None:
        """Save the current rules to the settings file."""
        self.settings.update("activity_rules", self.rules)

    def categorize_activity(self, app: str, url: str, title: str) -> ActivityCategory:
        """Categorize an activity based on its properties.
        
        Args:
            app: Application name
            url: URL or file path
            title: Window or tab title
            
        Returns:
            The determined activity category
        """
        # Check procrastination rules first
        if self._matches_rules(app, url, title, self.rules["procrastination"]):
            return ActivityCategory.PROCRASTINATING
            
        # Then check productive rules
        if self._matches_rules(app, url, title, self.rules["productive"]):
            return ActivityCategory.PRODUCTIVE
            
        # If no match, mark as unclear
        return ActivityCategory.UNCLEAR
        
    def _matches_rules(self, app: str, url: str, title: str, rules: Dict) -> bool:
        """Check if an activity matches any rules in the given rule set.
        
        Args:
            app: Application name
            url: URL or file path
            title: Window or tab title
            rules: Dictionary of rules to check against
            
        Returns:
            True if the activity matches any rules, False otherwise
        """
        # Check app rules
        if app and any(rule.lower() in app.lower() for rule in rules["apps"]):
            return True
            
        # Check URL rules
        if url and any(rule.lower() in url.lower() for rule in rules["urls"]):
            return True
            
        # Check title rules
        if title and any(rule.lower() in title.lower() for rule in rules["titles"]):
            return True
            
        return False
        
    def add_rule(self, category: ActivityCategory, rule_type: str, value: str) -> None:
        """Add a new rule for categorizing activities.
        
        Args:
            category: The category to add the rule for
            rule_type: Type of rule ("apps", "urls", or "titles")
            value: The rule value to add
        """
        category_key = "productive" if category == ActivityCategory.PRODUCTIVE else "procrastination"
        if rule_type in self.rules[category_key]:
            if value not in self.rules[category_key][rule_type]:
                self.rules[category_key][rule_type].append(value)
                self.save_rules()
                
    def remove_rule(self, category: ActivityCategory, rule_type: str, value: str) -> None:
        """Remove a rule for categorizing activities.
        
        Args:
            category: The category to remove the rule from
            rule_type: Type of rule ("apps", "urls", or "titles")
            value: The rule value to remove
        """
        category_key = "productive" if category == ActivityCategory.PRODUCTIVE else "procrastination"
        if rule_type in self.rules[category_key]:
            if value in self.rules[category_key][rule_type]:
                self.rules[category_key][rule_type].remove(value)
                self.save_rules()
                
    @staticmethod
    def status_to_emoji(category: ActivityCategory) -> str:
        """Convert a category to its corresponding emoji.
        
        Args:
            category: The activity category
            
        Returns:
            Emoji representing the category
        """
        if category == ActivityCategory.PRODUCTIVE:
            return "✅"
        elif category == ActivityCategory.PROCRASTINATING:
            return "❌"
        else:
            return "❓" 