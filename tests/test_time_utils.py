"""Unit tests for time utilities."""

from datetime import datetime, timedelta
from src.aw_watcher_procrastination.time_utils import format_duration, format_time_ago, calculate_end_time

def test_format_duration_seconds():
    """Test formatting duration with only seconds."""
    duration = timedelta(seconds=45)
    assert format_duration(duration) == "45s"

def test_format_duration_minutes():
    """Test formatting duration with minutes."""
    duration = timedelta(minutes=5, seconds=30)
    assert format_duration(duration) == "5m 30s"

def test_format_duration_hours():
    """Test formatting duration with hours."""
    duration = timedelta(hours=2, minutes=15, seconds=10)
    assert format_duration(duration) == "2h 15m 10s"

def test_format_duration_zero():
    """Test formatting zero duration."""
    duration = timedelta()
    assert format_duration(duration) == "0s"

def test_format_time_ago_just_now():
    """Test formatting very recent time."""
    delta = timedelta(seconds=5)
    assert format_time_ago(delta) == "just now"

def test_format_time_ago_seconds():
    """Test formatting seconds ago."""
    delta = timedelta(seconds=30)
    assert format_time_ago(delta) == "30 seconds ago"

def test_format_time_ago_minute():
    """Test formatting single minute."""
    delta = timedelta(minutes=1)
    assert format_time_ago(delta) == "1 minute ago"

def test_format_time_ago_minutes():
    """Test formatting multiple minutes."""
    delta = timedelta(minutes=5)
    assert format_time_ago(delta) == "5 minutes ago"

def test_format_time_ago_hour():
    """Test formatting single hour."""
    delta = timedelta(hours=1)
    assert format_time_ago(delta) == "1 hour ago"

def test_format_time_ago_hours():
    """Test formatting multiple hours."""
    delta = timedelta(hours=3)
    assert format_time_ago(delta) == "3 hours ago"

def test_format_time_ago_day():
    """Test formatting single day."""
    delta = timedelta(days=1)
    assert format_time_ago(delta) == "1 day ago"

def test_format_time_ago_days():
    """Test formatting multiple days."""
    delta = timedelta(days=3)
    assert format_time_ago(delta) == "3 days ago"

def test_format_time_ago_float():
    """Test formatting time from float seconds."""
    assert format_time_ago(30.5) == "30 seconds ago"

def test_calculate_end_time():
    """Test calculating end time from start and duration."""
    start_time = datetime(2024, 1, 1, 12, 0, 0)
    duration = timedelta(minutes=30)
    expected_end = datetime(2024, 1, 1, 12, 30, 0)
    assert calculate_end_time(start_time, duration) == expected_end

