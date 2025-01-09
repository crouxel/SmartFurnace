from typing import Dict, Any

# Database Configuration
DB_NAME = 'SmartFurnace.db'
COMPANY_NAME = 'YourCompany'
APP_NAME = 'TempController'

# UI Constants
WINDOW_SIZE = (800, 600)
BUTTON_WIDTH = 100
COMBO_WIDTH = 150
PADDING = 10
BORDER_RADIUS = 4

# Temperature Constants
DEFAULT_TEMP = 25
MIN_TEMP = 0
MAX_TEMP = 1200
TEMP_STEP = 5

# Time Constants
DEFAULT_TIME = "00:00:00"
TIME_FORMAT = "%H:%M:%S"

# Plot Configuration
PLOT_UPDATE_INTERVAL = 1000  # milliseconds
MAX_PLOT_POINTS = 100

# Style Constants
STYLE_DEFAULTS: Dict[str, Any] = {
    'padding': '5px',
    'margin': '2px',
    'border_radius': '4px',
    'font_size': '14px',
    'large_font_size': '48px',
    'button_height': '30px',
    'input_height': '25px'
}

# Error Messages
ERROR_MESSAGES = {
    'db_connection': "Failed to connect to database",
    'invalid_time': "Invalid time format. Please use HH:MM:SS",
    'invalid_temp': "Temperature must be between {} and {}".format(MIN_TEMP, MAX_TEMP),
    'save_failed': "Failed to save schedule",
    'delete_failed': "Failed to delete schedule",
    'load_failed': "Failed to load schedule"
}

# Success Messages
SUCCESS_MESSAGES = {
    'save_success': "Schedule saved successfully",
    'delete_success': "Schedule deleted successfully",
    'update_success': "Schedule updated successfully"
}

# Validation Patterns
TIME_PATTERN = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$'
TEMP_PATTERN = r'^\d+(\.\d+)?$'

def validate_temperature(temp: float) -> bool:
    """Validate temperature is within acceptable range."""
    return MIN_TEMP <= temp <= MAX_TEMP

def validate_time_format(time_str: str) -> bool:
    """Validate time string matches required format."""
    import re
    return bool(re.match(TIME_PATTERN, time_str)) 