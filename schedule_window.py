import sqlite3
from PyQt5.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
                            QComboBox)
import re

class ScheduleWindow(QDialog):
    def __init__(self, table_name=None, schedule_data=None, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.schedule_data = schedule_data
        self.is_new_schedule = table_name is None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Schedule Editor" if self.is_new_schedule else f"Edit Schedule: {self.table_name}")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Cycle Type", "Start Temp", "End Temp", "Cycle Time", "Notes"])

        if self.schedule_data:
            self.table.setRowCount(len(self.schedule_data))
            for row, data in enumerate(self.schedule_data):
                self.setup_row(row, data)
        else:
            self.table.setRowCount(1)
            self.setup_row(0)

        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_row)
        layout.addWidget(add_row_button)
        layout.addWidget(self.table)

        # Different button layouts for new vs edit
        button_layout = QHBoxLayout()
        if self.is_new_schedule:
            save_button = QPushButton("Save")
            save_button.clicked.connect(self.save_as_schedule)
            button_layout.addWidget(save_button)
        else:
            update_button = QPushButton("Update")
            update_button.clicked.connect(self.update_schedule)
            save_as_button = QPushButton("Save As")
            save_as_button.clicked.connect(self.save_as_schedule)
            button_layout.addWidget(update_button)
            button_layout.addWidget(save_as_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def setup_row(self, row, data=None):
        # Create and set up the combo box for cycle type
        cycle_type_combo = QComboBox()
        cycle_type_combo.addItem("")  # Add empty item first
        cycle_type_combo.addItems(["Ramp", "Soak"])
        
        # Connect the combo box change event to add_row
        cycle_type_combo.currentTextChanged.connect(lambda: self.on_cycle_type_changed(row))
        
        self.table.setCellWidget(row, 0, cycle_type_combo)

        if data:
            cycle_type_combo.setCurrentText(str(data[0]))
            for col in range(1, 5):
                item = QTableWidgetItem(str(data[col]))
                self.table.setItem(row, col, item)
        else:
            for col in range(1, 5):
                self.table.setItem(row, col, QTableWidgetItem(""))

    def add_row(self):
        current_row = self.table.rowCount()
        self.table.setRowCount(current_row + 1)
        self.setup_row(current_row)

    def on_cycle_type_changed(self, row):
        cycle_widget = self.table.cellWidget(row, 0)
        selected_type = cycle_widget.currentText()
        
        if selected_type in ["Ramp", "Soak"]:
            # Set default cycle time
            self.table.setItem(row, 3, QTableWidgetItem("00:00:00"))
            
            # If not the first row, copy previous end temp to start temp
            if row > 0:
                prev_end_temp = self.table.item(row - 1, 2)
                if prev_end_temp and prev_end_temp.text():
                    self.table.setItem(row, 1, QTableWidgetItem(prev_end_temp.text()))
                    
                    # If it's a Soak, set end temp equal to start temp
                    if selected_type == "Soak":
                        self.table.setItem(row, 2, QTableWidgetItem(prev_end_temp.text()))
            
            # Add new row if this is the last row
            if row == self.table.rowCount() - 1:
                self.add_row()

    def update_schedule(self):
        try:
            entries = self.validate_and_collect_entries()
            if entries:
                conn = sqlite3.connect('SmartFurnace.db')
                cursor = conn.cursor()
                
                # Clear existing entries
                cursor.execute(f"DELETE FROM {self.table_name}")
                
                # Insert new entries with Cycle number
                for i, entry in enumerate(entries, 1):  # Start counting from 1
                    cursor.execute(f"""
                        INSERT INTO {self.table_name} 
                        (Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (i,) + entry)  # Add cycle number to the entry
                
                conn.commit()
                conn.close()
                
                if hasattr(self.parent(), 'update_schedule_menu'):
                    self.parent().update_schedule_menu()
                
                self.accept()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"Failed to update schedule: {str(e)}")
            print(f"SQL Error details: {str(e)}")
            print(f"Entries being inserted: {entries}")

    def validate_and_collect_entries(self):
        time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}$')
        valid_entries = []
        
        for row in range(self.table.rowCount()):
            cycle_widget = self.table.cellWidget(row, 0)
            if cycle_widget is None or cycle_widget.currentText() == "":
                continue
                
            cycle_type = cycle_widget.currentText()
            start_temp = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
            end_temp = self.table.item(row, 2).text() if self.table.item(row, 2) else ""
            cycle_time = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
            notes = self.table.item(row, 4).text() if self.table.item(row, 4) else ""

            # Skip empty or incomplete rows
            if not cycle_type or not start_temp or not end_temp or not cycle_time:
                continue

            if not time_pattern.match(cycle_time):
                QMessageBox.critical(self, "Error", 
                                   f"Invalid time format in row {row + 1}. Use HH:MM:SS format.")
                return None

            try:
                start_temp = int(start_temp)
                end_temp = int(end_temp)
            except ValueError:
                QMessageBox.critical(self, "Error", 
                                   f"Temperature values in row {row + 1} must be integers.")
                return None

            valid_entries.append((cycle_type, start_temp, end_temp, cycle_time, notes))

        if not valid_entries:
            QMessageBox.critical(self, "Error", "No valid entries to save.")
            return None

        return valid_entries

    def save_as_schedule(self):
        new_schedule_name, ok = QInputDialog.getText(self, "Save As", "Enter new schedule name:")
        if not ok or not new_schedule_name:
            return

        if not re.match("^[A-Za-z0-9_]+$", new_schedule_name):
            QMessageBox.critical(self, "Error", 
                               "Schedule name can only contain letters, numbers, and underscores.")
            return

        entries = self.validate_and_collect_entries()
        if entries:
            try:
                save_schedule(new_schedule_name, entries)
                if hasattr(self.parent(), 'update_schedule_menu'):
                    self.parent().update_schedule_menu()
                self.accept()
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Error", f"Failed to save schedule: {str(e)}")

def save_schedule(schedule_name, entries):
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()

        # Create table with the new schedule name
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schedule_name} (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Cycle INTEGER NOT NULL,
                CycleType TEXT NOT NULL,
                StartTemp INTEGER NOT NULL,
                EndTemp INTEGER NOT NULL,
                CycleTime TEXT NOT NULL,
                Notes TEXT
            )
        """)

        # Insert entries with Cycle number
        for i, entry in enumerate(entries, 1):  # Start counting from 1
            cursor.execute(f"""
                INSERT INTO {schedule_name} 
                (Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (i,) + entry)

        conn.commit()
        conn.close()
        print(f"Schedule {schedule_name} saved successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred while saving the schedule: {e}")
        raise e