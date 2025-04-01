"""Test notification window functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from PyQt6.QtWidgets import QApplication

from aw_watcher_procrastination.notification_window import NotificationWindow
from aw_watcher_procrastination.activity_categorizer import ActivityCategorizer
from aw_watcher_procrastination.event_processor import EventProcessor

@pytest.fixture
def app():
    """Create a QApplication instance for testing."""
    return QApplication([])

@pytest.fixture
def notification_window(app):
    """Create a NotificationWindow instance for testing."""
    event_processor = MagicMock(spec=EventProcessor)
    categorizer = MagicMock(spec=ActivityCategorizer)
    return NotificationWindow(event_processor, categorizer)

def test_notification_delay(notification_window):
    """Test that notifications respect the delay setting."""
    notification_window.settings.update("delay_showing_popup_again_seconds", 300)
    
    # First show should work
    notification_window.show_alert(30, 20, 50, 80)
    assert notification_window.isVisible()
    first_shown = notification_window._last_shown
    
    # Hide window
    notification_window.hide()
    
    # Try to show again immediately - should be skipped
    notification_window.show_alert(35, 15, 50, 85)
    assert not notification_window.isVisible()
    assert notification_window._last_shown == first_shown  # Last shown time shouldn't update
    
    # Simulate time passing
    notification_window._last_shown = datetime.now() - timedelta(seconds=301)
    
    # Should show again after delay
    notification_window.show_alert(40, 10, 50, 90)
    assert notification_window.isVisible()
    assert notification_window._last_shown > first_shown 