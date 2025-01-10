"""
test_smartfurnace.py - Progressive test suite
"""

import pytest
from pytestqt.qt_compat import qt_api
from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QIntValidator
import sys
import os

from styles import Theme, ThemeManager
from database import DatabaseManager
from schedule_window import ScheduleWindow
from Main import MainWindow
from constants import MIN_TEMP, MAX_TEMP, validate_temperature, validate_time_format, DEFAULT_TEMP, DEFAULT_TIME

@pytest.fixture
def setup_database():
    """Create test database."""
    test_db = "test_smartfurnace.db"
    original_db = DatabaseManager.DB_NAME
    DatabaseManager.DB_NAME = test_db
    DatabaseManager.initialize_database()
    yield
    DatabaseManager.DB_NAME = original_db
    if os.path.exists(test_db):
        os.remove(test_db)

@pytest.fixture
def suppress_qt_warnings(monkeypatch):
    """Suppress QMessageBox warnings during tests."""
    def mock_warning(*args, **kwargs):
        pass
    
    monkeypatch.setattr(QMessageBox, 'warning', mock_warning)
    monkeypatch.setattr(QMessageBox, 'critical', mock_warning)
    monkeypatch.setattr(QMessageBox, 'information', mock_warning)

def test_database_operations(setup_database):
    """Test basic database operations."""
    assert DatabaseManager.save_schedule('Test Schedule', []) is True
    schedules = DatabaseManager.fetch_all_schedules()
    assert 'Test Schedule' in schedules
    DatabaseManager.delete_schedule('Test Schedule')
    schedules = DatabaseManager.fetch_all_schedules()
    assert 'Test Schedule' not in schedules

def test_theme_operations():
    """Test basic theme operations."""
    settings = QSettings('TestCompany', 'TestApp')
    settings.clear()
    
    ThemeManager.set_theme(Theme.DARK_INDUSTRIAL)
    theme = ThemeManager.get_current_theme()
    assert theme['name'] == 'Dark Industrial'

def test_validation_functions():
    """Test validation functions from constants."""
    # Temperature validation
    assert validate_temperature(100) is True
    assert validate_temperature(MIN_TEMP - 1) is False
    assert validate_temperature(MAX_TEMP + 1) is False
    
    # Time format validation
    assert validate_time_format('01:00:00') is True
    assert validate_time_format('1:00') is False
    assert validate_time_format('abc') is False

def test_default_values(qtbot):
    """Test auto-population of default values in first row."""
    window = ScheduleWindow()
    qtbot.addWidget(window)
    
    # Get first row widgets
    cycle_type_combo = window.table.cellWidget(0, 0)  # First row, cycle type column
    start_temp_input = window.table.cellWidget(0, 1)  # First row, start temp column
    cycle_time_input = window.table.cellWidget(0, 3)  # First row, cycle time column
    
    # Test Ramp defaults
    cycle_type_combo.setCurrentText('Ramp')
    qtbot.wait(100)  # Wait for any event processing
    assert start_temp_input.text() == str(DEFAULT_TEMP)
    assert cycle_time_input.text() == DEFAULT_TIME
    
    # Test Soak defaults
    cycle_type_combo.setCurrentText('Soak')
    qtbot.wait(100)  # Wait for any event processing
    assert start_temp_input.text() == str(DEFAULT_TEMP)
    assert cycle_time_input.text() == DEFAULT_TIME
    
    window.close() 

def test_first_row_auto_population(qtbot):
    """Test that first row auto-populates correctly when cycle type changes."""
    window = ScheduleWindow()
    qtbot.addWidget(window)
    
    # Get first row widgets
    first_row = 0
    cycle_type_combo = window.table.cellWidget(first_row, 0)
    start_temp_input = window.table.cellWidget(first_row, 1)
    cycle_time_input = window.table.cellWidget(first_row, 3)
    
    # Test Ramp defaults
    cycle_type_combo.setCurrentText('Ramp')
    qtbot.wait(100)  # Allow for event processing
    assert start_temp_input.text() == str(DEFAULT_TEMP), "Start temp should be default for Ramp"
    assert cycle_time_input.text() == DEFAULT_TIME, "Cycle time should be default for Ramp"
    
    # Test Soak defaults
    cycle_type_combo.setCurrentText('Soak')
    qtbot.wait(100)  # Allow for event processing
    assert start_temp_input.text() == str(DEFAULT_TEMP), "Start temp should be default for Soak"
    assert cycle_time_input.text() == DEFAULT_TIME, "Cycle time should be default for Soak"
    
    window.close() 

def test_validate_and_collect_entries(qtbot, suppress_qt_warnings):
    """Test validation and collection of schedule entries."""
    window = ScheduleWindow()
    qtbot.addWidget(window)
    
    def test_valid_entry():
        # Set up a valid row
        cycle_type = window.table.cellWidget(0, 0)
        start_temp = window.table.cellWidget(0, 1)
        end_temp = window.table.cellWidget(0, 2)
        cycle_time = window.table.cellWidget(0, 3)
        notes = window.table.cellWidget(0, 4)
        
        cycle_type.setCurrentText('Ramp')
        start_temp.setText('25')
        end_temp.setText('100')
        cycle_time.setText('01:00:00')
        notes.setText('Test ramp')
        
        entries = window.validate_and_collect_entries(show_warnings=False)
        assert entries is not None
        assert len(entries) == 1, "Should have one valid entry"
        expected = {
            'CycleType': 'Ramp',
            'StartTemp': 25,
            'EndTemp': 100,
            'Duration': '01:00:00',
            'Notes': 'Test ramp'
        }
        assert entries[0] == expected, "Entry data should match expected format"
    
    # Test Case 2: Invalid temperature
    def test_invalid_temperature():
        start_temp = window.table.cellWidget(0, 1)
        start_temp.setText('9999')  # Invalid temperature
        
        entries = window.validate_and_collect_entries(show_warnings=False)
        assert entries is None, "Invalid temperature should return None"
    
    # Test Case 3: Invalid time format
    def test_invalid_time():
        start_temp = window.table.cellWidget(0, 1)
        cycle_time = window.table.cellWidget(0, 3)
        
        start_temp.setText('25')  # Reset to valid temperature
        cycle_time.setText('1:00')  # Invalid time format
        
        entries = window.validate_and_collect_entries(show_warnings=False)
        assert entries is None, "Invalid time format should return None"
    
    # Test Case 4: Empty required fields
    def test_empty_fields():
        start_temp = window.table.cellWidget(0, 1)
        end_temp = window.table.cellWidget(0, 2)
        cycle_time = window.table.cellWidget(0, 3)
        
        start_temp.setText('')
        end_temp.setText('')
        cycle_time.setText('')
        
        entries = window.validate_and_collect_entries(show_warnings=False)
        assert entries is None, "Empty required fields should return None"
    
    # Run all test cases
    test_valid_entry()
    test_invalid_temperature()
    test_invalid_time()
    test_empty_fields()
    
    window.close() 

def test_schedule_persistence(qtbot, setup_database):
    """Test that schedules are properly saved and loaded."""
    window = ScheduleWindow()
    qtbot.addWidget(window)
    
    # Create test schedule
    cycle_type = window.table.cellWidget(0, 0)
    start_temp = window.table.cellWidget(0, 1)
    end_temp = window.table.cellWidget(0, 2)
    cycle_time = window.table.cellWidget(0, 3)
    notes = window.table.cellWidget(0, 4)
    
    test_data = ('Ramp', '25', '100', '01:00:00', 'Test ramp')
    cycle_type.setCurrentText(test_data[0])
    start_temp.setText(test_data[1])
    end_temp.setText(test_data[2])
    cycle_time.setText(test_data[3])
    notes.setText(test_data[4])
    
    # Save schedule
    schedule_name = "Test Schedule"
    entries = window.validate_and_collect_entries(show_warnings=False)
    assert DatabaseManager.save_schedule(schedule_name, entries)
    
    # Create new window to test loading
    window.close()
    new_window = ScheduleWindow()
    qtbot.addWidget(new_window)
    
    # Load and verify data
    loaded_data = DatabaseManager.load_schedule(schedule_name)
    assert loaded_data is not None
    assert len(loaded_data) == 1
    assert loaded_data[0]['CycleType'] == test_data[0]
    assert str(loaded_data[0]['StartTemp']) == test_data[1]
    assert str(loaded_data[0]['EndTemp']) == test_data[2]
    assert loaded_data[0]['Duration'] == test_data[3]
    assert loaded_data[0]['Notes'] == test_data[4]
    
    new_window.close() 

@pytest.fixture(autouse=True)
def cleanup_windows():
    """Fixture to clean up any remaining windows after each test."""
    yield
    for window in QApplication.topLevelWidgets():
        window.close()
        window.deleteLater()
    QApplication.processEvents()

def test_add_schedule_functionality(qtbot, setup_database):
    """Test the complete add schedule workflow."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    try:
        initial_schedules = DatabaseManager.fetch_all_schedules()
        initial_count = len(initial_schedules)
        
        # Select "Add Schedule"
        combo = window.combo
        add_schedule_index = combo.findText("Add Schedule")
        assert add_schedule_index != -1
        combo.setCurrentIndex(add_schedule_index)
        qtbot.wait(100)
        
        # Verify schedule window opened
        assert hasattr(window, 'schedule_window')
        schedule_window = window.schedule_window
        
        # Add test data
        table = schedule_window.table
        cycle_type = table.cellWidget(0, 0)
        start_temp = table.cellWidget(0, 1)
        end_temp = table.cellWidget(0, 2)
        cycle_time = table.cellWidget(0, 3)
        notes = table.cellWidget(0, 4)
        
        cycle_type.setCurrentText('Ramp')
        start_temp.setText('25')
        end_temp.setText('100')
        cycle_time.setText('01:00:00')
        notes.setText('Test ramp')
        
        # Save schedule
        schedule_window.save_schedule("Test Schedule")
        qtbot.wait(100)
        
        # Verify schedule was added
        final_schedules = DatabaseManager.fetch_all_schedules()
        assert len(final_schedules) > initial_count
        
    finally:
        window.close()
        window.deleteLater()
        QApplication.processEvents()

def test_custom_combobox(qtbot):
    """Test CustomComboBox functionality."""
    # Create parent window and combobox
    window = MainWindow()
    qtbot.addWidget(window)
    combo = window.combo
    
    # Add test items
    test_schedule = "Test Schedule"
    DatabaseManager.save_schedule(test_schedule, [{
        'CycleType': 'Ramp',
        'StartTemp': 25,
        'EndTemp': 100,
        'Duration': '01:00:00',
        'Notes': 'Test ramp'
    }])
    window.update_schedule_menu()
    
    # Test right-click with closed combobox
    combo.setCurrentText(test_schedule)
    qtbot.mouseClick(combo, Qt.RightButton)
    assert combo.context_menu.isVisible()
    combo.context_menu.hide()
    
    # Test right-click with open combobox
    combo.showPopup()
    viewport = combo.view().viewport()
    index = combo.findText(test_schedule)
    rect = combo.view().visualRect(combo.model().index(index, 0))
    qtbot.mouseClick(viewport, Qt.RightButton, pos=rect.center())
    assert combo.context_menu.isVisible()
    assert combo.currentText() == test_schedule
    
    # Clean up
    window.close()
    DatabaseManager.delete_schedule(test_schedule) 

def test_schedule_window_basics(qtbot):
    """Test basic ScheduleWindow functionality."""
    window = ScheduleWindow()
    qtbot.addWidget(window)
    
    # Test initial state
    assert window.table.rowCount() == 1, "Should start with one row"
    assert window.table.columnCount() == 6, "Should have 6 columns"
    
    # Test add row functionality
    add_button = window.table.cellWidget(0, 5)
    qtbot.mouseClick(add_button, Qt.LeftButton)
    assert window.table.rowCount() == 2, "Should add a new row"
    
    # Test row widgets
    for row in range(window.table.rowCount()):
        assert isinstance(window.table.cellWidget(row, 0), QComboBox), f"Row {row} missing cycle type combo"
        assert isinstance(window.table.cellWidget(row, 1), QLineEdit), f"Row {row} missing start temp input"
        assert isinstance(window.table.cellWidget(row, 2), QLineEdit), f"Row {row} missing end temp input"
        assert isinstance(window.table.cellWidget(row, 3), QLineEdit), f"Row {row} missing cycle time input"
        assert isinstance(window.table.cellWidget(row, 4), QLineEdit), f"Row {row} missing notes input"
    
    window.close()

def test_validators(qtbot):
    """Test input validation."""
    window = ScheduleWindow()
    qtbot.addWidget(window)
    
    # Get first row widgets
    start_temp = window.table.cellWidget(0, 1)
    end_temp = window.table.cellWidget(0, 2)
    cycle_time = window.table.cellWidget(0, 3)
    
    # Test temperature validation
    start_temp.setText('9999')  # Above MAX_TEMP
    assert not validate_temperature(int(start_temp.text()))
    
    start_temp.setText('25')  # Valid temperature
    assert validate_temperature(int(start_temp.text()))
    
    # Test time format validation
    cycle_time.setText('1:00')  # Invalid format
    assert not validate_time_format(cycle_time.text())
    
    cycle_time.setText('01:00:00')  # Valid format
    assert validate_time_format(cycle_time.text())
    
    window.close() 

def test_graph_regeneration(qtbot):
    """Test that graph updates correctly with schedule data."""
    window = MainWindow()
    qtbot.addWidget(window)
    
    try:
        # Create a test schedule
        test_data = [{
            'CycleType': 'Ramp',
            'StartTemp': 25,
            'EndTemp': 100,
            'CycleTime': '01:00:00',
            'Notes': 'Test ramp'
        }]
        DatabaseManager.save_schedule("Test Graph Schedule", test_data)
        
        # Update menu and select our test schedule
        window.update_schedule_menu()
        window.combo.setCurrentText("Test Graph Schedule")
        qtbot.wait(100)
        
        # Verify graph data
        assert window.current_schedule is not None
        assert len(window.current_schedule) > 0
        assert window.current_schedule[0]['StartTemp'] == 25
        assert window.current_schedule[0]['EndTemp'] == 100
        assert window.current_schedule[0]['CycleTime'] == '01:00:00'
        
        # Clean up
        DatabaseManager.delete_schedule("Test Graph Schedule")
        
    finally:
        window.close()
        window.deleteLater()
        QApplication.processEvents() 

def test_time_displays(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
    assert window.startTimeDisplay.text() == "Start: --:--:--"
    assert window.currentTimeDisplay.text() == "Current: --:--:--"
    assert window.endTimeDisplay.text() == "End: --:--:--" 