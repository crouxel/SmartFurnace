import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QMenu, QAction, QSizePolicy, QMessageBox, QComboBox)
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QSize
from datetime import datetime, timedelta
import pyqtgraph as pg
from custom_combobox import CustomComboBox
from styles import (get_label_style, get_temp_display_style, get_button_style, 
                   get_combo_style, get_time_label_style, get_plot_theme, 
                   ThemeManager, get_theme_dependent_styles, get_message_box_style)
from database import DatabaseManager
from options_dialog import OptionsDialog
from constants import (WINDOW_SIZE, BUTTON_WIDTH, COMBO_WIDTH, 
                      PLOT_UPDATE_INTERVAL, MAX_PLOT_POINTS, 
                      DEFAULT_TEMP, ERROR_MESSAGES)
import platform
import logging
from schedule_window import schedule_window

logger = logging.getLogger(__name__)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Initialize database
        DatabaseManager.initialize_database()
        self.setGeometry(100, 100, *WINDOW_SIZE)
        ThemeManager.initialize()  # Initialize theme from saved settings
        self.start_cycle_time = None
        self.current_schedule = []
        
        # Add these lines to load the first schedule by default
        schedules = DatabaseManager.fetch_all_schedules()
        if schedules:
            self.load_schedule(schedules[0])  # Load the first available schedule
        
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        # Define font family based on OS
        if platform.system() == 'Windows':
            font_family = 'Segoe UI'
        elif platform.system() == 'Darwin':  # macOS
            font_family = 'SF Pro'
        else:  # Linux and others
            font_family = 'Ubuntu'

        # Load the Orbitron font
        font_id = QFontDatabase.addApplicationFont("OrbitronFont.ttf")
        if font_id == -1:
            print("Failed to load Orbitron font")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        self.start_button = QPushButton("Start Cycle")
        self.combo = CustomComboBox()
        self.label = QLabel()
        self.label.setStyleSheet(get_label_style())
        self.plot_widget = pg.PlotWidget()

        # Setup layouts
        top_layout = self.setup_top_layout()
        temp_display_layout, self.temp_display = self.setup_temp_display(font_family)
        main_layout = self.setup_main_layout(top_layout, temp_display_layout)

        self.setLayout(main_layout)

        # Set up a timer to update the graph every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(1000)

        # Initial update to display the current temperature immediately
        self.update_graph()

    def setup_top_layout(self):
        """Set up the top layout with controls."""
        top_layout = QHBoxLayout()
        
        # Create start button with fixed width
        self.start_button = QPushButton("Start Cycle")
        self.start_button.setFixedWidth(BUTTON_WIDTH)
        self.start_button.setStyleSheet(get_button_style(embossed=True))
        self.start_button.clicked.connect(self.write_start_cycle_time)
        
        # Add start button to the left
        top_layout.addWidget(self.start_button)
        
        # Add stretch to push everything else to the right
        top_layout.addStretch()
        
        # Add Profile label
        profile_label = QLabel("Profile:")
        theme = ThemeManager.get_current_theme()
        profile_label.setStyleSheet(f"color: {theme['primary']}; font-weight: bold;")
        top_layout.addWidget(profile_label)
        
        # Add some spacing between label and combo
        top_layout.addSpacing(10)
        
        # Create combo box with smaller fixed width
        self.combo = CustomComboBox(self)
        self.combo.setFixedWidth(COMBO_WIDTH)
        self.combo.setStyleSheet(get_combo_style(embossed=True))
        
        # Set up combo box items and connection
        schedules = DatabaseManager.fetch_all_schedules()
        print(f"Available schedules: {schedules}")  # Debug print
        self.combo.addItems(schedules)
        self.combo.insertSeparator(len(schedules))
        self.combo.addItem("Add Schedule")
        self.combo.currentIndexChanged.connect(self.on_table_select)
        
        # Add combo box
        top_layout.addWidget(self.combo)
        
        return top_layout

    def setup_temp_display(self, font_family):
        temp_display = QLabel("---°C")
        temp_display.setAlignment(Qt.AlignCenter)
        temp_display.setFixedWidth(250)  # Increased width
        temp_display.setStyleSheet(get_temp_display_style(font_family=font_family))
        
        temp_display_layout = QHBoxLayout()
        temp_display_layout.addStretch()  # Add stretch before
        temp_display_layout.addWidget(temp_display)
        temp_display_layout.addStretch()  # Add stretch after
        
        return temp_display_layout, temp_display

    def setup_main_layout(self, top_layout, temp_display_layout):
        main_layout = QVBoxLayout()
        
        # Add time information layout
        time_info_layout = QHBoxLayout()
        self.start_time_label = QLabel("Start: --:--:--")
        self.end_time_label = QLabel("End: --:--:--")
        
        # Apply time label styles
        self.start_time_label.setStyleSheet(get_time_label_style())
        self.end_time_label.setStyleSheet(get_time_label_style())
        
        time_info_layout.addWidget(self.start_time_label)
        time_info_layout.addStretch()
        time_info_layout.addWidget(self.end_time_label)
        
        # Setup plot widget
        plot_widget = self.setup_plot_widget()
        
        main_layout.addLayout(top_layout)
        main_layout.addLayout(temp_display_layout)
        main_layout.addLayout(time_info_layout)
        main_layout.addWidget(self.label)
        main_layout.addWidget(plot_widget)
        
        # Add options button with SVG icon
        options_layout = QHBoxLayout()
        options_layout.addStretch()
        
        options_button = QPushButton()
        icon = QIcon("gear-icon.svg")  # Make sure this matches your file name exactly
        options_button.setIcon(icon)
        options_button.setIconSize(QSize(24, 24))  # Set icon size
        options_button.setFixedSize(32, 32)
        options_button.setToolTip("Options")  # Add tooltip
        options_button.clicked.connect(self.show_options)
        options_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }
        """)
        
        options_layout.addWidget(options_button)
        main_layout.addLayout(options_layout)
        
        return main_layout

    def setup_plot_widget(self):
        # Configure plot appearance
        theme = get_plot_theme()
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(theme['background'])
        
        # Style the plot
        plot_item = self.plot_widget.getPlotItem()
        
        # Configure axes with proper grid
        for axis in ['bottom', 'left']:
            axis_item = plot_item.getAxis(axis)
            axis_item.setPen(pg.mkPen(color=theme['axis'], width=1))
            axis_item.setTextPen(theme['text'])
            # Convert hex grid color to RGB tuple for proper grid handling
            grid_color = pg.mkColor(theme['grid'])
            axis_item.setGrid(50)  # Alpha value for grid
            
        # Show grids with proper styling
        plot_item.showGrid(x=True, y=True, alpha=0.5)
        
        # Set labels with proper styling
        plot_item.setLabel('left', text='Temperature', units='°C', 
                          color=theme['text'], font={'size': '12pt'})
        plot_item.setLabel('bottom', text='Time', 
                          color=theme['text'], font={'size': '12pt'})
        
        # Style the legend if needed
        plot_item.addLegend(offset=(-10, 10))
        
        return self.plot_widget

    def update_schedule_menu(self):
        """Update the schedule selector menu."""
        current_text = self.combo.currentText()
        self.combo.clear()
        schedules = DatabaseManager.fetch_all_schedules()
        self.combo.addItems(schedules)
        self.combo.insertSeparator(len(schedules))
        self.combo.addItem("Add Schedule")
        if current_text in schedules:
            self.combo.setCurrentText(current_text)
        else:
            self.combo.setCurrentIndex(0)

    def write_start_cycle_time(self):
        self.start_cycle_time = datetime.now()
        with open('start_cycle_time.txt', 'w') as f:
            f.write(self.start_cycle_time.isoformat())

    def get_start_cycle_time(self):
        if self.start_cycle_time is None:
            try:
                with open('start_cycle_time.txt', 'r') as f:
                    self.start_cycle_time = datetime.fromisoformat(f.read().strip())
            except FileNotFoundError:
                self.start_cycle_time = datetime.now()
        return self.start_cycle_time

    def update_graph(self):
        """Update the graph with current temperature and schedule."""
        try:
            # Clear the plot
            self.plot_widget.clear()
            
            # Get current time and temperature
            current_time = datetime.now()
            
            if self.current_schedule and self.start_cycle_time:
                # Plot schedule
                x_data = []
                y_data = []
                current_time_minutes = 0
                
                # Plot schedule data
                for cycle in self.current_schedule:
                    cycle_time_minutes = self.time_to_minutes(cycle['CycleTime'])
                    x_data.extend([current_time_minutes, current_time_minutes + cycle_time_minutes])
                    y_data.extend([cycle['StartTemp'], cycle['EndTemp']])
                    current_time_minutes += cycle_time_minutes
                
                # Plot the schedule line
                self.plot_widget.plot(x_data, y_data, pen={'color': 'g', 'width': 2})
                
                # Add vertical line for current time if cycle has started
                if self.start_cycle_time:
                    elapsed_minutes = (current_time - self.start_cycle_time).total_seconds() / 60
                    self.plot_widget.addLine(x=elapsed_minutes, pen={'color': 'y', 'width': 2, 'style': Qt.DashLine})
                
                # Update temperature display
                current_temp = self.get_current_temperature(elapsed_minutes)
                if current_temp is not None:
                    self.temp_display.setText(f"{current_temp:.1f}°C")
                
        except Exception as e:
            print(f"Error updating graph: {e}")

    def get_current_temperature(self, elapsed_time):
        """Get the current temperature based on elapsed time."""
        if not self.current_schedule:
            return None
        
        current_time = 0
        for cycle in self.current_schedule:
            cycle_time = self.time_to_minutes(cycle['CycleTime'])
            if current_time <= elapsed_time <= (current_time + cycle_time):
                # Calculate progress through current cycle
                cycle_progress = (elapsed_time - current_time) / cycle_time
                start_temp = cycle['StartTemp']
                end_temp = cycle['EndTemp']
                # Linear interpolation
                return start_temp + (end_temp - start_temp) * cycle_progress
            current_time += cycle_time
        return None

    def time_to_minutes(self, time_str):
        """Convert HH:MM:SS to minutes."""
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 60 + m + s / 60
        except Exception as e:
            print(f"Error converting time: {e}")
            return 0

    def on_table_select(self):
        """Handle schedule selection from combo box."""
        selected_table = self.combo.currentText()
        logger.debug(f"on_table_select called with: {selected_table}")
        
        if selected_table == "Add Schedule":
            try:
                logger.debug("Opening schedule_window in Add mode")
                self.schedule_window = schedule_window(self)
                logger.debug("Created schedule_window instance")
                if self.schedule_window.exec_():
                    logger.debug("Schedule window accepted, updating menu")
                    self.update_schedule_menu()
                else:
                    logger.debug("Schedule window cancelled")
            except Exception as e:
                logger.error(f"Error in on_table_select: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to open schedule window: {str(e)}")
        else:
            logger.debug(f"Loading existing schedule: {selected_table}")
            self.load_schedule(selected_table)

    def show_context_menu(self, position):
        """Show context menu for schedule operations."""
        current_text = self.combo.currentText()
        if current_text and current_text != "Add Schedule":
            menu = QMenu()
            edit_action = menu.addAction("Edit")
            delete_action = menu.addAction("Delete")
            
            action = menu.exec_(self.combo.mapToGlobal(position))
            
            if action == edit_action:
                self.edit_schedule()
            elif action == delete_action:
                self.delete_schedule()

    def delete_schedule(self):
        """Delete the currently selected schedule."""
        schedule_name = self.combo.currentText()
        if schedule_name and schedule_name != "Add Schedule":
            if DatabaseManager.delete_schedule(schedule_name):
                self.show_message("Success", "Schedule deleted successfully")
                self.update_schedule_menu()

    def edit_schedule(self):
        """Edit the currently selected schedule."""
        schedule_name = self.combo.currentText()
        logger.debug(f"edit_schedule called for: {schedule_name}")
        
        if schedule_name and schedule_name != "Add Schedule":
            try:
                logger.debug(f"Opening schedule_window in Edit mode for: {schedule_name}")
                self.schedule_window = schedule_window(self, schedule_name)
                
                if self.schedule_window.exec_():
                    logger.debug("Schedule edit accepted, updating UI")
                    self.update_schedule_menu()
                    self.combo.setCurrentText(schedule_name)
                    self.load_schedule(schedule_name)
                else:
                    logger.debug("Schedule edit cancelled")
                    
            except Exception as e:
                logger.error(f"Exception in edit_schedule: {str(e)}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to edit schedule: {str(e)}")

    def show_options(self):
        dialog = OptionsDialog(self)
        dialog.exec_()

    def apply_theme(self):
        theme = ThemeManager.get_current_theme()
        # Set main window background
        self.setStyleSheet(f"background-color: {theme['background']};")
        
        # Update all themed components
        styles = get_theme_dependent_styles()
        
        # Apply styles to components
        self.start_button.setStyleSheet(styles['button'])
        self.combo.setStyleSheet(styles['combo'])
        self.temp_display.setStyleSheet(styles['temp_display'])
        
        # Update plot theme
        self.plot_widget.setBackground(theme['background'])
        self.plot_widget.getAxis('bottom').setPen(theme['grid'])
        self.plot_widget.getAxis('left').setPen(theme['grid'])

    def load_schedule(self, schedule_name):
        """Load a schedule and update the display."""
        logger.debug(f"Loading schedule: {schedule_name}")
        try:
            self.current_schedule = []
            data = DatabaseManager.load_schedule(schedule_name)
            logger.debug(f"Loaded data from database: {data}")
            
            if data:
                for row in data:
                    logger.debug(f"Processing row: {row}")
                    cycle = {
                        'CycleType': row['CycleType'],
                        'StartTemp': float(row['StartTemp']),
                        'EndTemp': float(row['EndTemp']),
                        'CycleTime': row['CycleTime']
                    }
                    logger.debug(f"Created cycle: {cycle}")
                    self.current_schedule.append(cycle)
                
                logger.debug("Getting start cycle time")
                self.start_cycle_time = self.get_start_cycle_time()
                logger.debug(f"Start cycle time: {self.start_cycle_time}")
                
                logger.debug("Updating graph")
                self.update_graph()
                return True
        except Exception as e:
            logger.error(f"Error loading schedule: {e}", exc_info=True)
            return False

    def setup_schedule_selector(self):
        """Set up the schedule selector combo box."""
        self.combo = CustomComboBox(self)
        self.combo.setFixedWidth(COMBO_WIDTH)
        self.combo.setStyleSheet(get_combo_style(embossed=True))
        self.combo.setContextMenuPolicy(Qt.CustomContextMenu)
        self.combo.customContextMenuRequested.connect(self.show_context_menu)
        self.update_schedule_menu()

    def on_combo_activated(self, text):
        """Handle combo box selection."""
        if text == "Add Schedule":
            try:
                self.schedule_window = schedule_window(self)  # Create new window
                self.schedule_window.exec_()  # Show modal dialog
            except Exception as e:
                logger.error(f"Failed to open schedule window: {e}")
                QMessageBox.critical(self, "Error", f"Failed to open schedule window: {str(e)}")

    def show_message(self, title: str, message: str, icon=QMessageBox.Information):
        """Show a themed message box."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.setStyleSheet(get_message_box_style())
        return msg.exec_()

    def load_last_schedule(self):
        """Load the last opened schedule on startup."""
        last_schedule = self.settings.value('last_schedule', '')
        if last_schedule:
            self.load_schedule(last_schedule)
            # Remove redundant update_graph() call since load_schedule() already calls it

def fetch_schedule_data(table_name):
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT CycleType, StartTemp, EndTemp, CycleTime, Notes FROM {table_name}")
        schedule_data = cursor.fetchall()
        conn.close()
        return schedule_data
    except sqlite3.OperationalError as e:
        print(f"Error fetching schedule data: {e}")
        return []

# Initialize the QApplication instance
app = QApplication(sys.argv)

# Initialize database
DatabaseManager.initialize_database()

# Create and show the main window
window = MainWindow()
window.show()

sys.exit(app.exec_())