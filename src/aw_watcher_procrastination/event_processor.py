"""Event processing and analysis functionality."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dateutil.tz import tzlocal
import aw_transform
from aw_client import ActivityWatchClient
from rich.table import Table
from rich.console import Console

from .activity_categorizer import ActivityCategorizer, ActivityCategory
from .time_utils import format_duration, format_time_ago
from .settings import Settings

class EventProcessor:
    """Processes and analyzes ActivityWatch events."""
    
    def __init__(self, client: ActivityWatchClient, categorizer: ActivityCategorizer):
        """Initialize the event processor.
        
        Args:
            client: ActivityWatch client instance
            categorizer: Activity categorizer instance
        """
        self.client = client
        self.categorizer = categorizer
        self.settings = Settings()
    
    def get_recent_activities(self, time_window: timedelta = timedelta(minutes=5), debug_level: int = 0) -> Optional[List]:
        """Get recent activities within the time window.
        
        Args:
            time_window: Time window to look back for events
            debug_level: Level of debug output (0=none, 1=events)
            
        Returns:
            List of processed events or None if no events found
        """
        start_time = datetime.now(tzlocal()) - time_window
        bucket_ids_to_skip = self.settings.get("bucket_ids_to_skip")
        
        all_events = None
        for bucket_id in self.client.get_buckets():
            if any(skip_id in bucket_id for skip_id in bucket_ids_to_skip):
                continue

            events = self.client.get_events(
                bucket_id=bucket_id,
                start=start_time,
                limit=40
            )
            
            # events = aw_transform.flood(events)
            events = self._process_events(events, bucket_id, debug_level=debug_level)
            
            if all_events is None:
                all_events = events
            else:
                all_events = aw_transform.union_no_overlap(all_events, events)
        
        all_events = aw_transform.flood(all_events)

        if debug_level >= 1:
            self.print_events(all_events, title="All Events")

        return all_events

    def _process_events(self, events: List, bucket_id: str, debug_level: int = 0) -> List:
        """Process raw events to add additional information.
        
        Args:
            events: List of raw events
            bucket_id: ID of the bucket events came from
            debug_level: Level of debug output
            
        Returns:
            List of processed events
        """
        for event in events:
            # Basic event info
            event.bucket_id_short = bucket_id.replace("aw-watcher-", "").split("_")[0]
            
            # Extract app and URL info
            app = event.data.get("app", "")
            url = event.data.get("url", "")
            title = event.data.get('title', '')
            
            # Special handling for IDE events
            if "vscode" in event.bucket_id_short or "cursor" in event.bucket_id_short:
                app = event.bucket_id_short
                title = event.data.get('language', '')
                url = event.data.get('file', '')
            
            # Process URL for domain
            if url:
                url = self._clean_url(url)
                event.url_domain = self._extract_domain(url)
            
            # Add formatted times
            event.time_tz = event.timestamp.astimezone(tzlocal()).strftime("%H:%M:%S")
            event.time_ago_str = format_time_ago(datetime.now(tzlocal()) - event.timestamp)
            event.duration_str = format_duration(event.duration)
            
            # Add categorization
            event.category = self.categorizer.categorize_activity(app, url, title)
            event.category_str = self.categorizer.status_to_emoji(event.category)
            
            # Store processed values
            event.app = app
            event.title = title
            event.url = url
            
        if debug_level >= 2:
            self.print_events(events, title=f"Events from {bucket_id}")

        return events
    
    @staticmethod
    def _clean_url(url: str) -> str:
        """Clean URL by removing common prefixes."""
        if url.startswith('http://'):
            url = url[7:]
        elif url.startswith('https://'):
            url = url[8:]
        
        if url.startswith('www.'):
            url = url[4:]
            
        return url
    
    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        return domain if domain else None
    
    def calculate_procrastination_percentage(self, time_window: timedelta = timedelta(minutes=5), debug_level: int = 0) -> Tuple[float, float, float, float]:
        """Calculate procrastination percentages from recent activities.
        
        Args:
            time_window: Time window to analyze
            
        Returns:
            Tuple containing:
            - Procrastination percentage (0-100)
            - Unclear percentage (0-100)
            - Productive percentage (0-100)
            - Active time percentage (0-100)
        """
        # reload rules
        self.categorizer.load_rules()

        all_events = self.get_recent_activities(time_window, debug_level=debug_level)
        if not all_events:
            return 0.0, 0.0, 0.0, 0.0
            
        total_duration = timedelta()
        procrastination_duration = timedelta()
        unclear_duration = timedelta()
        productive_duration = timedelta()

        for event in all_events:
            total_duration += event.duration
            if event.category == ActivityCategory.PROCRASTINATING:
                procrastination_duration += event.duration
            elif event.category == ActivityCategory.UNCLEAR:
                unclear_duration += event.duration
            elif event.category == ActivityCategory.PRODUCTIVE:
                productive_duration += event.duration

        if total_duration.total_seconds() <= 0:
            return 0.0, 0.0, 0.0, 0.0

        return (
            (procrastination_duration.total_seconds() / total_duration.total_seconds()) * 100,
            (unclear_duration.total_seconds() / total_duration.total_seconds()) * 100,
            (productive_duration.total_seconds() / total_duration.total_seconds()) * 100,
            (total_duration / time_window) * 100
        ) 
    
    def print_events(self, events: List, title: str = ""):
        table = Table(title=title)
        table.add_column("Time", justify="right")
        table.add_column("Duration", justify="left")
        table.add_column("Endtime", justify="left")
        table.add_column("", justify="center")
        table.add_column("Bucket", justify="left")
        table.add_column("App", justify="left")
        table.add_column("Title/Language", justify="left")
        table.add_column("URL", justify="left")
        
        for event in events:
            table.add_row(
                event.time_tz,
                event.duration_str,
                (event.timestamp + event.duration).astimezone(tzlocal()).strftime("%H:%M:%S"),
                event.category_str if event.duration > timedelta(seconds=1) else "",
                event.bucket_id_short,
                event.app,
                event.title,
                event.url,
                style="green" if event.category == ActivityCategory.PRODUCTIVE else "red" if event.category == ActivityCategory.PROCRASTINATING else "grey50" if event.duration < timedelta(seconds=1) else ""
            )

        console = Console()
        console.print(table)