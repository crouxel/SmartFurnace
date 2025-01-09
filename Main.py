import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontDatabase
from datetime import datetime, timedelta
import pyqtgraph as pg
from custom_combobox import CustomComboBox
from schedule_window import ScheduleWindow
from styles import get_label_style, get_temp_display_style
from database import fetch_all_schedules

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.start_cycle_time = None
        self.current_schedule = []
        self.init_ui()

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

    def setup_top_layout(self):
        top_layout = QHBoxLayout()
        self.start_button.clicked.connect(self.write_start_cycle_time)
        self.combo.addItems(fetch_all_schedules() + ["Add Schedule"])
        self.combo.currentIndexChanged.connect(lambda: self.on_table_select())

        # Create and set the context menu
        context_menu = self.show_context_menu()
        self.combo.set_context_menu(context_menu)

        top_layout.addWidget(self.start_button)
        top_layout.addWidget(self.combo)
        return top_layout

    def setup_temp_display(self, font_family):
        temp_display = QLabel("000°C")
        temp_display.setAlignment(Qt.AlignCenter)
        temp_display.setFixedWidth(9 * 24)  # Set the width to accommodate 7 characters
        temp_display.setStyleSheet(get_temp_display_style(font_family))

        # Center the temperature display with padding
        temp_display_layout = QHBoxLayout()
        temp_display_layout.addStretch()
        temp_display_layout.addWidget(temp_display)
        temp_display_layout.addStretch()
        return temp_display_layout, temp_display

    def setup_main_layout(self, top_layout, temp_display_layout):
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addLayout(temp_display_layout)  # Add the centered temperature display layout
        main_layout.addWidget(self.label)
        main_layout.addWidget(self.plot_widget)
        return main_layout

    def update_schedule_menu(self):
        self.combo.clear()
        schedules = fetch_all_schedules()
        self.combo.addItems(schedules)
        self.combo.insertSeparator(len(schedules))
        self.combo.addItem("Add Schedule")

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
            return

        elapsed_time = (datetime.now() - self.start_cycle_time).total_seconds() / 60  # in minutes
        self.plot_widget.clear()
        self.regenerate_graph()
        self.plot_widget.addLine(x=elapsed_time, pen=pg.mkPen('r', style=Qt.DashLine), label='Current Time')

        # Update temperature display
        current_temp = self.get_current_temperature(elapsed_time)  # Pass elapsed time to get current temperature
        self.temp_display.setText(f"{current_temp:03d}°C")

    def get_current_temperature(self, elapsed_time):
        for cycle in self.current_schedule:
            cycle_start = cycle['Cycle']
            cycle_end = cycle_start + cycle['CycleTime']
            if cycle_start <= elapsed_time <= cycle_end:
                # Linear interpolation between start and end temperature
                start_temp = cycle['StartTemp']
                end_temp = cycle['EndTemp']
                temp = start_temp + (end_temp - start_temp) * (elapsed_time - cycle_start) / (cycle_end - cycle_start)
                return int(temp)
        return 0  # Default temperature if not found

    def regenerate_graph(self):
        selected_table = self.combo.currentText()
        try:
            schedule, times, temps, min_temp, max_temp = load_schedule(selected_table)
            if schedule is None:
                return

            self.current_schedule = schedule

            self.plot_widget.clear()
            self.plot_widget.plot(times, temps, pen='b', name='Temperature Schedule')

            # Add current time vertical line
            start_time = self.get_start_cycle_time()
            current_time = datetime.now()
            elapsed_time = (current_time - start_time).total_seconds() / 60  # in minutes
            self.plot_widget.addLine(x=elapsed_time, pen='r', label='Current Time')  # Removed 'style' argument

            self.plot_widget.setXRange(0, times[-1])  # Set X-axis limits from start to end time
            self.plot_widget.setYRange(min_temp - 10, max_temp + 10)  # Set Y-axis limits based on min and max temperatures

            # Update X-axis with actual time
            actual_times = [start_time + timedelta(minutes=t) for t in times]
            actual_time_labels = [t.strftime('%I:%M %p') for t in actual_times]
            self.plot_widget.getAxis('bottom').setTicks([list(zip(times, actual_time_labels))])
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
        menu = QMenu()
        edit_action = QAction("Edit Schedule", self.combo)
        delete_action = QAction("Delete Schedule", self.combo)

        # Connect actions to functions
        edit_action.triggered.connect(lambda: self.open_edit_table_window(self.combo.currentText()))
        delete_action.triggered.connect(lambda: self.delete_table(self.combo.currentText()))

        # Add actions to the menu
        menu.addAction(edit_action)
        menu.addAction(delete_action)
        return menu

    def open_edit_table_window(self, table_name):
        # Fetch the schedule data for the selected table
        schedule_data = fetch_schedule_data(table_name)
        edit_window = ScheduleWindow(table_name, schedule_data, parent=self)
        edit_window.exec_()

    def open_add_table_window(self):
        add_window = ScheduleWindow(parent=self)
        add_window.exec_()

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