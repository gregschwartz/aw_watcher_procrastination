"""Notification window UI functionality."""

from typing import Optional
import webbrowser
from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QMargins, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QInputDialog
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCharts import QChart, QPieSeries, QChartView
from PyQt6.QtGui import QPainter, QFont, QIcon

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
        super().__init__(None)  # No parent
        
        self.event_processor = event_processor
        self.categorizer = categorizer
        self.settings = Settings()
        
        # Initialize window attributes
        self._browser_window: Optional[QMainWindow] = None
        self._category_editor: Optional[CategoryEditor] = None
        self._last_shown: Optional[datetime] = None
        
        self._break_end_time: Optional[datetime] = None
        self._break_duration_minutes: Optional[int] = None

        # Set up the UI
        self._init_ui()
        
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("Procrastination Alert")

        # Set window flags for proper behavior on macOS
        self.setWindowFlags(
            Qt.WindowType.Dialog |  # Dialog window (no taskbar/dock entry)
            Qt.WindowType.WindowStaysOnTopHint |  # Keep on top
            Qt.WindowType.CustomizeWindowHint |  # Custom window hints
            Qt.WindowType.WindowTitleHint |  # Show title bar
            Qt.WindowType.WindowCloseButtonHint  # Show close button
        )
        
        # Set window attributes
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)  # Don't activate when shown
        # Cursor, FYI: WA_AlwaysShowToolWindow DOES NOT EXIST! WA_MacAlwaysShowToolWindow does
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow, False)  # Don't show in dock
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        title = QLabel("Are you being productive?")
        title.setStyleSheet("QLabel { font-size: 24px; font-weight: bold; }")
        main_layout.addWidget(title)

        subtitle = QLabel(f"You've spent the last {self.settings.get('notifications.check_last_seconds')/60:.0f} minutes:")
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
        
        # Remove margins from chart container layout for better space usage
        chart_layout.setContentsMargins(0, 0, 0, 0)
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
        
        break_button = QPushButton("I'm taking a break")
        break_button.setStyleSheet("QPushButton { padding: 10px; border-radius: 5px; }")
        break_button.clicked.connect(self._show_break_dialog)
        main_layout.addWidget(break_button)
        
        # self.edit_button = QPushButton("Edit Activity Categories")
        # self.edit_button.setStyleSheet("QPushButton { padding: 10px; border-radius: 5px; }")
        # self.edit_button.clicked.connect(self._toggle_category_editor)
        # self.edit_button.setDisabled(True)
        # main_layout.addWidget(self.edit_button)
        
        # Set tab order for keyboard navigation
        chat_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        close_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        break_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        # self.edit_button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set initial focus to chat button
        chat_button.setFocus()
        
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
        
    def show_alert(self, proc_pct: float, unclear_pct: float, prod_pct: float, active_pct: float, debug_level: int = 0) -> None:
        """Show a procrastination alert with the given percentages.
        
        Args:
            proc_pct: Procrastination percentage
            unclear_pct: Unclear activity percentage
            prod_pct: Productive activity percentage
            active_pct: Active time percentage
        """
        now = datetime.now()
        
        # Check if break is over and show welcome back dialog if needed
        if self._break_end_time:
            if now >= self._break_end_time:
                self._show_welcome_back_dialog()
                return
            else:
                if debug_level >= 1:
                    print(f"Skipping popup, on break. Current time: {now}, break ends at {self._break_end_time}")
                return
            
        # Check if enough time has passed since last shown
        if self._last_shown is not None:
            delay_seconds = self.settings.get("delay_showing_popup_again_seconds")
            time_since_last = (now - self._last_shown).total_seconds()
            if time_since_last < delay_seconds:
                if debug_level >= 1:
                    print(f"Skipping popup, only {time_since_last:.1f}s since last shown (minimum delay: {delay_seconds}s)")
                return

        # Update pie chart
        series = QPieSeries()
        if proc_pct > 0:
            slice = series.append(f"{proc_pct:.0f}% Procrastinating", proc_pct)
            slice.setBrush(Qt.GlobalColor.red)
        if prod_pct > 0:
            slice = series.append(f"{prod_pct:.0f}% Productive", prod_pct)
            slice.setBrush(Qt.GlobalColor.darkGreen)
        if unclear_pct > 0:
            slice = series.append(f"{unclear_pct:.0f}% Unclear", unclear_pct)
            slice.setBrush(Qt.GlobalColor.darkGray)
            
        chart = QChart()
        chart.addSeries(series)
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignLeft)
        chart.legend().setFont(QFont("Arial", 18))
        
        # Minimize margins while keeping some spacing for readability
        chart.setMargins(QMargins(5, 5, 5, 5))
        series.setHoleSize(0.0)
        series.setPieSize(0.8)
        
        # # Set chart title font
        # title_font = QFont("Arial", 14)
        # title_font.setBold(False)
        # chart.setTitleFont(title_font)

        self.chart_view.setChart(chart)
        
        # Update last shown time and show window
        self._last_shown = now
        self.show()

    def _show_welcome_back_dialog(self) -> None:
        """Show a welcome back dialog when returning from a break."""
        # Clear break state first so we have the duration for the message
        duration = self._break_duration_minutes
        self._break_end_time = None
        self._break_duration_minutes = None

        dialog = QDialog(self)
        dialog.setWindowTitle("Welcome Back!")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Add welcome message
        welcome_label = QLabel(f"Hope you had a great {duration} minute break!")
        welcome_label.setStyleSheet("QLabel { font-size: 24px; font-weight: bold; }")
        layout.addWidget(welcome_label)

        ready_label = QLabel("Ready to get back to work?")
        ready_label.setStyleSheet("QLabel { font-size: 18px; }")
        layout.addWidget(ready_label)

        # Add buttons
        chat_button = QPushButton("Need help getting started? Chat with Procrastination Assistant")
        chat_button.setStyleSheet("QPushButton { color: white; background-color: #28a745; padding: 10px; border-radius: 5px; font-weight: bold; }")
        chat_button.clicked.connect(lambda: [dialog.close(), self._open_chat()])
        layout.addWidget(chat_button)

        ready_button = QPushButton("I'm ready to work!")
        ready_button.setStyleSheet("QPushButton { padding: 10px; border-radius: 5px; background-color: #28a745; }")
        ready_button.clicked.connect(lambda: [dialog.close(), self._close_window()])
        layout.addWidget(ready_button)

        more_break_button = QPushButton("I need more break time...")
        more_break_button.setStyleSheet("QPushButton { padding: 10px; border-radius: 5px; }")
        more_break_button.clicked.connect(lambda: [dialog.close(), self._show_break_dialog()])
        layout.addWidget(more_break_button)

        dialog.exec()

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
        
    def _show_break_dialog(self) -> None:
        """Show dialog for selecting break duration."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Take a Break")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Calculate end of day (4am tomorrow)
        now = datetime.now()
        tomorrow_4am = (now + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
        rest_of_day_minutes = int((tomorrow_4am - now).total_seconds() / 60)

        # Create buttons for predefined durations
        durations = [
            ("5 minutes", 5),
            ("10 minutes", 10),
            ("15 minutes", 15),
            ("30 minutes", 30),
            (f"Rest of the day", rest_of_day_minutes)
        ]

        for label, minutes in durations:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, m=minutes: self._take_break(m, dialog))
            layout.addWidget(btn)

        # Add custom time input directly in dialog
        custom_btn = QPushButton("Enter exact time")
        custom_btn.clicked.connect(lambda: self._handle_custom_time(dialog))
        layout.addWidget(custom_btn)

        dialog.exec()

    def _handle_custom_time(self, dialog: QDialog) -> None:
        """Handle custom time input.
        
        Args:
            dialog: Parent dialog to close
        """
        custom_minutes, ok = QInputDialog.getInt(
            self, "Enter Break Duration",
            "Enter break duration in minutes:",
            min=1, max=24*60  # Max 24 hours
        )
        if ok:
            self._take_break(custom_minutes, dialog)

    def _take_break(self, minutes: int, dialog: QDialog) -> None:
        """Take a break for the specified duration.
        
        Args:
            minutes: Break duration in minutes
            dialog: Dialog to close
        """
        self._break_duration_minutes = minutes
        self._break_end_time = datetime.now() + timedelta(minutes=minutes)
        dialog.close()
        self._close_window()

    def closeEvent(self, event) -> None:
        """Handle window close event. Prevents the window from being destroyed by
        hiding it instead, which allows it to be shown again later.
        
        Args:
            event: Close event from Qt
        """
        try:
            self._close_window()
            event.accept()  # Accept the close event
            event.ignore()
        except:
            pass

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