from PyQt5.QtWidgets import (QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
                            QComboBox, QLineEdit)
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
import logging

logger = logging.getLogger(__name__)

# More flexible time pattern that allows single digits
TIME_PATTERN = re.compile(r'^(\d{1,2}):([0-5]?\d):([0-5]?\d)$')

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

        # Connect first row cycle type changes to auto-population
        first_row_cycle_type = self.table.cellWidget(0, 0)
        if first_row_cycle_type:
            first_row_cycle_type.currentTextChanged.connect(self.auto_populate_first_row)

    def setup_row(self, row, data=None):
        """Set up a row in the schedule table."""
        # Create and set up the combo box for cycle type
        cycle_type_combo = QComboBox()
        cycle_type_combo.addItem("")  # Empty item first
        cycle_type_combo.addItems(["Ramp", "Soak"])
        cycle_type_combo.setStyleSheet(get_combo_style())
        self.table.setCellWidget(row, 0, cycle_type_combo)

        # Create line edits for temperature and time
        start_temp_edit = QLineEdit()
        end_temp_edit = QLineEdit()
        cycle_time_edit = QLineEdit()
        notes_edit = QLineEdit()

        # Set up widgets in cells
        self.table.setCellWidget(row, 1, start_temp_edit)
        self.table.setCellWidget(row, 2, end_temp_edit)
        self.table.setCellWidget(row, 3, cycle_time_edit)
        self.table.setCellWidget(row, 4, notes_edit)

        if data:
            cycle_type_combo.setCurrentText(str(data[0]))
            start_temp_edit.setText(str(data[1]))
            end_temp_edit.setText(str(data[2]))
            cycle_time_edit.setText(str(data[3]))
            notes_edit.setText(str(data[4]))

        # Connect first row cycle type changes to auto-population
        if row == 0:
            cycle_type_combo.currentTextChanged.connect(self.auto_populate_first_row)

    def add_row(self):
        current_row = self.table.rowCount()
        self.table.setRowCount(current_row + 1)
        self.setup_row(current_row)

    def on_cycle_type_changed(self, row):
        try:
            cycle_type = self.table.cellWidget(row, 0).currentText()
            logger.debug(f"Cycle type changed in row {row} to: {cycle_type}")
            
            if cycle_type in ["Ramp", "Soak"]:
                # Initialize time to 00:00:00
                time_item = QTableWidgetItem("00:00:00")
                self.table.setItem(row, 3, time_item)
                logger.debug(f"Set initial time for row {row}")
        except Exception as e:
            logger.error(f"Error in on_cycle_type_changed: {e}")

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

    def validate_time_format(self, time_str: str) -> bool:
        """Validate time format and values."""
        try:
            logger.debug(f"Validating time format: '{time_str}'")
            
            if not time_str:
                logger.debug("Empty time string")
                return False
            
            # Check pattern match
            match = TIME_PATTERN.match(time_str)
            if not match:
                logger.debug(f"Time string '{time_str}' doesn't match pattern")
                return False
            
            # Get the matched groups
            hours, minutes, seconds = match.groups()
            logger.debug(f"Matched groups - H:{hours} M:{minutes} S:{seconds}")
            
            # Convert to integers
            hours = int(hours)
            minutes = int(minutes)
            seconds = int(seconds)
            logger.debug(f"Converted values - H:{hours} M:{minutes} S:{seconds}")
            
            # Check ranges
            if not (0 <= hours <= 99 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
                logger.debug(f"Time values out of range - H:{hours} M:{minutes} S:{seconds}")
                return False
            
            logger.debug("Time format validation successful")
            return True
        except Exception as e:
            logger.debug(f"Time validation error: {str(e)}")
            return False

    def validate_and_collect_entries(self):
        valid_entries = []
        row_count = self.table.rowCount()
        
        # Log validation process
        logger.debug(f"Validating {row_count} rows")
        
        for row in range(row_count):
            # Get cycle type
            cycle_widget = self.table.cellWidget(row, 0)
            if cycle_widget is None:
                logger.debug(f"Row {row}: No cycle widget")
                continue
            
            cycle_type = cycle_widget.currentText()
            if not cycle_type:
                logger.debug(f"Row {row}: Empty cycle type")
                continue

            try:
                # Get cell values
                start_temp = self.table.item(row, 1)
                end_temp = self.table.item(row, 2)
                cycle_time = self.table.item(row, 3)
                notes = self.table.item(row, 4)

                # Check if cells exist and have text
                if not all([start_temp, end_temp, cycle_time]):
                    logger.debug(f"Row {row}: Missing required fields")
                    continue

                start_temp_text = start_temp.text().strip()
                end_temp_text = end_temp.text().strip()
                cycle_time_text = cycle_time.text().strip()
                notes_text = notes.text().strip() if notes else ""

                # Skip empty rows
                if not all([start_temp_text, end_temp_text, cycle_time_text]):
                    logger.debug(f"Row {row}: Empty required fields")
                    continue

                # Validate time format
                if not validate_time_format(cycle_time_text):
                    QMessageBox.warning(self, "Error", 
                        f"Invalid time format in row {row + 1}. Use HH:MM:SS")
                    return None

                # Validate temperatures
                try:
                    start_temp_val = int(start_temp_text)
                    end_temp_val = int(end_temp_text)
                    
                    if not (validate_temperature(start_temp_val) and 
                            validate_temperature(end_temp_val)):
                        QMessageBox.warning(self, "Error", 
                            f"Invalid temperature in row {row + 1}")
                        return None
                            
                except ValueError:
                    QMessageBox.warning(self, "Error", 
                        f"Invalid temperature format in row {row + 1}")
                    return None

                # Add valid entry
                valid_entries.append((
                    cycle_type, 
                    start_temp_val, 
                    end_temp_val, 
                    cycle_time_text, 
                    notes_text
                ))
                logger.debug(f"Row {row}: Valid entry added")

            except AttributeError as e:
                logger.error(f"Row {row}: AttributeError - {str(e)}")
                continue

        if not valid_entries:
            QMessageBox.warning(self, "Error", 
                "No valid entries to save. Please check all required fields.")
            return None

        logger.info(f"Collected {len(valid_entries)} valid entries")
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

    def auto_populate_first_row(self, cycle_type):
        """Auto-populate default values for first row when cycle type changes."""
        if cycle_type in ["Ramp", "Soak"]:
            start_temp_edit = self.table.cellWidget(0, 1)
            cycle_time_edit = self.table.cellWidget(0, 3)
            
            if start_temp_edit and cycle_time_edit:
                start_temp_edit.setText(str(DEFAULT_TEMP))
                cycle_time_edit.setText(DEFAULT_TIME)

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