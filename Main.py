import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontDatabase
from datetime import datetime, timedelta
import pyqtgraph as pg
from custom_combobox import CustomComboBox  # Import the custom combo box

# Initialize the QApplication instance
app = QApplication(sys.argv)

start_cycle_time = None
current_schedule = []

def fetch_tables():
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables
    except sqlite3.OperationalError as e:
        print(f"Error fetching tables: {e}")
        return []

def delete_table(table_name):
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        conn.close()
        print(f"Table {table_name} deleted successfully.")
    except sqlite3.OperationalError as e:
        print(f"Error deleting table {table_name}: {e}")

def on_table_select(combo, label, plot_widget):
    selected_table = combo.currentText()
    if selected_table == "Add Schedule":
        open_add_table_window()
    else:
        label.setText(f"Selected table: {selected_table}")
        regenerate_graph(plot_widget, selected_table)

def show_context_menu(combo, label):
    menu = QMenu()
    edit_action = QAction("Edit Table", combo)
    delete_action = QAction("Delete Table", combo)
    add_action = QAction("Add Schedule", combo)

    # Connect actions to functions
    edit_action.triggered.connect(lambda: edit_table(combo.currentText()))
    delete_action.triggered.connect(lambda: delete_table(combo.currentText()))
    add_action.triggered.connect(open_add_table_window)

    # Add actions to the menu
    menu.addAction(edit_action)
    menu.addAction(delete_action)
    menu.addSeparator()
    menu.addAction(add_action)
    return menu

def edit_table(table_name):
    # Placeholder function for editing a table
    print(f"Edit table: {table_name}")

def open_add_table_window():
    # Placeholder function for adding a new table
    print("Open add table window")

def write_start_cycle_time():
    global start_cycle_time
    start_cycle_time = datetime.now()
    with open('start_cycle_time.txt', 'w') as f:
        f.write(start_cycle_time.isoformat())

def get_start_cycle_time():
    global start_cycle_time
    if start_cycle_time is None:
        try:
            with open('start_cycle_time.txt', 'r') as f:
                start_cycle_time = datetime.fromisoformat(f.read().strip())
        except FileNotFoundError:
            start_cycle_time = datetime.now()
    return start_cycle_time

def update_graph():
    global start_cycle_time
    if start_cycle_time is None:
        return

    elapsed_time = (datetime.now() - start_cycle_time).total_seconds() / 60  # in minutes
    plot_widget.clear()
    regenerate_graph(plot_widget, combo.currentText())
    plot_widget.addLine(x=elapsed_time, pen=pg.mkPen('r', style=Qt.DashLine), label='Current Time')

    # Update temperature display
    current_temp = get_current_temperature(elapsed_time)  # Pass elapsed time to get current temperature
    temp_display.setText(f"{current_temp:03d}°C")

def get_current_temperature(elapsed_time):
    global current_schedule
    for cycle in current_schedule:
        cycle_start = cycle[0]
        cycle_end = cycle[1]
        if cycle_start <= elapsed_time <= cycle_end:
            # Linear interpolation between start and end temperature
            start_temp = cycle[2]
            end_temp = cycle[3]
            temp = start_temp + (end_temp - start_temp) * (elapsed_time - cycle_start) / (cycle_end - cycle_start)
            return int(temp)
    return 0  # Default temperature if not found

def regenerate_graph(plot_widget, selected_table):
    global current_schedule
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()
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
            cycle_time_minutes = int(cycle[5])  # Ensure the value is numeric
            if cycle[4].lower() == 'ramp':
                times.extend([total_time, total_time + cycle_time_minutes])
                temps.extend([cycle[2], cycle[3]])
                min_temp = min(min_temp, cycle[2], cycle[3])
                max_temp = max(max_temp, cycle[2], cycle[3])
                current_schedule.append((total_time, total_time + cycle_time_minutes, cycle[2], cycle[3]))
            elif cycle[4].lower() == 'soak':
                times.extend([total_time, total_time + cycle_time_minutes])
                temps.extend([cycle[2], cycle[2]])
                min_temp = min(min_temp, cycle[2])
                max_temp = max(max_temp, cycle[2])
                current_schedule.append((total_time, total_time + cycle_time_minutes, cycle[2], cycle[2]))
            total_time += cycle_time_minutes

        plot_widget.clear()
        plot_widget.plot(times, temps, pen='b', name='Temperature Schedule')

        # Add current time vertical line
        start_time = get_start_cycle_time()
        current_time = datetime.now()
        elapsed_time = (current_time - start_time).total_seconds() / 60  # in minutes
        plot_widget.addLine(x=elapsed_time, pen='r', label='Current Time')  # Removed 'style' argument

        plot_widget.setXRange(0, total_time)  # Set X-axis limits from start to end time
        plot_widget.setYRange(min_temp - 10, max_temp + 10)  # Set Y-axis limits based on min and max temperatures

        # Update X-axis with actual time
        actual_times = [start_time + timedelta(minutes=t) for t in times]
        actual_time_labels = [t.strftime('%I:%M %p') for t in actual_times]
        plot_widget.getAxis('bottom').setTicks([list(zip(times, actual_time_labels))])
    except Exception as e:
        print(f"Error in regenerate_graph: {e}")

window = QWidget()
main_layout = QVBoxLayout()

# Load the Orbitron font
font_id = QFontDatabase.addApplicationFont("OrbitronFont.ttf")
if font_id == -1:
    print("Failed to load Orbitron font")
else:
    font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

# Create the top horizontal layout
top_layout = QHBoxLayout()
start_button = QPushButton("Start Cycle")
combo = CustomComboBox()

combo.addItems(fetch_tables() + ["Add Schedule"])
combo.currentIndexChanged.connect(lambda: on_table_select(combo, label, plot_widget))

label = QLabel()  # Define the label before using it

# Create and set the context menu
context_menu = show_context_menu(combo, label)
combo.set_context_menu(context_menu)

start_button.clicked.connect(write_start_cycle_time)

top_layout.addWidget(start_button)
top_layout.addWidget(combo)

# Create the temperature display
temp_display = QLabel("000°C")
temp_display.setAlignment(Qt.AlignCenter)
temp_display.setFixedWidth(7 * 24)  # Set the width to accommodate 7 characters
temp_display.setStyleSheet(f"""
    background-color: black;
    color: green;
    font-size: 48px;
    font-family: '{font_family}';
""")

# Center the temperature display
temp_display_layout = QHBoxLayout()
temp_display_layout.addStretch()
temp_display_layout.addWidget(temp_display)
temp_display_layout.addStretch()

plot_widget = pg.PlotWidget()

main_layout.addLayout(top_layout)
main_layout.addLayout(temp_display_layout)  # Add the centered temperature display layout
main_layout.addWidget(label)
main_layout.addWidget(plot_widget)
window.setLayout(main_layout)
window.show()

# Set up a timer to update the graph every second
timer = QTimer()
timer.timeout.connect(update_graph)
timer.start(1000)

sys.exit(app.exec_())