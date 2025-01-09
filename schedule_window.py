from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
import re
from database import save_schedule, fetch_all_schedules, fetch_schedule, delete_schedule

class ScheduleWindow(QDialog):
    def __init__(self, table_name=None, schedule_data=None, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.schedule_data = schedule_data
        self.cycle_entries = []
        self.row_added = False  # Flag to track if a new row has been added
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Schedule" if self.schedule_data else "Add Schedule")
        self.setMinimumSize(800, 600)  # Set minimum size for the window
        layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.name_edit = QLineEdit(self.table_name if self.table_name else "")
        form_layout.addRow("Schedule Name:", self.name_edit)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Cycle Type", "Start Temp [°C]", "End Temp [°C]", "Cycle Time (HH:MM:SS)", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addLayout(form_layout)
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")

        self.save_button.clicked.connect(self.save_schedule)
        self.cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        if self.schedule_data:
            self.load_schedule_data()
        else:
            self.add_empty_row()

        self.table.cellChanged.connect(self.on_cell_changed)

    def load_schedule_data(self):
        self.table.blockSignals(True)
        for cycle in self.schedule_data:
            self.add_cycle_row(cycle)
        self.table.blockSignals(False)

    def add_cycle_row(self, cycle=None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        cycle_type_combobox = QComboBox()
        cycle_type_combobox.addItems(["", "Ramp", "Soak"])  # Add a blank option
        if cycle:
            cycle_type_combobox.setCurrentText(cycle[0])  # CycleType is the first item
        self.table.setCellWidget(row, 0, cycle_type_combobox)

        start_temp_item = QTableWidgetItem(str(cycle[1]) if cycle else "")
        self.table.setItem(row, 1, start_temp_item)

        end_temp_item = QTableWidgetItem(str(cycle[2]) if cycle else "")
        self.table.setItem(row, 2, end_temp_item)

        cycle_time_item = QTableWidgetItem(cycle[3] if cycle else "00:00:00")  # Prepopulate with 00:00:00
        self.table.setItem(row, 3, cycle_time_item)

        notes_item = QTableWidgetItem(cycle[4] if cycle else "")
        self.table.setItem(row, 4, notes_item)

        cycle_type_combobox.currentIndexChanged.connect(lambda: self.on_cycle_type_change(row))

        if row == 0 and not cycle:
            start_temp_item.setText("25")

        # Trigger the addition of a new row when an option is selected
        cycle_type_combobox.currentIndexChanged.connect(lambda: self.add_empty_row_if_needed(row))

    def add_empty_row_if_needed(self, row):
        cycle_type = self.table.cellWidget(row, 0).currentText()
        if cycle_type and row == self.table.rowCount() - 1:
            self.add_empty_row()

    def is_last_row_empty(self):
        last_row = self.table.rowCount() - 1
        for col in range(self.table.columnCount()):
            item = self.table.item(last_row, col)
            if item and item.text():
                return False
        return True

    def add_empty_row(self):
        self.row_added = False  # Reset the flag when adding a new row
        self.add_cycle_row()

    def on_cycle_type_change(self, row):
        cycle_type = self.table.cellWidget(row, 0).currentText()
        start_temp_item = self.table.item(row, 1)
        end_temp_item = self.table.item(row, 2)

        if row > 0:
            prev_end_temp = self.table.item(row - 1, 2).text()
            start_temp_item.setText(prev_end_temp)

        if cycle_type == "Soak":
            end_temp_item.setText(start_temp_item.text())
            end_temp_item.setFlags(end_temp_item.flags() & ~Qt.ItemIsEditable)
        else:
            end_temp_item.setFlags(end_temp_item.flags() | Qt.ItemIsEditable)

    def on_cell_changed(self, row, column):
        if row == self.table.rowCount() - 1:
            cycle_type = self.table.cellWidget(row, 0).currentText()
            if cycle_type:
                self.add_empty_row()

    def save_schedule(self):
        schedule_name = self.name_edit.text()
        if not schedule_name:
            QMessageBox.critical(self, "Error", "Schedule name cannot be empty")
            return

        # Validate cycle time format
        time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}$')
        valid_entries = []
        for row in range(self.table.rowCount() - 1):
            cycle_type = self.table.cellWidget(row, 0).currentText()
            start_temp = self.table.item(row, 1).text()
            end_temp = self.table.item(row, 2).text()
            cycle_time = self.table.item(row, 3).text()
            notes = self.table.item(row, 4).text()

            # Skip empty rows
            if not cycle_type and not start_temp and not end_temp and not cycle_time and not notes:
                continue

            if not time_pattern.match(cycle_time) or cycle_time == "00:00:00":
                QMessageBox.critical(self, "Error", f"Invalid time format for cycle {row + 1}. Please use HH:MM:SS format and ensure time is not 00:00:00.")
                return

            valid_entries.append([row + 1, cycle_type, start_temp, end_temp, cycle_time, notes])

        # Save the schedule to the database
        save_schedule(schedule_name, valid_entries)

        # Update the dropdown menu if the method exists
        if hasattr(self.parent(), 'update_schedule_menu'):
            self.parent().update_schedule_menu()
        else:
            print("Warning: Parent widget does not have update_schedule_menu method")

        self.accept()