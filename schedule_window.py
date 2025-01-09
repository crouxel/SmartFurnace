from PyQt5.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, 
    QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
    QComboBox, QLineEdit, QHeaderView, QWidget
)
from PyQt5.QtGui import QPalette, QIntValidator
from PyQt5.QtCore import QObject
from typing import List, Dict, Optional, Tuple

from styles import (
    ThemeManager, get_dialog_style, get_button_style, 
    get_table_style, get_combo_style
)
from database import DatabaseManager
from constants import (
    TIME_PATTERN, TEMP_PATTERN, DEFAULT_TIME, 
    MIN_TEMP, MAX_TEMP, ERROR_MESSAGES, 
    SUCCESS_MESSAGES, validate_time_format, 
    validate_temperature, DEFAULT_TEMP
)
import re
import logging

logger = logging.getLogger(__name__)

# More flexible time pattern that allows single digits
TIME_PATTERN = re.compile(r'^(\d{1,2}):([0-5]?\d):([0-5]?\d)$')

class ScheduleWindow:  # Remove QDialog inheritance for test mode
    def __new__(cls, parent=None, test_mode=False):
        if test_mode:
            return super().__new__(cls)
        else:
            return super().__new__(QDialog)
            
    def __init__(self, parent=None, test_mode=False):
        if test_mode:
            self.test_mode = True
            self.test_cells = {}
            self.schedule_data = None
        else:
            QDialog.__init__(self, parent)
            self.test_mode = False
            self.schedule_data = None
            self.setup_ui()

    def setup_ui(self):
        """Set up the user interface."""
        if self.test_mode:
            return
        
        self.setWindowTitle("Schedule Editor")
        self.setStyleSheet(get_dialog_style())
        
        # Force text color for all widgets
        palette = self.palette()
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        self.setPalette(palette)
        
        self.resize(800, 400)  # Set initial window size
        
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Add spacing between elements
        
        # Set up table with proper column widths
        self.table = QTableWidget()
        self.setup_table()
        self.table.setColumnWidth(0, 100)  # Type
        self.table.setColumnWidth(1, 100)  # Start Temp
        self.table.setColumnWidth(2, 100)  # End Temp
        self.table.setColumnWidth(3, 100)  # Time
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Notes
        self.table.setColumnWidth(5, 30)   # Add button
        layout.addWidget(self.table)
        
        # Set up buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(self.save_as_schedule)
        cancel_button.clicked.connect(self.reject)
        
        for button in [save_button, cancel_button]:
            button.setStyleSheet(get_button_style())
            button_layout.addWidget(button)
            
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Type", "Start °C", "End °C", "Time", "Notes", ""])
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 30)
        self.table.setStyleSheet(get_table_style())  # Add table styling

        if self.schedule_data:
            self.table.setRowCount(len(self.schedule_data))
            for row, data in enumerate(self.schedule_data):
                self.setup_row(row, data)
        else:
            self.table.setRowCount(1)
            self.setup_row(0)

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

        # Connect cycle type changes to auto-population
        cycle_type_combo.currentTextChanged.connect(
            lambda text: self.auto_populate_first_row(text) if row == 0 else None
        )

    def add_row(self):
        """Add a new row to the table."""
        current_row = self.table.rowCount()
        self.table.insertRow(current_row)
        
        # Create widgets for the new row
        cycle_type = QComboBox()
        cycle_type.addItems(["Ramp", "Soak"])
        cycle_type.currentTextChanged.connect(lambda text: self.auto_populate_first_row(text))
        
        start_temp = QLineEdit()
        end_temp = QLineEdit()
        cycle_time = QLineEdit()
        notes = QLineEdit()
        
        # Set validators
        start_temp.setValidator(QIntValidator(MIN_TEMP, MAX_TEMP))
        end_temp.setValidator(QIntValidator(MIN_TEMP, MAX_TEMP))
        
        # Add widgets to the row
        self.table.setCellWidget(current_row, 0, cycle_type)
        self.table.setCellWidget(current_row, 1, start_temp)
        self.table.setCellWidget(current_row, 2, end_temp)
        self.table.setCellWidget(current_row, 3, cycle_time)
        self.table.setCellWidget(current_row, 4, notes)
        
        # Connect the add row button
        if current_row == self.table.rowCount() - 1:  # If this is the last row
            add_row_button = QPushButton("+")
            add_row_button.clicked.connect(self.add_row)
            self.table.setCellWidget(current_row, 5, add_row_button)
        
        return current_row

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
        """Update the existing schedule."""
        try:
            entries = self.validate_and_collect_entries()
            if entries:
                if DatabaseManager.save_schedule(self.schedule_name, entries):  # Pass dict directly
                    QMessageBox.information(self, "Success", SUCCESS_MESSAGES['update_success'])
                    if hasattr(self.parent(), 'update_schedule_menu'):
                        self.parent().update_schedule_menu()
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", ERROR_MESSAGES['save_failed'])
        except Exception as e:
            print(f"Error updating schedule: {str(e)}")  # Debug print
            QMessageBox.critical(self, "Error", f"Failed to update schedule: {str(e)}")

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

    def validate_and_collect_entries(self, show_warnings: bool = True) -> Optional[List[Dict]]:
        """Validate and collect all entries from the table.
        
        Args:
            show_warnings: Whether to show warning messages for invalid entries
            
        Returns:
            List of valid entries or None if validation fails
        """
        valid_entries = []
        row_count = self.table.rowCount()
        
        for row in range(row_count):
            try:
                # Get widgets
                cycle_type_widget = self.table.cellWidget(row, 0)
                start_temp_widget = self.table.cellWidget(row, 1)
                end_temp_widget = self.table.cellWidget(row, 2)
                cycle_time_widget = self.table.cellWidget(row, 3)
                notes_widget = self.table.cellWidget(row, 4)
                
                # Skip if no widgets
                if not all([cycle_type_widget, start_temp_widget, end_temp_widget, cycle_time_widget]):
                    continue
                    
                # Get values
                cycle_type = cycle_type_widget.currentText()
                start_temp_text = start_temp_widget.text().strip()
                end_temp_text = end_temp_widget.text().strip()
                cycle_time_text = cycle_time_widget.text().strip()
                notes_text = notes_widget.text().strip() if notes_widget else ""
                
                # Skip empty rows
                if not all([cycle_type, start_temp_text, end_temp_text, cycle_time_text]):
                    continue
                    
                # Validate time format
                if not validate_time_format(cycle_time_text):
                    if show_warnings:
                        QMessageBox.warning(self, "Error", f"Invalid time format in row {row + 1}. Use HH:MM:SS")
                    return None
                    
                # Validate temperatures
                try:
                    start_temp = int(start_temp_text)
                    end_temp = int(end_temp_text)
                    
                    if not (validate_temperature(start_temp) and validate_temperature(end_temp)):
                        if show_warnings:
                            QMessageBox.warning(self, "Error", f"Invalid temperature in row {row + 1}")
                        return None
                            
                    # Add valid entry
                    valid_entries.append({
                        'CycleType': cycle_type,
                        'StartTemp': start_temp,
                        'EndTemp': end_temp,
                        'Duration': cycle_time_text,
                        'Notes': notes_text
                    })
                    
                except ValueError:
                    if show_warnings:
                        QMessageBox.warning(self, "Error", f"Invalid temperature format in row {row + 1}")
                    return None
                    
            except Exception as e:
                logger.error(f"Row {row}: Error - {str(e)}")
                continue
                
        if not valid_entries:
            if show_warnings:
                QMessageBox.warning(self, "Error", "No valid entries to save. Please check all required fields.")
            return None
                
        return valid_entries

    def save_as_schedule(self):
        try:
            name, ok = QInputDialog.getText(self, 'Save Schedule', 'Enter schedule name:')
            if ok and name:
                entries = self.validate_and_collect_entries()
                if entries:
                    # Convert entries to list of tuples if needed by DatabaseManager
                    formatted_entries = [(
                        entry['CycleType'],
                        entry['StartTemp'],
                        entry['EndTemp'],
                        entry['Duration'],
                        entry.get('Notes', '')
                    ) for entry in entries]
                    
                    if DatabaseManager.save_schedule(name, formatted_entries):
                        QMessageBox.information(self, "Success", SUCCESS_MESSAGES['save_success'])
                        if hasattr(self.parent(), 'update_schedule_menu'):
                            self.parent().update_schedule_menu()
                        self.accept()
                    else:
                        QMessageBox.critical(self, "Error", ERROR_MESSAGES['save_failed'])
        except Exception as e:
            print(f"Error saving schedule: {str(e)}")  # Debug print
            QMessageBox.critical(self, "Error", f"Failed to save schedule: {str(e)}")

    def get_cell_value(self, row, col):
        """Get cell value (works in both test and normal mode)."""
        if self.test_mode:
            return self.test_cells.get((row, col), '')
        return self.table.cellWidget(row, col).text()

    def set_cell_value(self, row, col, value):
        """Set cell value (works in both test and normal mode)."""
        if self.test_mode:
            self.test_cells[(row, col)] = str(value)
        else:
            self.table.cellWidget(row, col).setText(str(value))

    def auto_populate_first_row(self, cycle_type: str):
        """Auto-populate the first row when cycle type is selected."""
        try:
            if cycle_type in ["Ramp", "Soak"]:
                if self.test_mode:
                    # Set default values in test mode
                    self.set_cell_value(0, 1, DEFAULT_TEMP)  # Start temp
                    if cycle_type == "Soak":
                        self.set_cell_value(0, 2, DEFAULT_TEMP)  # End temp
                    self.set_cell_value(0, 3, DEFAULT_TIME)  # Cycle time
                else:
                    # Normal mode code
                    start_temp = self.table.cellWidget(0, 1)
                    end_temp = self.table.cellWidget(0, 2)
                    cycle_time = self.table.cellWidget(0, 3)
                    
                    if start_temp and end_temp and cycle_time:
                        if not start_temp.text().strip():
                            start_temp.setText(str(DEFAULT_TEMP))
                        if not end_temp.text().strip() and cycle_type == "Soak":
                            end_temp.setText(str(DEFAULT_TEMP))
                        if not cycle_time.text().strip():
                            cycle_time.setText(DEFAULT_TIME)
        except Exception as e:
            logger.error(f"Error in auto_populate_first_row: {e}")

    def load_data(self, data):
        """Load schedule data into the table."""
        try:
            # Clear existing rows
            while self.table.rowCount() > 1:
                self.table.removeRow(1)
                
            # Add rows for data plus one extra for new entries
            while self.table.rowCount() < len(data) + 1:
                self.add_row()
                
            # Fill existing data
            for i, entry in enumerate(data):
                cycle_type = self.table.cellWidget(i, 0)
                start_temp = self.table.cellWidget(i, 1)
                end_temp = self.table.cellWidget(i, 2)
                cycle_time = self.table.cellWidget(i, 3)
                notes = self.table.cellWidget(i, 4)
                
                if all([cycle_type, start_temp, end_temp, cycle_time, notes]):
                    cycle_type.setCurrentText(entry['CycleType'])
                    start_temp.setText(str(entry['StartTemp']))
                    end_temp.setText(str(entry['EndTemp']))
                    cycle_time.setText(entry['CycleTime'])
                    notes.setText(entry.get('Notes', ''))
                
            # Add this line to trigger graph update
            self.parent().update_graph()  # Assuming the graph update method is in the parent
            
        except Exception as e:
            print(f"Error loading data: {e}")
            raise

    def exec_(self):
        """Override exec_ to handle test mode."""
        if self.test_mode:
            return QDialog.Accepted
        return super().exec_()

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