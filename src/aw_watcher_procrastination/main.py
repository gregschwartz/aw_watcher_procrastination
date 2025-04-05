"""Main entry point for the ActivityWatch procrastination monitor."""

from math import ceil
import sys
from datetime import timedelta, datetime
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from aw_client import ActivityWatchClient

from .activity_categorizer import ActivityCategorizer
from .event_processor import EventProcessor
from .notification_window import NotificationWindow
from .settings import Settings
# from .updater import ensure_latest_version

def main():
    """Main entry point for the application."""
    print("Starting application...")

    app = QApplication(sys.argv)
    client = ActivityWatchClient("aw-procrastination-monitor")
    client.connect()  # Explicitly connect the client
    
    categorizer = ActivityCategorizer()
    event_processor = EventProcessor(client, categorizer)
    notification_window = NotificationWindow(event_processor, categorizer)
    
    # Load settings
    settings = Settings()
    check_interval = settings.get("notifications.check_interval_seconds")
    procrastination_threshold = settings.get("thresholds.min_procrastination_percent")
    active_threshold = settings.get("thresholds.min_active_percent")

    global debug_level
    debug_level = 1
    
    def check_procrastination():
        """Check for procrastination and show notification if needed."""
        global debug_level
        proc_pct, unclear_pct, prod_pct, active_pct = event_processor.calculate_procrastination_percentage(debug_level=debug_level)
        
        # make ascii stacked bar chart
        print(f"{'😭' * ceil(proc_pct / 2) if proc_pct > 0.1 else ''}{'❓' * ceil(unclear_pct / 2) if unclear_pct > 0.0 else ''}{'👍' * ceil(prod_pct / 2) if prod_pct > 0.1 else ''} -- {proc_pct:.0f}% {unclear_pct:.0f}% {prod_pct:.0f}%")

        if proc_pct >= procrastination_threshold and active_pct >= active_threshold:
            if debug_level >= 1:
                print("Triggering alert")
            notification_window.show_alert(proc_pct, unclear_pct, prod_pct, active_pct)
        elif debug_level >= 2:
            print(f"proc_pct >= procrastination_threshold: {proc_pct >= procrastination_threshold}, active_pct < active_threshold: {active_pct < active_threshold}")

    last_check = datetime.now() - timedelta(days=1) # so it checks immediately
    def check_if_needed():
        """Only perform the check if enough time has passed."""
        nonlocal last_check
        now = datetime.now()
        if (now - last_check).total_seconds() >= check_interval:
            check_procrastination()
            last_check = now
    
    timer = QTimer()
    timer.timeout.connect(check_if_needed)
    timer.start(500)  # Check every 500ms

    def clean_shutdown(signum=None, frame=None):
        """Handle shutdown cleanly and quickly."""
        print("\nShutting down...")
        timer.stop()
        app.quit()
        try:
            client.disconnect()
        except RuntimeError as e:
            print("Error: Client wasn't properly disconnected", e)

        sys.exit(0)

    # Set up signal handling
    signal.signal(signal.SIGINT, clean_shutdown)
    signal.signal(signal.SIGTERM, clean_shutdown)

    # Start the application
    try:
        return app.exec()
    except Exception as e:
        print("Error: Application exited with an error", e)
        clean_shutdown()

if __name__ == "__main__":
    main() 