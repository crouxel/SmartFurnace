"""
test_smartfurnace.py - Progressive test suite
"""

import pytest
from pytestqt.qt_compat import qt_api
from PyQt5.QtCore import QSettings, Qt
import sys
import os

from styles import Theme, ThemeManager
from database import DatabaseManager
from schedule_window import ScheduleWindow
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