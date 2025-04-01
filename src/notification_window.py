"""Notification window UI functionality."""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from src.activity_categorizer import ActivityCategorizer, ActivityCategory
from src.event_processor import EventProcessor
from src.settings import get_setting
from src.time_utils import format_duration, calculate_end_time

class NotificationWindow(QMainWindow):
    """Main notification window for displaying procrastination alerts."""
    
    def __init__(self, event_processor: EventProcessor, categorizer: ActivityCategorizer):
        """Initialize the notification window.
        
        Args:
            event_processor: Event processor instance
            categorizer: Activity categorizer instance
        """
        super().__init__()
        
        self.event_processor = event_processor
        self.categorizer = categorizer
        self.settings = get_setting("window_sizes")
        
        # Initialize window attributes
        self._browser_window: Optional[QMainWindow] = None
        self._category_editor: Optional[CategoryEditor] = None
        
        # Set up the UI
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Procrastination Alert")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create left panel for alert content
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Add alert message
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        left_layout.addWidget(self.message_label)
        
        # Add buttons
        button_layout = QHBoxLayout()
        
        self.edit_button = QPushButton("Edit Categorization")
        self.edit_button.clicked.connect(self._toggle_category_editor)
        button_layout.addWidget(self.edit_button)
        
        self.browser_button = QPushButton("Open Mini Browser")
        self.browser_button.clicked.connect(self._show_mini_browser)
        button_layout.addWidget(self.browser_button)
        
        left_layout.addLayout(button_layout)
        
        # Add left panel to main layout
        main_layout.addWidget(left_panel)
        
        # Create right panel for category editor
        self._category_editor = CategoryEditor(self.event_processor, self.categorizer)
        self._category_editor.hide()
        main_layout.addWidget(self._category_editor)
        
        # Set initial size
        size = self.settings["notification"]["default"]
        self.resize(size["width"], size["height"])
        self._center_on_screen()
        
    def _center_on_screen(self) -> None:
        """Center the window on the screen."""
        frame_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())
        
    def show_alert(self, proc_pct: float, unclear_pct: float, prod_pct: float, active_pct: float) -> None:
        """Show a procrastination alert with the given percentages.
        
        Args:
            proc_pct: Procrastination percentage
            unclear_pct: Unclear activity percentage
            prod_pct: Productive activity percentage
            active_pct: Active time percentage
        """
        message = (
            f"In the last 5 minutes:\n"
            f"• {proc_pct:.1f}% procrastinating\n"
            f"• {unclear_pct:.1f}% unclear\n"
            f"• {prod_pct:.1f}% productive\n"
            f"• {active_pct:.1f}% active time"
        )
        self.message_label.setText(message)
        self.show()
        
    def _toggle_category_editor(self) -> None:
        """Toggle the visibility of the category editor panel."""
        if self._category_editor.isHidden():
            # Show category editor
            self._category_editor.show()
            self._category_editor.update_table()
            self.edit_button.setText("Hide Categorization")
            
            # Expand window
            size = self.settings["notification"]["expanded"]
            self.resize(size["width"], size["height"])
        else:
            # Hide category editor
            self._category_editor.hide()
            self.edit_button.setText("Edit Categorization")
            
            # Shrink window
            size = self.settings["notification"]["default"]
            self.resize(size["width"], size["height"])
            
        self._center_on_screen()
        
    def _show_mini_browser(self) -> None:
        """Show the mini browser window."""
        if not self._browser_window:
            self._browser_window = QMainWindow(self)
            self._browser_window.setWindowTitle("Mini Browser")
            self._browser_window.setWindowFlags(Qt.WindowType.WindowStaysOnTop)
            
            web_view = QWebEngineView()
            web_view.setUrl(QUrl("https://singular-cendol-4f9273.netlify.app/"))
            self._browser_window.setCentralWidget(web_view)
            
            # Set size and position
            size = self.settings["browser"]
            self._browser_window.resize(size["width"], size["height"])
            
            # Center on screen
            frame_geometry = self._browser_window.frameGeometry()
            screen_center = self.screen().availableGeometry().center()
            frame_geometry.moveCenter(screen_center)
            self._browser_window.move(frame_geometry.topLeft())
            
        self._browser_window.show()
        self._browser_window.raise_()
        
    def closeEvent(self, event) -> None:
        """Handle window close event.
        
        Args:
            event: Close event
        """
        if self._browser_window:
            self._browser_window.close()
        super().closeEvent(event)

class CategoryEditor(QWidget):
    """Widget for editing activity categorizations."""
    
    def __init__(self, event_processor: EventProcessor, categorizer: ActivityCategorizer):
        """Initialize the category editor.
        
        Args:
            event_processor: Event processor instance
            categorizer: Activity categorizer instance
        """
        super().__init__()
        self.event_processor = event_processor
        self.categorizer = categorizer
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Add title
        title_label = QLabel("Recent Activities")
        layout.addWidget(title_label)
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Time", "Duration", "End Time", "Gap", "Activity"])
        
        # Set column properties
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        # Enable keyboard navigation
        self.table.setTabKeyNavigation(True)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        layout.addWidget(self.table)
        
        # Add category buttons
        button_layout = QHBoxLayout()
        
        self.productive_button = QPushButton("Mark Productive")
        self.productive_button.clicked.connect(lambda: self._mark_selected(ActivityCategory.PRODUCTIVE))
        button_layout.addWidget(self.productive_button)
        
        self.procrastinating_button = QPushButton("Mark Procrastinating")
        self.procrastinating_button.clicked.connect(lambda: self._mark_selected(ActivityCategory.PROCRASTINATING))
        button_layout.addWidget(self.procrastinating_button)
        
        layout.addLayout(button_layout)
        
    def update_table(self) -> None:
        """Update the table with recent activities."""
        events = self.event_processor.get_recent_activities()
        if not events:
            return
            
        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        self.table.setRowCount(len(events))
        for i, event in enumerate(events):
            # Time column
            time_item = QTableWidgetItem(event.time_tz)
            time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 0, time_item)
            
            # Duration column
            duration_item = QTableWidgetItem(event.duration_str)
            duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 1, duration_item)
            
            # End time column
            end_time = calculate_end_time(event.timestamp, event.duration)
            end_time_item = QTableWidgetItem(end_time.strftime("%H:%M:%S"))
            end_time_item.setFlags(end_time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 2, end_time_item)
            
            # Gap column
            if i < len(events) - 1:
                next_event = events[i + 1]
                gap = next_event.timestamp - end_time
                gap_str = format_duration(gap)
                if gap.total_seconds() < 0:
                    gap_str = f"overlap {gap_str}"
            else:
                gap_str = ""
            gap_item = QTableWidgetItem(gap_str)
            gap_item.setFlags(gap_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 3, gap_item)
            
            # Activity column
            activity_text = f"{event.app}"
            if event.url:
                activity_text += f" - {event.url}"
            if event.title:
                activity_text += f" ({event.title})"
            activity_item = QTableWidgetItem(f"{event.category_str} {activity_text}")
            activity_item.setFlags(activity_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(i, 4, activity_item)
            
    def _mark_selected(self, category: ActivityCategory) -> None:
        """Mark selected activities with the given category.
        
        Args:
            category: Category to mark the activities as
        """
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return
            
        for row in selected_rows:
            activity_item = self.table.item(row, 4)
            if not activity_item:
                continue
                
            activity_text = activity_item.text()
            if not activity_text:
                continue
                
            # Extract activity info (remove emoji prefix if present)
            parts = activity_text.split(" ", 1)
            if len(parts) > 1 and parts[0] in ["✅", "❌", "❓"]:
                activity_text = parts[1]
                
            # Add rules for the activity
            if " - " in activity_text:
                app, rest = activity_text.split(" - ", 1)
                url = rest.split(" (")[0] if " (" in rest else rest
                self.categorizer.add_rule(category, "apps", app.strip())
                self.categorizer.add_rule(category, "urls", url.strip())
            else:
                app = activity_text.split(" (")[0]
                self.categorizer.add_rule(category, "apps", app.strip())
                
        # Update the table to show new categories
        self.update_table() 