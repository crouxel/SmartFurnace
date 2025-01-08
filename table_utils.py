import sqlite3
from PyQt5.QtWidgets import QMenu, QAction
from datetime import datetime, timedelta
import pyqtgraph as pg
from database import get_start_cycle_time

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

def regenerate_graph(plot_widget, selected_table):
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

        for cycle in cycles:
            cycle_time_minutes = int(cycle[5])  # Ensure the value is numeric
            if cycle[4].lower() == 'ramp':
                times.extend([total_time, total_time + cycle_time_minutes])
                temps.extend([cycle[2], cycle[3]])
                min_temp = min(min_temp, cycle[2], cycle[3])
                max_temp = max(max_temp, cycle[2], cycle[3])
            elif cycle[4].lower() == 'soak':
                times.extend([total_time, total_time + cycle_time_minutes])
                temps.extend([cycle[2], cycle[2]])
                min_temp = min(min_temp, cycle[2])
                max_temp = max(max_temp, cycle[2])
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

def on_table_select(combo, label, plot_widget):
    selected_table = combo.currentText()
    if selected_table == "Add Table":
        open_add_table_window()
    else:
        label.setText(f"Selected table: {selected_table}")
        regenerate_graph(plot_widget, selected_table)

def show_context_menu(combo, label):
    menu = QMenu()
    edit_action = QAction("Edit Table", combo)
    delete_action = QAction("Delete Table", combo)
    # Add actions to the menu
    menu.addAction(edit_action)
    menu.addAction(delete_action)
    return menu