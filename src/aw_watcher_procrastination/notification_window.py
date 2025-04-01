"""Notification window UI functionality."""

from typing import Optional
import webbrowser
from datetime import datetime
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCharts import QChart, QPieSeries, QChartView
from PyQt6.QtGui import QPainter, QFont

from .activity_categorizer import ActivityCategorizer, ActivityCategory
from .event_processor import EventProcessor
from .settings import Settings
from .time_utils import format_duration, calculate_end_time

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
        self.settings = Settings()
        
        # Initialize window attributes
        self._browser_window: Optional[QMainWindow] = None
        self._category_editor: Optional[CategoryEditor] = None
        self._last_shown: Optional[datetime] = None

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
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        title = QLabel("Procrastinating?")
        title.setStyleSheet("QLabel { font-size: 24px; font-weight: bold; }")
        main_layout.addWidget(title)

        subtitle = QLabel(f"In the last {self.settings.get('notifications.check_last_seconds')/60:.0f} minutes:")
        subtitle.setStyleSheet("QLabel { font-size: 18px; }")
        main_layout.addWidget(subtitle)
        
        # Create chart container with horizontal layout
        chart_container = QWidget()
        chart_layout = QHBoxLayout()
        chart_container.setLayout(chart_layout)
        
        # Add pie chart
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chart_view.setMinimumHeight(200)  # Set minimum height for better visibility
        chart_layout.addWidget(self.chart_view)
        
        main_layout.addWidget(chart_container)
        
        # Add alert message
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        main_layout.addWidget(self.message_label)
        
        # Add buttons
        chat_button = QPushButton("Get back on track: chat with Procrastination Assistant")
        chat_button.setStyleSheet("QPushButton { color: white; background-color: #28a745; padding: 10px; border-radius: 5px; font-weight: bold; }")
        chat_button.clicked.connect(self._open_chat)
        main_layout.addWidget(chat_button)
        
        close_button = QPushButton("I know what I need and I can do it now, close popup")
        close_button.setStyleSheet("QPushButton { padding: 10px; border-radius: 5px; }")
        close_button.clicked.connect(self._close_window)
        main_layout.addWidget(close_button)
        
        self.edit_button = QPushButton("Edit Activity Categories")
        self.edit_button.setStyleSheet("QPushButton { padding: 10px; border-radius: 5px; }")
        self.edit_button.clicked.connect(self._toggle_category_editor)
        self.edit_button.setDisabled(True)
        main_layout.addWidget(self.edit_button)
        
        # Create category editor panel
        self._category_editor = CategoryEditor(self.event_processor, self.categorizer)
        self._category_editor.hide()
        main_layout.addWidget(self._category_editor)
        
        # Set initial size
        size = self.settings.get("window_sizes.notification.default")
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
        # Check if enough time has passed since last shown
        now = datetime.now()
        if self._last_shown is not None:
            delay_seconds = self.settings.get("delay_showing_popup_again_seconds")
            time_since_last = (now - self._last_shown).total_seconds()
            if time_since_last < delay_seconds:
                print(f"Skipping popup, only {time_since_last:.1f}s since last shown (minimum delay: {delay_seconds}s)")
                return

        # Update pie chart
        series = QPieSeries()
        if prod_pct > 0:
            slice = series.append(f"Productive ({prod_pct:.0f}%)", prod_pct)
            slice.setBrush(Qt.GlobalColor.green)
        if proc_pct > 0:
            slice = series.append(f"Procrastinating ({proc_pct:.0f}%)", proc_pct)
            slice.setBrush(Qt.GlobalColor.red)
        if unclear_pct > 0:
            slice = series.append(f"Unclear ({unclear_pct:.0f}%)", unclear_pct)
            slice.setBrush(Qt.GlobalColor.gray)
            
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Activity Breakdown")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        chart.legend().setFont(QFont("Arial", 10))
        
        self.chart_view.setChart(chart)
        
        # Update last shown time and show window
        self._last_shown = now
        self.show()
        
    def _toggle_category_editor(self) -> None:
        """Toggle the visibility of the category editor panel."""
        if self._category_editor.isHidden():
            # Show category editor
            self._category_editor.show()
            self._category_editor.update_table()
            self.edit_button.setText("Hide Categories")
            
            # Expand window
            size = self.settings.get("window_sizes.notification.expanded")
            self.resize(size["width"], size["height"])
        else:
            # Hide category editor
            self._category_editor.hide()
            self.edit_button.setText("Edit Categories")
            
            # Shrink window
            size = self.settings.get("window_sizes.notification.default")
            self.resize(size["width"], size["height"])
            
        self._center_on_screen()
        
    def _close_window(self) -> None:
        """Safely close the notification window."""
        try:
            if self._browser_window:
                self._browser_window.close()
                self._browser_window = None
            if self._category_editor:
                self._category_editor.hide()
            
            # Start timer from now because we don't want to close window and have it come back fast if it was open a while
            self._last_shown = datetime.now()

            self.hide()  # Hide instead of close to prevent crash
        except Exception as e:
            print(f"Error closing window: {e}")
            self.hide()  # Fallback to just hiding the window
        
    def _open_chat(self) -> None:
        """Open the chat in the default browser."""
        webbrowser.open("https://singular-cendol-4f9273.netlify.app/")
        self._close_window()
        
    def closeEvent(self, event) -> None:
        """Handle window close event.
        
        Args:
            event: Close event
        """
        try:
            self._close_window()
            event.accept()  # Accept the close event
        except:
            event.ignore()  # If something goes wrong, prevent the close

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