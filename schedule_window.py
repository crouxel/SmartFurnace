from PyQt5.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
                            QComboBox)
from styles import (ThemeManager, get_dialog_style, get_button_style, 
                   get_table_style, get_combo_style)
from database import DatabaseManager
from constants import (TIME_PATTERN, TEMP_PATTERN, DEFAULT_TIME, 
                      MIN_TEMP, MAX_TEMP, ERROR_MESSAGES, 
                      SUCCESS_MESSAGES, validate_time_format, 
                      validate_temperature, DEFAULT_TEMP)
import re
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QPalette

class ScheduleWindow(QDialog):
    def __init__(self, table_name=None, schedule_data=None, parent=None):
        super().__init__(parent)
        self.table_name = table_name
        self.schedule_data = schedule_data
        self.is_new_schedule = table_name is None
        
        # Apply theme styles
        theme = ThemeManager.get_current_theme()
        self.setStyleSheet(get_dialog_style())
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Schedule Editor" if self.is_new_schedule else f"Edit Schedule: {self.table_name}")
        self.setGeometry(100, 100, 600, 400)

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Cycle Type", "Start Temp", "End Temp", "Cycle Time", "Notes"])
        self.table.setStyleSheet(get_table_style())  # Add table styling

        if self.schedule_data:
            self.table.setRowCount(len(self.schedule_data))
            for row, data in enumerate(self.schedule_data):
                self.setup_row(row, data)
        else:
            self.table.setRowCount(1)
            self.setup_row(0)

        add_row_button = QPushButton("Add Row")
        add_row_button.setStyleSheet(get_button_style())  # Add button styling
        add_row_button.clicked.connect(self.add_row)
        layout.addWidget(add_row_button)
        layout.addWidget(self.table)

        # Different button layouts for new vs edit
        button_layout = QHBoxLayout()
        if self.is_new_schedule:
            save_button = QPushButton("Save")
            save_button.setStyleSheet(get_button_style())  # Add button styling
            save_button.clicked.connect(self.save_as_schedule)
            button_layout.addWidget(save_button)
        else:
            update_button = QPushButton("Update")
            update_button.setStyleSheet(get_button_style())  # Add button styling
            update_button.clicked.connect(self.update_schedule)
            save_as_button = QPushButton("Save As")
            save_as_button.setStyleSheet(get_button_style())  # Add button styling
            save_as_button.clicked.connect(self.save_as_schedule)
            button_layout.addWidget(update_button)
            button_layout.addWidget(save_as_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(get_button_style())  # Add button styling
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def setup_row(self, row, data=None):
        # Create and set up the combo box for cycle type
        cycle_type_combo = QComboBox()
        cycle_type_combo.addItem("")  # Empty item first
        cycle_type_combo.addItems(["Ramp", "Soak"])
        
        # Apply theme-aware style to combo box
        theme = ThemeManager.get_current_theme()
        text_color = theme['text'] if theme['name'] == 'Light Industrial' else '#E0E0E0'
        cycle_type_combo.setStyleSheet(get_combo_style())
        
        # Connect the combo box change event
        cycle_type_combo.currentTextChanged.connect(lambda: self.on_cycle_type_changed(row))
        
        self.table.setCellWidget(row, 0, cycle_type_combo)

        if data:
            cycle_type_combo.setCurrentText(str(data[0]))
            for col in range(1, 5):
                item = QTableWidgetItem(str(data[col]))
                self.table.setItem(row, col, item)
        else:
            # Initialize empty cells
            for col in range(1, 5):
                self.table.setItem(row, col, QTableWidgetItem(""))

    def add_row(self):
        current_row = self.table.rowCount()
        self.table.setRowCount(current_row + 1)
        self.setup_row(current_row)

    def on_cycle_type_changed(self, row):
        cycle_type = self.table.cellWidget(row, 0).currentText()
        
        if cycle_type in ["Ramp", "Soak"]:
            # Check if start temperature is empty
            start_temp_item = self.table.item(row, 1)
            if not start_temp_item or not start_temp_item.text():
                self.table.setItem(row, 1, QTableWidgetItem(str(DEFAULT_TEMP)))
            
            # Only set end temperature for Soak
            end_temp_item = self.table.item(row, 2)
            if cycle_type == "Soak":
                if not end_temp_item or not end_temp_item.text():
                    self.table.setItem(row, 2, QTableWidgetItem(str(DEFAULT_TEMP)))
            elif cycle_type == "Ramp":
                # For Ramp, clear end temperature if it's the default value
                if end_temp_item and end_temp_item.text() == str(DEFAULT_TEMP):
                    self.table.setItem(row, 2, QTableWidgetItem(""))
        else:
            # Clear temperatures if cycle type is cleared
            self.table.setItem(row, 1, QTableWidgetItem(""))
            self.table.setItem(row, 2, QTableWidgetItem(""))

    def update_schedule(self):
        try:
            entries = self.validate_and_collect_entries()
            if entries:
                # Convert entries to the format expected by DatabaseManager
                formatted_data = [(entry[0], entry[1], entry[2], entry[3], entry[4]) 
                                for entry in entries]
                
                if DatabaseManager.save_schedule(self.table_name, formatted_data):
                    QMessageBox.information(self, "Success", SUCCESS_MESSAGES['update_success'])
                    if hasattr(self.parent(), 'update_schedule_menu'):
                        self.parent().update_schedule_menu()
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", ERROR_MESSAGES['save_failed'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update schedule: {str(e)}")
            print(f"Error details: {str(e)}")

    def validate_and_collect_entries(self):
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

            if not validate_time_format(cycle_time):
                QMessageBox.warning(self, "Error", ERROR_MESSAGES['invalid_time'])
                return None

            try:
                start_temp = int(start_temp)
                end_temp = int(end_temp)
                
                if not validate_temperature(start_temp) or not validate_temperature(end_temp):
                    QMessageBox.warning(self, "Error", ERROR_MESSAGES['invalid_temp'])
                    return None
                    
            except ValueError:
                QMessageBox.warning(self, "Error", ERROR_MESSAGES['invalid_temp'])
                return None

            valid_entries.append((cycle_type, start_temp, end_temp, cycle_time, notes))

        if not valid_entries:
            QMessageBox.critical(self, "Error", "No valid entries to save.")
            return None

        return valid_entries

    def save_as_schedule(self):
        try:
            name, ok = QInputDialog.getText(self, 'Save Schedule', 'Enter schedule name:')
            if ok and name:
                # Validate entries first
                entries = self.validate_and_collect_entries()
                if entries:
                    # Print debug info
                    print(f"Attempting to save schedule: {name}")
                    print(f"Data to save: {entries}")
                    
                    if DatabaseManager.save_schedule(name, entries):
                        QMessageBox.information(self, "Success", SUCCESS_MESSAGES['save_success'])
                        if hasattr(self.parent(), 'update_schedule_menu'):
                            self.parent().update_schedule_menu()
                        self.accept()
                    else:
                        QMessageBox.critical(self, "Error", ERROR_MESSAGES['save_failed'])
        except Exception as e:
            print(f"Error saving schedule: {str(e)}")  # Debug print
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