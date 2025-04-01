"""Main entry point for the ActivityWatch procrastination monitor."""

from math import ceil
import sys
import os
from datetime import timedelta
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QSocketNotifier
from aw_client import ActivityWatchClient

from .activity_categorizer import ActivityCategorizer
from .event_processor import EventProcessor
from .notification_window import NotificationWindow
from .settings import Settings
from .updater import ensure_latest_version

def main():
    """Main entry point for the application."""
    print("Starting application...")

    # Check for updates
    # ensure_latest_version()
    
    app = QApplication(sys.argv)
    client = ActivityWatchClient("aw-procrastination-monitor")
    categorizer = ActivityCategorizer()
    event_processor = EventProcessor(client, categorizer)
    notification_window = NotificationWindow(event_processor, categorizer)
    
    # Load settings
    settings = Settings()
    check_interval = settings.get("notifications.check_interval_seconds")
    procrastination_threshold = settings.get("thresholds.min_procrastination_percent")
    active_threshold = settings.get("thresholds.min_active_percent")
    
    def check_procrastination():
        """Check for procrastination and show notification if needed."""
        proc_pct, unclear_pct, prod_pct, active_pct = event_processor.calculate_procrastination_percentage(debug_level=1)
        
        # make ascii stacked bar chart
        print(f"{'😭' * ceil(proc_pct / 2) if proc_pct > 0.1 else ''}{'❓' * ceil(unclear_pct / 2) if unclear_pct > 0.0 else ''}{'👍' * ceil(prod_pct / 2) if prod_pct > 0.1 else ''} -- {proc_pct:.0f}% {unclear_pct:.0f}% {prod_pct:.0f}%")

        if proc_pct >= procrastination_threshold and active_pct >= active_threshold:
            print("Showing alert")
            notification_window.show_alert(proc_pct, unclear_pct, prod_pct, active_pct)
        else:
            print(f"proc_pct >= procrastination_threshold: {proc_pct >= procrastination_threshold}, active_pct < active_threshold: {active_pct < active_threshold}")


    # Set up timer for periodic checks
    timer = QTimer()
    timer.timeout.connect(check_procrastination)
    timer.start(check_interval * 1000)  # Convert seconds to milliseconds
    print(f"Timer will run every {check_interval} seconds")
    
    # Set up signal handling through Qt
    sn = QSocketNotifier(signal.SIGINT, QSocketNotifier.Type.Exception)
    
    def handle_signal():
        """Handle the signal in Qt's event loop."""
        sn.setEnabled(False)
        print("\nShutting down...")
        client.disconnect()
        os._exit(1)
    
    sn.activated.connect(handle_signal)

    # Run check immediately
    check_procrastination()

    # Start the application
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 