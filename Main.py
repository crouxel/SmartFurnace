import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QMenu, QAction, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime, timedelta
import pyqtgraph as pg
from database import fetch_schedule, get_start_cycle_time
from table_utils import fetch_tables, on_table_select, show_context_menu, regenerate_graph  # Import functions from table_utils

start_cycle_time = None

def write_start_cycle_time():
    global start_cycle_time
    start_cycle_time = datetime.now()
    with open('start_cycle_time.txt', 'w') as f:
        f.write(start_cycle_time.isoformat())

def update_graph():
    global start_cycle_time
    if start_cycle_time is None:
        return

    elapsed_time = (datetime.now() - start_cycle_time).total_seconds() / 60  # in minutes
    plot_widget.clear()
    regenerate_graph(plot_widget, combo.currentText())
    plot_widget.addLine(x=elapsed_time, pen=pg.mkPen('r', style=Qt.DashLine), label='Current Time')

app = QApplication(sys.argv)
window = QWidget()
layout = QVBoxLayout()

combo = QComboBox()
label = QLabel()
plot_widget = pg.PlotWidget()
start_button = QPushButton("Start Cycle")

combo.addItems(fetch_tables())
combo.currentIndexChanged.connect(lambda: on_table_select(combo, label, plot_widget))
combo.setContextMenuPolicy(Qt.CustomContextMenu)
combo.customContextMenuRequested.connect(lambda: show_context_menu(combo, label).exec_(combo.mapToGlobal(combo.pos())))

start_button.clicked.connect(write_start_cycle_time)

layout.addWidget(combo)
layout.addWidget(label)
layout.addWidget(plot_widget)
layout.addWidget(start_button)
window.setLayout(layout)
window.show()

# Set up a timer to update the graph every second
timer = QTimer()
timer.timeout.connect(update_graph)
timer.start(1000)

sys.exit(app.exec_())