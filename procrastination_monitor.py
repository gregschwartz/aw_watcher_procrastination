#!/usr/bin/env python3

from ast import List
from math import ceil
import aw_transform
import rich
from rich.console import Console
from rich.table import Table

import time
from datetime import datetime, timedelta
from aw_client import ActivityWatchClient
from activity_categorizer import ActivityCategorizer, ActivityCategory, RuleType
from dateutil.tz import tzlocal
from aw_transform.flood import flood

def setup_categorizer():
    """Set up the activity categorizer with rules."""
    categorizer = ActivityCategorizer()
    
    # Procrastination
    procrastination_titles = [
        "funny videos",
        "memes",
        "gaming",
        "social media",
        "entertainment",
        "news",
        "gossip",
        "shopping",
        "online games",
        "viral videos",
        "reddit",
        "tiktok",
        "instagram",
        "pinterest",
        "twitch",
        "youtube",
        "the verge",
        "the guardian",
        "nytimes",
        "wsj",
        "bloomberg",
        "partiful",
        "eventbrite",
    ]
    for title in procrastination_titles:
        categorizer.add_rule(title, ActivityCategory.PROCRASTINATING, RuleType.TITLE)
    
    procrastination_sites = [
        "facebook.com",
        "twitter.com",
        "x.tv",
        "youtube.com",
        "reddit.com",
        "instagram.com",
        "tiktok.com",
        "pinterest.com",
        "twitch.tv",
        "theverge.com",
        "theguardian.com",
        "nytimes.com",
        "wsj.com",
        "bloomberg.com",
        "partiful.com",
        "eventbrite.com",
    ]
    for site in procrastination_sites:
        categorizer.add_rule(site, ActivityCategory.PROCRASTINATING, RuleType.URL)
    
    procrastination_apps = [
        "Spotify",
        "WhatsApp",
    ]
    for app in procrastination_apps:
        categorizer.add_rule(app, ActivityCategory.PROCRASTINATING, RuleType.APP)

    # Productive
    productive_titles = [
        "pull request",
        "code review",
        "jira ticket",
        "documentation",
        "meeting notes",
        "sprint planning",
        "standup",
        "retrospective",
        "technical design",
        "architecture",
        "debugging",
        "unit test",
        "integration test",
        "api",
    ]
    for title in productive_titles:
        categorizer.add_rule(title, ActivityCategory.PRODUCTIVE, RuleType.TITLE)
    
    productive_sites = [
        "github.com",
        "stackoverflow.com",
        "docs.google.com",
        "jira",
        "confluence",
        "gitlab",
        "bitbucket",
        "atlassian",
        "applyall.com",
        "readthedocs.io",
    ]
    for site in productive_sites:
        categorizer.add_rule(site, ActivityCategory.PRODUCTIVE, RuleType.URL)
        categorizer.add_rule(site, ActivityCategory.PRODUCTIVE, RuleType.TITLE)
    
    productive_apps = [
        "Cursor",
        "Visual Studio Code",
        "vscode",
        "PyCharm",
        "IntelliJ",
        "Google Docs",
        "Microsoft Word",
        "Excel",
        "PowerPoint",
        "slack"
    ]
    for app in productive_apps:
        categorizer.add_rule(app, ActivityCategory.PRODUCTIVE, RuleType.APP)
    
    return categorizer

def format_time_ago(time_ago: timedelta) -> str:
    """Format a timedelta into a human readable string (e.g. '5h', '3m', '45s').
    
    Args:
        time_ago: The timedelta to format
        
    Returns:
        A human readable string representing the time ago
    """
    total_seconds = int(time_ago.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def format_duration(duration: timedelta) -> str:
    """Format a timedelta duration into a human readable string.
    
    Args:
        duration: The timedelta to format
        
    Returns:
        A human readable string representing the duration
    """
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def get_recent_activities(client: ActivityWatchClient, categorizer: ActivityCategorizer, time_window: timedelta = timedelta(minutes=5), bucket_ids_to_skip: List = [], debug_level: int = 0) -> List:
    """Get the recent activities.
    
    Args:
        client: ActivityWatch client instance
        time_window: Time window to look back for events (default: 5 minutes)
        
    Returns:
        List of activities
    """
    start_time = datetime.now(tzlocal()) - time_window

    buckets = client.get_buckets()
    if debug_level >= 3:
        print(f"Found {len(buckets)} buckets")
    
    all_events = None
    for bucket_id in buckets:
        # skip afk and input buckets because they are not useful for monitoring
        if "afk_" in bucket_id or "input_" in bucket_id or bucket_id in bucket_ids_to_skip:
            continue

        events = client.get_events(
            bucket_id=bucket_id,
            start=start_time,
            limit=40
        )

        events = flood(events)

        # add more info to each event
        for event in events:
            # remove aw-watcher- from bucket_id as well as the device name (after the _)
            event.bucket_id_short = bucket_id.replace("aw-watcher-", "").split("_")[0]

            app = event.data.get("app", "")
            url = event.data.get("url", "")
            title = event.data.get('title', '')
            
            if debug_level >= 2:
                print(f"\nPre customize, Event: Bucket: {event.bucket_id_short} App: {app}\n\tTitle: {title}\n\tURL: {url}\n\tdata: {event.data}")
            
            if "vscode" in event.bucket_id_short or "cursor" in event.bucket_id_short:
                # Keep vscode as the app name for categorization
                app = event.bucket_id_short
                title = event.data.get('language', '')
                url = event.data.get('file', '')
            # elif "brave" in event.bucket_id_short or "chrome" in event.bucket_id_short:
            #     app = event.bucket_id_short
            #     title = event.data.get('title', '')

            # Format time in local 24-hour format
            event.time_tz = event.timestamp.astimezone(tzlocal()).strftime("%H:%M:%S")
            event.time_ago_str = format_time_ago(datetime.now(tzlocal()) - event.timestamp)
            
            event.duration_str = format_duration(event.duration)
            
            event.category = categorizer.categorize_activity(app, url, title)
            event.category_str = categorizer.status_to_emoji(event.category)

            event.app = app
            event.title = title
            event.url = url

        if all_events is None:
            all_events = events
        else:
            all_events = aw_transform.union_no_overlap(all_events, events)
        
        if debug_level >= 3:
            print(f"Found {len(events)} events from bucket: {bucket_id}")
            
    if not all_events:
        print(f"{datetime.now(tzlocal())}: No events found")
        return None

    if debug_level >= 3:
        print(f"\n\n--- Found {len(all_events)} events in total ---")

    console = Console()
    table = Table(title="Activity History")
    table.add_column("Time", justify="right")
    table.add_column("Duration", justify="left")
    table.add_column("", justify="center")
    table.add_column("Bucket", justify="left")
    table.add_column("App", justify="left")
    table.add_column("Title/Language", justify="left")
    table.add_column("URL", justify="left")
    
    for event in all_events[-20:]:        
        # Show the title/language in the App column for vscode/browser
        table.add_row(event.time_tz, event.duration_str, event.category_str if event.duration > timedelta(seconds=1) else "", event.bucket_id_short, event.app, event.title, event.url, style="green" if event.category == ActivityCategory.PRODUCTIVE else "red" if event.category == ActivityCategory.PROCRASTINATING else "")

    if debug_level >= 1:
        console.print(table)
    return all_events

def get_current_activity(client: ActivityWatchClient, categorizer: ActivityCategorizer, time_window: timedelta = timedelta(minutes=5)) -> tuple[str, str]:
    all_events = get_recent_activities(client, categorizer, time_window)
    if not all_events:
        return "idle", ""
    return all_events[-1].data.get("app", ""), all_events[-1].data.get("url", "")

def calculate_procrastination_percentage(client: ActivityWatchClient, categorizer: ActivityCategorizer, time_window: timedelta = timedelta(minutes=5), debug_level: int = 0) -> float:
    """Calculate the percentage of time spent procrastinating within the given time window.
    
    Args:
        client: ActivityWatch client instance
        categorizer: ActivityCategorizer instance with rules
        time_window: Time window to analyze (default: 5 minutes)
        
    Returns:
        Float representing percentage of time spent procrastinating (0-100)
        Float representing percentage of time spent in Unclear category (0-100)
        Float representing percentage of time spent in Productive category (0-100)
    """
    all_events = get_recent_activities(client, categorizer, time_window, debug_level=debug_level)
    if not all_events:
        return 0.0, 0.0, 0.0
        
    total_duration = timedelta()
    procrastination_duration = timedelta()
    unclear_duration = timedelta()
    productive_duration = timedelta()

    for event in all_events:
        app = event.data.get("app", "")
        url = event.data.get("url", "")
        title = event.data.get('title', '')
        
        # Handle special cases like VSCode/Cursor
        if "vscode" in event.bucket_id_short or "cursor" in event.bucket_id_short:
            app = event.bucket_id_short
            title = event.data.get('language', '')
            
        category = categorizer.categorize_activity(app, url, title)
        
        total_duration += event.duration
        if category == ActivityCategory.PROCRASTINATING:
            procrastination_duration += event.duration
        elif category == ActivityCategory.UNCLEAR:
            unclear_duration += event.duration
        elif category == ActivityCategory.PRODUCTIVE:
            productive_duration += event.duration

    if total_duration.total_seconds() == 0:
        return 0.0, 0.0, 0.0
        
    return (
        (procrastination_duration.total_seconds() / total_duration.total_seconds()) * 100,
        (unclear_duration.total_seconds() / total_duration.total_seconds()) * 100,
        (productive_duration.total_seconds() / total_duration.total_seconds()) * 100
    )

def check_procrastination(categorizer: ActivityCategorizer, client: ActivityWatchClient, time_window: timedelta = timedelta(minutes=5), debug_level: int = 0):
    """Check if current activity is procrastination.
    
    Args:
        categorizer: ActivityCategorizer instance with rules
        client: ActivityWatch client instance
    """
    # app_name, url = get_current_activity(client, categorizer)
    
    # if app_name == "idle":
    #     print(f"{datetime.now(tzlocal())}: User is idle")
        
    procrastination_pct, unclear_pct, productive_pct = calculate_procrastination_percentage(client, categorizer, time_window=time_window, debug_level=debug_level)
    # print(f"Last 5 minutes, Procrastination: {procrastination_pct:.1f}%, Unclear: {unclear_pct:.1f}%, Productive: {productive_pct:.1f}%")
    
    # make ascii stacked bar chart
    print(f"{'😭' * ceil(procrastination_pct / 2)}{'❓' * ceil(unclear_pct / 2)}{'👍' * ceil(productive_pct / 2)} -- {procrastination_pct:.1f}% {unclear_pct:.1f}% {productive_pct:.1f}%")

def main():
    client = ActivityWatchClient("procrastination-monitor")
    categorizer = setup_categorizer()
    print("Starting procrastination monitor... (Press Ctrl+C to stop)")
    
    debug_level = 1
    try:
        while True:
            check_procrastination(categorizer, client, debug_level=debug_level)
            # return
            time.sleep(7)
    except KeyboardInterrupt:
        print("\nStopping procrastination monitor...")

if __name__ == "__main__":
    main() 