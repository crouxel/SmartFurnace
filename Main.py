import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QMenu, QAction, QSizePolicy)
from PyQt5.QtGui import QIcon, QFontDatabase
from PyQt5.QtCore import Qt, QTimer, QSize
from datetime import datetime, timedelta
import pyqtgraph as pg
from custom_combobox import CustomComboBox
from styles import (get_label_style, get_temp_display_style, get_button_style, 
                   get_combo_style, get_time_label_style, get_plot_theme, 
                   ThemeManager, get_theme_dependent_styles)
from database import fetch_all_schedules
from options_dialog import OptionsDialog

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        ThemeManager.initialize()  # Initialize theme from saved settings
        self.start_cycle_time = None
        self.current_schedule = []
        self.init_ui()
        self.apply_theme()  # Make sure we call this

    def init_ui(self):
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
        top_layout = QHBoxLayout()
        
        # Create start button with fixed width
        self.start_button = QPushButton("Start Cycle")
        self.start_button.setFixedWidth(100)  # Set fixed width
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
        self.combo.setFixedWidth(150)  # Reduced width
        self.combo.setStyleSheet(get_combo_style(embossed=True))
        self.combo.addItems(fetch_all_schedules() + ["Add Schedule"])
        self.combo.currentIndexChanged.connect(self.on_table_select)
        
        # Create and set the context menu
        menu = QMenu(self)
        edit_action = QAction("Edit Schedule", self)
        delete_action = QAction("Delete Schedule", self)
        
        edit_action.triggered.connect(lambda: self.open_edit_table_window(self.combo.currentText()))
        delete_action.triggered.connect(lambda: self.delete_table(self.combo.currentText()))
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        self.combo.set_context_menu(menu)
        
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
        current_text = self.combo.currentText()
        self.combo.clear()
        schedules = fetch_all_schedules()
        self.combo.addItems(schedules)
        self.combo.insertSeparator(len(schedules))
        self.combo.addItem("Add Schedule")
        if current_text in schedules:
            self.combo.setCurrentText(current_text)  # Reselect the previously selected schedule
        else:
            self.combo.setCurrentIndex(0)  # Select the first valid schedule

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
        if self.start_cycle_time is None:
            self.start_cycle_time = self.get_start_cycle_time()

        elapsed_time = (datetime.now() - self.start_cycle_time).total_seconds() / 60
        self.plot_widget.clear()
        
        theme = get_plot_theme()
        self.regenerate_graph()
        
        # Add current time line with updated style
        self.plot_widget.addLine(
            x=elapsed_time, 
            pen=pg.mkPen(theme['current_time'], width=2, style=Qt.DashLine)
        )

        # Update temperature display
        current_temp = self.get_current_temperature(elapsed_time)
        self.temp_display.setText(f"{current_temp:03d}°C")

        # Update time labels with AM/PM
        if self.current_schedule:
            start_time = self.get_start_cycle_time()
            total_duration = sum(cycle['CycleTime'] for cycle in self.current_schedule)
            end_time = start_time + timedelta(minutes=total_duration)
            
            self.start_time_label.setText(f"Start: {start_time.strftime('%I:%M:%S %p')}")
            self.end_time_label.setText(f"End: {end_time.strftime('%I:%M:%S %p')}")

    def get_current_temperature(self, elapsed_time):
        if not self.current_schedule:
            return 0  # Return 0 if no schedule is loaded
        
        # Get the first cycle's start temperature for times before the first cycle
        if elapsed_time < self.current_schedule[0]['Cycle']:
            return self.current_schedule[0]['StartTemp']
        
        for cycle in self.current_schedule:
            cycle_start = cycle['Cycle']
            cycle_end = cycle_start + cycle['CycleTime']
            if cycle_start <= elapsed_time <= cycle_end:
                # Linear interpolation between start and end temperature
                start_temp = cycle['StartTemp']
                end_temp = cycle['EndTemp']
                temp = start_temp + (end_temp - start_temp) * (elapsed_time - cycle_start) / (cycle_end - cycle_start)
                return int(temp)
        
        # If we're past the last cycle, return the last cycle's end temperature
        if self.current_schedule and elapsed_time > cycle_end:
            return self.current_schedule[-1]['EndTemp']
        
        return 0  # Default temperature if not found

    def regenerate_graph(self):
        selected_table = self.combo.currentText()
        try:
            schedule, times, temps, min_temp, max_temp = load_schedule(selected_table)
            if schedule is None:
                return

            self.current_schedule = schedule
            theme = get_plot_theme()

            # Plot temperature curve with enhanced styling
            self.plot_widget.plot(
                times, 
                temps, 
                pen=pg.mkPen(
                    color=theme['curve'],
                    width=3,
                    style=Qt.SolidLine
                ),
                symbol='o',  # Add points at each vertex
                symbolSize=8,
                symbolBrush=theme['curve'],
                symbolPen=None,  # No border on points
                name='Temperature Schedule'
            )

            # Set axis ranges with padding
            y_padding = (max_temp - min_temp) * 0.1  # 10% padding
            self.plot_widget.setXRange(0, times[-1])
            self.plot_widget.setYRange(min_temp - y_padding, max_temp + y_padding)

            # Update X-axis with HH:MM format
            if times and self.start_cycle_time:
                start_time = self.start_cycle_time
                x_ticks = []
                for t in times:
                    tick_time = start_time + timedelta(minutes=t)
                    x_ticks.append((t, tick_time.strftime('%H:%M')))
                
                self.plot_widget.getAxis('bottom').setTicks([x_ticks])

            # Ensure grid is visible
            self.plot_widget.getPlotItem().showGrid(x=True, y=True, alpha=0.5)

        except Exception as e:
            print(f"Error in regenerate_graph: {e}")

    def on_table_select(self):
        selected_table = self.combo.currentText()
        if selected_table == "Add Schedule":
            self.open_add_table_window()
        else:
            self.label.setText(f"Selected table: {selected_table}")
            self.regenerate_graph()

    def show_context_menu(self):
        print("Creating context menu")
        menu = QMenu(self.combo)  # Set combo as parent
        menu.setStyleSheet(get_combo_style())
        
        edit_action = QAction("Edit Schedule", menu)
        delete_action = QAction("Delete Schedule", menu)
        
        edit_action.triggered.connect(lambda: self.open_edit_table_window(self.combo.currentText()))
        delete_action.triggered.connect(lambda: self.delete_table(self.combo.currentText()))
        
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        
        print("Menu created with actions")
        return menu

    def open_edit_table_window(self, table_name):
        from schedule_window import ScheduleWindow  # Import here to avoid circular import
        # Fetch the schedule data for the selected table
        schedule_data = fetch_schedule_data(table_name)
        edit_window = ScheduleWindow(table_name, schedule_data, parent=self)
        edit_window.exec_()
        self.update_schedule_menu()
        self.combo.setCurrentText(table_name)  # Ensure the combo box stays on the same schedule

    def open_add_table_window(self):
        from schedule_window import ScheduleWindow  # Import here to avoid circular import
        add_window = ScheduleWindow(parent=self)
        add_window.exec_()
        self.update_schedule_menu()
        self.combo.setCurrentIndex(0)  # Select the first valid schedule

    def delete_table(self, table_name):
        try:
            conn = sqlite3.connect('SmartFurnace.db')
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            conn.commit()
            conn.close()
            print(f"Table {table_name} deleted successfully.")
            self.update_schedule_menu()
        except sqlite3.OperationalError as e:
            print(f"Error deleting table {table_name}: {e}")

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

def load_schedule(selected_table):
    global current_schedule
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f"PRAGMA table_info({selected_table})")
        columns = {row[1]: index for index, row in enumerate(cursor.fetchall())}
        
        cursor.execute(f"SELECT * FROM {selected_table}")
        cycles = cursor.fetchall()
        conn.close()

        times = []
        temps = []
        total_time = 0
        min_temp = float('inf')
        max_temp = float('-inf')
        current_schedule = []

        for cycle in cycles:
            cycle_dict = {
                'Id': cycle[columns['Id']],
                'Cycle': cycle[columns['Cycle']],
                'StartTemp': cycle[columns['StartTemp']],
                'EndTemp': cycle[columns['EndTemp']],
                'CycleType': cycle[columns['CycleType']],
                'CycleTime': cycle[columns['CycleTime']],
                'Notes': cycle[columns['Notes']]
            }

            try:
                # Parse the time string into a datetime object
                cycle_time = datetime.strptime(cycle_dict['CycleTime'], "%H:%M:%S")
                
                # Calculate total minutes
                cycle_time_minutes = cycle_time.hour * 60 + cycle_time.minute + cycle_time.second / 60
                
                # Update min and max temperatures
                min_temp = min(min_temp, cycle_dict['StartTemp'], cycle_dict['EndTemp'])
                max_temp = max(max_temp, cycle_dict['StartTemp'], cycle_dict['EndTemp'])
                
                # Append to current_schedule
                cycle_dict['CycleTime'] = cycle_time_minutes
                current_schedule.append(cycle_dict)
                
                # Append to times and temps for plotting
                if cycle_dict['CycleType'].lower() == 'ramp':
                    times.extend([total_time, total_time + cycle_time_minutes])
                    temps.extend([cycle_dict['StartTemp'], cycle_dict['EndTemp']])
                elif cycle_dict['CycleType'].lower() == 'soak':
                    times.extend([total_time, total_time + cycle_time_minutes])
                    temps.extend([cycle_dict['StartTemp'], cycle_dict['StartTemp']])
                
                # Update total_time
                total_time += cycle_time_minutes
                
            except ValueError:
                print(f"Invalid cycle time format: {cycle_dict['CycleTime']}")
                continue

        return current_schedule, times, temps, min_temp, max_temp

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return None, None, None, None, None

# Initialize the QApplication instance
app = QApplication(sys.argv)

# Create and show the main window
window = MainWindow()
window.show()

sys.exit(app.exec_())