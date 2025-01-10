# SmartFurnace Controller

A PyQt5-based furnace control interface for managing temperature schedules and generating programming codes.

© 2024 Christopher Rouxel. All rights reserved.
This software is provided under the MIT License. Any redistribution must maintain attribution.

## Table of Contents
- [SmartFurnace Controller](#smartfurnace-controller)
  - [Table of Contents](#table-of-contents)
  - [Project Structure](#project-structure)
  - [Installation \& Running](#installation--running)
    - [Method 1: From Source (Recommended for Development)](#method-1-from-source-recommended-for-development)
    - [Method 2: Executable (Windows)](#method-2-executable-windows)
  - [Application Data Locations](#application-data-locations)
    - [Windows](#windows)
    - [Linux](#linux)
    - [macOS](#macos)
  - [Component Details](#component-details)
    - [Schedule Window](#schedule-window)
    - [Theme System](#theme-system)
    - [Custom Icons](#custom-icons)
  - [Technical Notes](#technical-notes)
    - [Custom ComboBox Implementation](#custom-combobox-implementation)
  - [Critical Functions](#critical-functions)
    - [Temperature Calculation](#temperature-calculation)
    - [Graph Updates](#graph-updates)

## Project Structure
```
SmartFurnace/
├── Main.py              # Application core
├── database.py          # Data persistence
├── schedule_window.py   # Schedule editor
├── styles.py            # Theme management
├── constants.py         # Configuration
├── custom_combobox.py   # UI components
├── options_dialog.py    # Theme settings
├── resources.py         # Custom icons
└── requirements.txt     # Dependencies
```

## Installation & Running

### Method 1: From Source (Recommended for Development)
1. Clone the repository
2. Create and activate virtual environment:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python Main.py
```

### Method 2: Executable (Windows)
1. Download SmartFurnace-v1.0.0.zip from Releases
2. Extract to desired location
3. Run SmartFurnace.exe

Note: The executable includes all dependencies and doesn't require Python installation.

## Application Data Locations

### Windows
```
C:/Users/<username>/AppData/Local/SmartFurnace/
├── database.db          # Schedule database
├── start_cycle_time.txt # Current cycle start time
└── settings.ini         # Theme and last used schedule
```

### Linux
```
~/.local/share/SmartFurnace/
├── database.db
├── start_cycle_time.txt
└── settings.ini
```

### macOS
```
~/Library/Application Support/SmartFurnace/
├── database.db
├── start_cycle_time.txt
└── settings.ini
```

## Component Details

### Schedule Window
The Schedule Window provides the interface for creating and editing temperature cycles:
```python
def save_schedule(self, name):
    """Save the current schedule to database."""
    try:
        entries = self.validate_and_collect_entries()
        if entries and DatabaseManager.save_schedule(name, entries):
            self.parent().update_schedule_menu()
            return True
    except Exception as e:
        logger.error(f"Failed to save schedule: {e}")
        return False
```

Features:
- Add/remove temperature cycles
- Set cycle types (Ramp/Soak)
- Configure temperatures and durations
- Add notes for each cycle

### Theme System
The application uses a customizable theme system:

```python
class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options")
        self.setFixedWidth(400)
        
    def on_theme_changed(self, theme_name):
        """Handle theme changes and apply them immediately."""
        for theme in Theme:
            if theme.value['name'] == theme_name:
                ThemeManager.set_theme(theme)
                if self.parent():
                    self.parent().apply_theme()
```

Add new themes by modifying ThemeManager:
```python
NEW_THEME = {
    'name': 'Custom Theme',
    'background': '#2b2b2b',
    'primary': '#ffffff',
    'secondary': '#808080',
    'accent': '#4a9eff',
    'grid': '#404040',
    'current_time': '#ffff00'
}

ThemeManager.THEMES['CUSTOM'] = NEW_THEME
```

### Custom Icons
The application uses vector-based icons that adapt to the current theme:

```python
class GearIcon(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
    
    def paintEvent(self, event):
        """Draw a gear icon that matches the current theme."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        theme = ThemeManager.get_current_theme()
        color = QColor('white') if theme['name'] != 'Light Industrial' else QColor(theme['text'])
        painter.setPen(QPen(color, 2))
```

## Technical Notes

### Custom ComboBox Implementation
The schedule selector uses a custom ComboBox with context menu support:

```python
class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.context_menu = QMenu(self)
        self.view().viewport().installEventFilter(self)
        
    def mousePressEvent(self, event):
        """Handle right-clicks on the main combobox."""
        if event.button() == Qt.RightButton:
            current_text = self.currentText()
            if current_text and current_text != "Add Schedule":
                self.context_menu.exec_(self.mapToGlobal(event.pos()))
        else:
            super().mousePressEvent(event)
    
    def eventFilter(self, source, event):
        """Handle right-clicks in the dropdown list."""
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
            index = self.view().indexAt(event.pos())
            if index.isValid():
                text = self.itemText(index.row())
                if text and text != "Add Schedule":
                    self.setCurrentIndex(index.row())
                    self.context_menu.exec_(self.view().mapToGlobal(event.pos()))
                    return True
        return super().eventFilter(source, event)
```

## Critical Functions

### Temperature Calculation
The entire application depends on these core functions:

```python
def time_to_minutes(self, time_str):
    """Convert time string (HH:MM:SS) to minutes."""
    try:
        h, m, s = map(int, time_str.split(':'))
        return h * 60 + m + (1 if s > 0 else 0)  # Round up if there are seconds
    except ValueError:
        return 0

def get_current_temperature(self, elapsed_minutes):
    """Calculate the current temperature based on elapsed time."""
    if not self.current_schedule:
        return 0
        
    current_time = 0
    for cycle in self.current_schedule:
        cycle_time = self.time_to_minutes(cycle['CycleTime'])
        if current_time + cycle_time > elapsed_minutes:
            # We're in this cycle
            cycle_progress = (elapsed_minutes - current_time) / cycle_time
            temp_diff = float(cycle['EndTemp']) - float(cycle['StartTemp'])
            return float(cycle['StartTemp']) + (temp_diff * cycle_progress)
        current_time += cycle_time
    
    # Past all cycles, return last temperature
    return float(self.current_schedule[-1]['EndTemp'])
```

### Graph Updates
Real-time display relies on:
```python
def update_graph(self):
    """Update the graph display."""
    if not self.current_schedule:
        self.plot_widget.clear()
        self.temp_display.setText("---°C")
        return

    elapsed_time = (datetime.now() - self.start_cycle_time).total_seconds() / 60
    self.plot_widget.clear()
    
    theme = get_plot_theme()
    
    # Calculate total duration
    total_duration = sum(self.time_to_minutes(cycle['CycleTime']) 
                        for cycle in self.current_schedule)
    
    # Add current time line
    self.plot_widget.addLine(
        x=elapsed_time, 
        pen=pg.mkPen(theme['current_time'], width=2, style=Qt.DashLine)
    )
```