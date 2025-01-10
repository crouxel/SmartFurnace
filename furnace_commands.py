from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QSpinBox, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt
from styles import get_dialog_style, get_button_style

class FurnaceCommandsWindow(QDialog):
    def __init__(self, parent=None, schedule_data=None):
        super().__init__(parent)
        self.schedule_data = schedule_data
        self.initial_program = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Furnace Commands")
        self.setStyleSheet(get_dialog_style())
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Program number input
        number_layout = QHBoxLayout()
        label = QLabel("Initial Program Number:")
        self.program_spin = QSpinBox()
        self.program_spin.setRange(0, 99)
        self.program_spin.valueChanged.connect(self.update_commands)
        
        number_layout.addWidget(label)
        number_layout.addWidget(self.program_spin)
        number_layout.addStretch()
        
        # Commands table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Temperature Commands", "Time Commands"])
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setStyleSheet(get_button_style())
        close_button.clicked.connect(self.accept)
        
        # Add widgets to layout
        layout.addLayout(number_layout)
        layout.addWidget(self.table)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        self.update_commands()
        
    def update_commands(self):
        """Update the commands table based on schedule and program number."""
        if not self.schedule_data:
            return
            
        self.table.setRowCount(len(self.schedule_data))
        program_num = self.program_spin.value()
        
        for i, cycle in enumerate(self.schedule_data):
            # Temperature command
            temp_cmd = f"PV=C{program_num + i}, SV={int(cycle['StartTemp'])}"
            self.table.setItem(i, 0, QTableWidgetItem(temp_cmd))
            
            # Time command
            time_minutes = self.parse_time_to_minutes(cycle['CycleTime'])
            time_cmd = f"PV=t{program_num + i}, SV={time_minutes}"
            self.table.setItem(i, 1, QTableWidgetItem(time_cmd))
            
        self.table.resizeColumnsToContents()
        
    def parse_time_to_minutes(self, time_str):
        """Convert time string (HH:MM:SS) to minutes."""
        h, m, s = map(int, time_str.split(':'))
        return h * 60 + m + (1 if s > 0 else 0)  # Round up if there are seconds 