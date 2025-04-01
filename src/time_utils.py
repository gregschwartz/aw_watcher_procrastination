"""Time-related utility functions."""

from datetime import datetime, timedelta
from typing import Union

def format_duration(duration: timedelta) -> str:
    """Format a timedelta duration into a human-readable string.
    
    Args:
        duration: The duration to format
        
    Returns:
        Formatted string like "2h 30m" or "45s"
    """
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or (hours > 0 and seconds > 0):
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
        
    return " ".join(parts)

def format_time_ago(delta: Union[timedelta, float]) -> str:
    """Format a time difference into a human-readable "time ago" string.
    
    Args:
        delta: Time difference as timedelta or seconds
        
    Returns:
        String like "2 minutes ago" or "just now"
    """
    if isinstance(delta, float):
        delta = timedelta(seconds=delta)
        
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 10:
        return "just now"
    elif total_seconds < 60:
        return f"{total_seconds} seconds ago"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = total_seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"

def calculate_end_time(start_time: datetime, duration: timedelta) -> datetime:
    """Calculate the end time given a start time and duration.
    
    Args:
        start_time: The starting timestamp
        duration: The duration of the event
        
    Returns:
        The calculated end time
    """
    return start_time + duration
