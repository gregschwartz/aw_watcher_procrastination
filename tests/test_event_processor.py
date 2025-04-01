"""Integration tests for event processing."""

from datetime import datetime, timedelta
import pytest
from unittest.mock import MagicMock, patch
from dateutil.tz import tzlocal
from aw_client import ActivityWatchClient
from aw_core.models import Event
from aw_watcher_procrastination.activity_categorizer import ActivityCategorizer, ActivityCategory
from aw_watcher_procrastination.event_processor import EventProcessor

class MockEvent:
    """Mock event for testing."""
    def __init__(self, timestamp, duration, data):
        self.timestamp = timestamp
        self.duration = duration
        self.data = data

@pytest.fixture
def mock_client():
    """Create a mock ActivityWatch client."""
    client = MagicMock(spec=ActivityWatchClient)
    client.get_buckets.return_value = ["aw-watcher-window_test", "aw-watcher-afk_test"]
    return client

@pytest.fixture
def mock_events():
    """Create mock events for testing."""
    now = datetime.now(tzlocal())
    events = [
        MockEvent(
            now - timedelta(minutes=4),
            timedelta(minutes=2),
            {"app": "vscode", "title": "coding project"}
        ),
        MockEvent(
            now - timedelta(minutes=2),
            timedelta(minutes=1),
            {"app": "chrome", "url": "facebook.com", "title": "social feed"}
        ),
        MockEvent(
            now - timedelta(minutes=1),
            timedelta(minutes=1),
            {"app": "unknown", "title": "random activity"}
        )
    ]
    return events

@pytest.fixture
def event_processor(mock_client, tmp_path):
    """Create an event processor with mock client and temporary files."""
    settings_file = tmp_path / "test_settings.json"
    categorizer = ActivityCategorizer(rules_file=str(settings_file))
    categorizer.add_rule(ActivityCategory.PRODUCTIVE, "apps", "vscode")
    categorizer.add_rule(ActivityCategory.PROCRASTINATING, "urls", "facebook.com")
    processor = EventProcessor(mock_client, categorizer)
    return processor

def test_get_recent_activities(event_processor, mock_client, mock_events):
    """Test getting and processing recent activities."""
    mock_client.get_events.return_value = mock_events
    
    activities = event_processor.get_recent_activities(timedelta(minutes=5))
    assert len(activities) == 3
    
    # Check processed event attributes
    vscode_event = activities[0]
    assert vscode_event.category == ActivityCategory.PRODUCTIVE
    assert vscode_event.app == "vscode"
    assert hasattr(vscode_event, "time_tz")
    assert hasattr(vscode_event, "duration_str")
    
    facebook_event = activities[1]
    assert facebook_event.category == ActivityCategory.PROCRASTINATING
    assert "facebook.com" in facebook_event.url
    
    unknown_event = activities[2]
    assert unknown_event.category == ActivityCategory.UNCLEAR

def test_calculate_procrastination_percentage(event_processor, mock_client, mock_events):
    """Test calculating procrastination percentages."""
    mock_client.get_events.return_value = mock_events
    
    proc_pct, unclear_pct, prod_pct, active_pct = event_processor.calculate_procrastination_percentage(
        timedelta(minutes=5)
    )
    
    # Total duration is 4 minutes (240 seconds)
    # Productive: 2 minutes (120 seconds) = 50%
    # Procrastinating: 1 minute (60 seconds) = 25%
    # Unclear: 1 minute (60 seconds) = 25%
    # Active time: 4 minutes out of 5 minutes = 80%
    
    assert proc_pct == pytest.approx(25.0)
    assert unclear_pct == pytest.approx(25.0)
    assert prod_pct == pytest.approx(50.0)
    assert active_pct == pytest.approx(80.0)

def test_event_processing_with_gaps(event_processor, mock_client):
    """Test processing events with gaps between them."""
    now = datetime.now(tzlocal())
    events = [
        MockEvent(
            now - timedelta(minutes=5),
            timedelta(minutes=1),
            {"app": "vscode", "title": "coding"}
        ),
        # 2-minute gap
        MockEvent(
            now - timedelta(minutes=2),
            timedelta(minutes=2),
            {"app": "chrome", "url": "facebook.com"}
        )
    ]
    mock_client.get_events.return_value = events
    
    activities = event_processor.get_recent_activities(timedelta(minutes=5))
    assert len(activities) == 2
    
    # Verify gap calculation
    end_time1 = activities[0].timestamp + activities[0].duration
    start_time2 = activities[1].timestamp
    gap = start_time2 - end_time1
    assert gap == timedelta(minutes=2)

def test_event_processing_with_overlaps(event_processor, mock_client):
    """Test processing events with overlapping times."""
    now = datetime.now(tzlocal())
    events = [
        MockEvent(
            now - timedelta(minutes=3),
            timedelta(minutes=2),
            {"app": "vscode", "title": "coding"}
        ),
        # 1-minute overlap
        MockEvent(
            now - timedelta(minutes=2),
            timedelta(minutes=2),
            {"app": "chrome", "url": "facebook.com"}
        )
    ]
    mock_client.get_events.return_value = events
    
    activities = event_processor.get_recent_activities(timedelta(minutes=5))
    assert len(activities) == 2
    
    # Verify overlap calculation
    end_time1 = activities[0].timestamp + activities[0].duration
    start_time2 = activities[1].timestamp
    overlap = start_time2 - end_time1
    assert overlap == timedelta(minutes=-1) 