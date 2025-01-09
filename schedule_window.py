from PyQt5.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, 
    QHBoxLayout, QPushButton, QInputDialog, QMessageBox,
    QComboBox, QLineEdit, QHeaderView, QWidget
)
from PyQt5.QtGui import QPalette, QIntValidator
from PyQt5.QtCore import Qt, QObject
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

class schedule_window(QDialog):
    def __init__(self, parent=None, existing_schedule=None):
        super().__init__(parent)
        logger.debug(f"Initializing schedule_window - Mode: {'Edit' if existing_schedule else 'Add'}")
        
        # Initialize class attributes
        self.test_mode = False
        self.existing_schedule = existing_schedule
        self.schedule_data = None
        
        # Set window title based on mode
        title = "Edit Schedule" if existing_schedule else "Add Schedule"
        logger.debug(f"Setting window title to: {title}")
        self.setWindowTitle(title)
        
        # Setup main UI (table, etc)
        self.setup_ui()
        
        # Setup different button layouts based on mode
        logger.debug("Setting up button layout")
        self.setup_buttons()
        
        # Initialize with empty row or load existing data
        if existing_schedule:
            logger.debug(f"Loading existing schedule: {existing_schedule}")
            self.load_schedule(existing_schedule)
        else:
            logger.debug("Adding empty row for new schedule")
            self.add_row(-1)  # Add first row at position -1 (will become row 0)

    def setup_buttons(self):
        """Create button layout based on whether we're editing or adding"""
        logger.debug(f"Setting up buttons for mode: {'Edit' if self.existing_schedule else 'Add'}")
        button_layout = QHBoxLayout()
        
        if self.existing_schedule:
            logger.debug("Creating Edit mode buttons (Update + Save As)")
            update_btn = QPushButton("Update")
            save_as_btn = QPushButton("Save As...")
            update_btn.clicked.connect(self.update_schedule)
            save_as_btn.clicked.connect(self.save_as_schedule)
            button_layout.addWidget(update_btn)
            button_layout.addWidget(save_as_btn)
        else:
            logger.debug("Creating Add mode button (Save)")
            save_btn = QPushButton("Save")
            save_btn.clicked.connect(self.save_schedule)
            button_layout.addWidget(save_btn)
        
        logger.debug("Adding Cancel button")
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        logger.debug("Adding button layout to main layout")
        self.layout().addLayout(button_layout)

    def setup_ui(self):
        """Set up the user interface."""
        if self.test_mode:
            return
        
        self.setStyleSheet(get_dialog_style())
        
        # Force text color for all widgets
        palette = self.palette()
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        self.setPalette(palette)
        
        self.resize(800, 400)  # Set initial window size
        
        layout = QVBoxLayout()
        layout.setSpacing(10)  # Add spacing between elements
        
        # Set up table
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # Don't create buttons here - they'll be created by setup_buttons()
        self.setLayout(layout)

    def setup_table(self):
        """Set up the table widget."""
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # Add, Type, Start, End, Time, Notes, Delete
        self.table.setHorizontalHeaderLabels(["Add", "Type", "Start Temp", "End Temp", "Time", "Notes", "Delete"])
        
        # Set column widths
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)  # Add button
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)  # Delete button
        self.table.setColumnWidth(0, 30)  # Add button width
        self.table.setColumnWidth(6, 30)  # Delete button width
        
        # Add initial row only for new schedules
        if not self.existing_schedule:
            self.add_row(0)  # Add first row at index 0

    def add_row(self, position):
        """Add a row after the specified position."""
        logger.debug(f"Adding row after position {position}")
        self.table.insertRow(position + 1)
        current_row = position + 1
        
        # Create widgets for the new row
        add_btn = QPushButton("+")
        add_btn.clicked.connect(lambda: self.add_row(current_row))
        
        cycle_type = QComboBox()
        cycle_type.addItems(["", "Ramp", "Soak"])
        cycle_type.setStyleSheet(get_combo_style())
        cycle_type.currentTextChanged.connect(lambda: self.on_cycle_type_changed(current_row))
        
        start_temp = QLineEdit()
        end_temp = QLineEdit()
        cycle_time = QLineEdit()
        notes = QLineEdit()
        
        # Set default time
        cycle_time.setText("00:00:00")
        
        # If there's a previous row, set start temp to previous end temp
        if current_row > 0:
            prev_end_temp = self.table.cellWidget(current_row - 1, 3)  # End temp column
            if prev_end_temp and prev_end_temp.text():
                start_temp.setText(prev_end_temp.text())
        
        # Create delete button
        delete_btn = QPushButton("-")
        delete_btn.clicked.connect(lambda: self.delete_row(current_row))
        
        # Add widgets to the row
        self.table.setCellWidget(current_row, 0, add_btn)      # Add button first
        self.table.setCellWidget(current_row, 1, cycle_type)   # Then cycle type
        self.table.setCellWidget(current_row, 2, start_temp)   # Start temp
        self.table.setCellWidget(current_row, 3, end_temp)     # End temp
        self.table.setCellWidget(current_row, 4, cycle_time)   # Time
        self.table.setCellWidget(current_row, 5, notes)        # Notes
        self.table.setCellWidget(current_row, 6, delete_btn)   # Delete button last
        
        # Update subsequent rows' start temperatures
        self.update_start_temperatures(current_row + 1)
        
        logger.debug(f"Row added at index {current_row}")

    def delete_row(self, row):
        """Delete a row from the table."""
        if self.table.rowCount() > 1:  # Prevent deleting the last row
            self.table.removeRow(row)
            # Update start temperatures for remaining rows
            self.update_start_temperatures(row)
        else:
            QMessageBox.warning(self, "Warning", "Cannot delete the last row")

    def update_start_temperatures(self, start_row=0):
        """Update start temperatures based on previous row's end temperature."""
        for row in range(start_row, self.table.rowCount()):
            if row > 0:
                prev_end_temp = self.table.cellWidget(row - 1, 3)  # End temp column
                current_start_temp = self.table.cellWidget(row, 2)  # Start temp column
                if prev_end_temp and prev_end_temp.text() and current_start_temp:
                    current_start_temp.setText(prev_end_temp.text())

    def load_data(self):
        """Load existing schedule data into the table."""
        try:
            data = DatabaseManager.load_schedule(self.existing_schedule)
            if data:
                # Clear existing rows
                self.table.setRowCount(0)
                
                # Add rows for each entry
                last_row = -1  # Start with -1 so first add_row will be at position 0
                for entry in data:
                    self.add_row(last_row)  # This will handle start temp propagation
                    current_row = last_row + 1
                    last_row = current_row
                    
                    # Set the values
                    self.table.cellWidget(current_row, 1).setCurrentText(entry['CycleType'])
                    self.table.cellWidget(current_row, 2).setText(str(entry['StartTemp']))
                    self.table.cellWidget(current_row, 3).setText(str(entry['EndTemp']))
                    self.table.cellWidget(current_row, 4).setText(entry['CycleTime'])
                    self.table.cellWidget(current_row, 5).setText(entry.get('Notes', ''))
                
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading data: {e}", exc_info=True)
            raise

    def on_cycle_type_changed(self, row):
        """Handle cycle type changes."""
        try:
            cycle_type = self.table.cellWidget(row, 1).currentText()  # Column 1 is cycle type
            logger.debug(f"Cycle type changed in row {row} to: {cycle_type}")
            
            if cycle_type == "Soak":
                # Get start temp value
                start_temp_widget = self.table.cellWidget(row, 2)  # Column 2 is start temp
                if start_temp_widget and start_temp_widget.text():
                    # Set end temp to match start temp
                    end_temp_widget = self.table.cellWidget(row, 3)  # Column 3 is end temp
                    end_temp_widget.setText(start_temp_widget.text())
                    logger.debug(f"Set end temp to match start temp: {start_temp_widget.text()}")
            
            # Set default time if needed
            cycle_time = self.table.cellWidget(row, 4)  # Column 4 is time
            if cycle_type in ["Ramp", "Soak"] and (not cycle_time.text() or cycle_time.text() == ""):
                cycle_time.setText("00:00:00")
                logger.debug(f"Set initial time for row {row}")
            
        except Exception as e:
            logger.error(f"Error in on_cycle_type_changed: {e}", exc_info=True)

    def update_schedule(self):
        """Update the existing schedule."""
        try:
            entries = self.validate_and_collect_entries()
            if entries:
                # Convert dictionary entries to tuples in the EXACT format DatabaseManager expects
                formatted_entries = [
                    (
                        entry['CycleType'],
                        entry['StartTemp'],
                        entry['EndTemp'],
                        entry['CycleTime'],
                        entry.get('Notes', '')
                    ) for entry in entries
                ]
                
                logger.debug(f"Formatted entries for database: {formatted_entries}")
                
                if DatabaseManager.save_schedule(self.existing_schedule, formatted_entries):
                    QMessageBox.information(self, "Success", SUCCESS_MESSAGES['update_success'])
                    if hasattr(self.parent(), 'update_schedule_menu'):
                        self.parent().update_schedule_menu()
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", ERROR_MESSAGES['save_failed'])
        except Exception as e:
            logger.error(f"Error updating schedule: {e}", exc_info=True)
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
        """Validate and collect all entries from the table."""
        entries = []
        for row in range(self.table.rowCount()):
            try:
                # Get widgets from correct columns (shifted right by 1 due to add button)
                cycle_type = self.table.cellWidget(row, 1)  # Was 0, now 1
                start_temp = self.table.cellWidget(row, 2)  # Was 1, now 2
                end_temp = self.table.cellWidget(row, 3)    # Was 2, now 3
                cycle_time = self.table.cellWidget(row, 4)  # Was 3, now 4
                notes = self.table.cellWidget(row, 5)       # Was 4, now 5
                
                # Validate cycle type
                if not cycle_type.currentText():
                    if show_warnings:
                        QMessageBox.warning(self, "Validation Error", f"Row {row + 1}: Cycle type is required")
                    return None
                    
                # Validate temperatures
                try:
                    start_temp_val = float(start_temp.text())
                    end_temp_val = float(end_temp.text())
                except ValueError:
                    if show_warnings:
                        QMessageBox.warning(self, "Validation Error", 
                                          f"Row {row + 1}: Start and End temperatures must be numbers")
                    return None
                    
                # Validate time format and non-zero duration
                time_text = cycle_time.text()
                if not self.validate_time_format(time_text):
                    if show_warnings:
                        QMessageBox.warning(self, "Validation Error", 
                                          f"Row {row + 1}: Time must be in format HH:MM:SS")
                    return None
                
                # Check for zero duration
                if time_text == "00:00:00":
                    if show_warnings:
                        QMessageBox.warning(self, "Validation Error", 
                                          f"Row {row + 1}: Duration cannot be zero")
                    return None
                    
                # Collect entry
                entry = {
                    'CycleType': cycle_type.currentText(),
                    'StartTemp': start_temp_val,
                    'EndTemp': end_temp_val,
                    'CycleTime': time_text,
                    'Notes': notes.text()
                }
                entries.append(entry)
                
            except Exception as e:
                logger.error(f"Row {row}: Error - {str(e)}")
                if show_warnings:
                    QMessageBox.warning(self, "Error", f"Error processing row {row + 1}: {str(e)}")
                return None
                
        return entries

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
                        entry['CycleTime'],
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

    def save_schedule(self):
        """Save a new schedule."""
        try:
            name, ok = QInputDialog.getText(self, 'Save Schedule', 'Enter schedule name:')
            if ok and name:
                entries = self.validate_and_collect_entries()
                if entries:
                    # Convert entries to list of tuples for DatabaseManager
                    formatted_entries = [(
                        entry['CycleType'],
                        entry['StartTemp'],
                        entry['EndTemp'],
                        entry['CycleTime'],
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
            logger.error(f"Error saving schedule: {e}")
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

    def load_schedule(self, schedule_name):
        """Load an existing schedule into the table."""
        logger.debug(f"Loading schedule: {schedule_name}")
        try:
            # Load data from database
            data = DatabaseManager.load_schedule(schedule_name)
            logger.debug(f"Loaded data from database: {data}")
            
            if not data:
                logger.warning(f"No data found for schedule: {schedule_name}")
                return False
            
            # Clear existing rows
            self.table.setRowCount(0)
            
            # Add rows for each cycle
            last_row = -1  # Start with -1 so first add_row will be at position 0
            for row_data in data:
                logger.debug(f"Processing row: {row_data}")
                self.add_row(last_row)  # Pass the position
                current_row = last_row + 1
                last_row = current_row
                
                # Set data in the new row
                cycle_type = self.table.cellWidget(current_row, 1)
                start_temp = self.table.cellWidget(current_row, 2)
                end_temp = self.table.cellWidget(current_row, 3)
                cycle_time = self.table.cellWidget(current_row, 4)
                notes = self.table.cellWidget(current_row, 5)
                
                cycle_type.setCurrentText(row_data['CycleType'])
                start_temp.setText(str(row_data['StartTemp']))
                end_temp.setText(str(row_data['EndTemp']))
                cycle_time.setText(row_data['CycleTime'])
                notes.setText(row_data.get('Notes', ''))
                
            return True
        except Exception as e:
            logger.error(f"Error loading schedule: {e}", exc_info=True)
            raise

    def exec_(self):
        """Override exec_ to handle test mode."""
        if self.test_mode:
            return QDialog.Accepted
        return super().exec_()