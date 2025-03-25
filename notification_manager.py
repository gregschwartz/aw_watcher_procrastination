#!/usr/bin/env python3

from datetime import timedelta
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer
import sys
import webbrowser
from typing import Optional

class NotificationWindow(QMainWindow):
    """A custom notification window that appears when procrastination is detected.
    
    This window shows a friendly message and provides options to either:
    1. Chat with the bot for guidance
    2. Dismiss the notification
    """
    
    def __init__(self, title: str, message: str, chat_url: str):
        """Initialize the notification window.
        
        Args:
            title: The window title
            message: The main message to display
            chat_url: URL to open when the chat button is clicked
        """
        super().__init__()
        
        # Store the chat URL
        self._chat_url = chat_url
        
        # Configure window properties
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add message label
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(message_label)
        
        # Add chat button
        chat_button = QPushButton("Chat with the bot to choose what to do next")
        chat_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        chat_button.clicked.connect(self._open_chat)
        layout.addWidget(chat_button)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        close_button.clicked.connect(self._handle_close)
        layout.addWidget(close_button)
        
        # Set fixed size
        self.setFixedSize(400, 200)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )
    
    def _handle_close(self):
        """Handle window closing and cleanup."""
        self.close()
        # Get the Qt application instance
        app = QApplication.instance()
        if app:
            # Exit the event loop if it's running
            app.quit()

    def _open_chat(self):
        """Open the chat URL in the default browser and close the window."""
        webbrowser.open(self._chat_url)
        self._handle_close()

class NotificationManager:
    """Manages system notifications and popup windows for the procrastination monitor."""
    
    def __init__(self):
        """Initialize the notification manager.
        
        Args:
            chat_url: The URL to open when the chat button is clicked
        """
        self._app: Optional[QApplication] = None
        self._window: Optional[NotificationWindow] = None
        self._chat_url = "https://singular-cendol-4f9273.netlify.app/"
        
        # Initialize Qt application if needed
        if not QApplication.instance():
            self._app = QApplication(sys.argv)
            print("Qt application initialized")
        
        print("Notification manager ready")
    
    def show_procrastination_alert(self, procrastination_pct: float, unclear_pct: float, productive_pct: float, active_pct: float):
        """Show a notification when procrastination percentage is too high.
        
        Args:
            procrastination_pct: The current procrastination percentage
            unclear_pct: The current unclear percentage
            productive_pct: The current productive percentage
            active_pct: The current active percentage
        """
        # Don't show if conditions aren't met or if a window is already showing
        if procrastination_pct <= 60 or active_pct <= 70:
            return
            
        if self._window and self._window.isVisible():
            print("Notification window already showing, skipping new alert")
            return
            
        title = "Getting off track? 🤔"
        message = (
            f"I notice you've spent {procrastination_pct:.0f}% of the last few minutes "
            "on non-productive activities. Would you like some help getting back on track?"
        )
        
        # Create and show the notification window
        self._window = NotificationWindow(title, message, self._chat_url)
        self._window.show()
        
        # Create a timer to automatically close the window after 30 seconds
        QTimer.singleShot(30000, self._window._handle_close)
        
        # Run event loop until window is closed
        if self._app:
            self._app.exec()

# for testing
if __name__ == "__main__":
    notification_manager = NotificationManager()
    notification_manager.show_procrastination_alert(69, 0, 0, 100)
    # Keep the application running until window is closed
    notification_manager.run_event_loop()
