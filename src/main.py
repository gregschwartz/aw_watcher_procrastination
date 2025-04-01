"""Main entry point for the ActivityWatch procrastination monitor."""

from math import ceil
import sys
import os
from datetime import timedelta
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QSocketNotifier
from aw_client import ActivityWatchClient

from src.activity_categorizer import ActivityCategorizer
from src.event_processor import EventProcessor
from src.notification_window import NotificationWindow
from src.settings import get_setting
from src.updater import ensure_latest_version

def main():
    """Main entry point for the application."""
    # Check for updates
    # ensure_latest_version()
    
    app = QApplication(sys.argv)
    client = ActivityWatchClient("aw-procrastination-monitor")
    categorizer = ActivityCategorizer()
    event_processor = EventProcessor(client, categorizer)
    notification_window = NotificationWindow(event_processor, categorizer)
    
    # Load settings
    check_interval = get_setting("check_interval")
    procrastination_threshold = get_setting("procrastination_threshold")
    active_threshold = get_setting("active_threshold")
    
    def check_procrastination():
        """Check for procrastination and show notification if needed."""
        proc_pct, unclear_pct, prod_pct, active_pct = event_processor.calculate_procrastination_percentage(debug_level=1)
        
        # make ascii stacked bar chart
        print(f"{'😭' * ceil(proc_pct / 2) if proc_pct > 0.1 else ''}{'❓' * ceil(unclear_pct / 2) if unclear_pct > 0.0 else ''}{'👍' * ceil(prod_pct / 2) if prod_pct > 0.1 else ''} -- {proc_pct:.0f}% {unclear_pct:.0f}% {prod_pct:.0f}%")

        if proc_pct >= procrastination_threshold and active_pct >= active_threshold:
            notification_window.show_alert(proc_pct, unclear_pct, prod_pct, active_pct)

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
    print("Starting application...")
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 