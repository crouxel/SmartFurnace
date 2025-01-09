# Changelog

## [Unreleased] - 2024-03-19 16:00 UTC
### Added
- Current time indicator in schedule graph
  - Added yellow dashed vertical line showing current position
  - Helps visualize progress through the schedule
  - Updates in real-time with temperature display

### Fixed
- Bug: Schedule loads but graph doesn't update on GUI open
  - Fixed data format mismatch in load_schedule()
  - Removed redundant regenerate_graph() method
  - Consolidated all graph updates into update_graph()
  - Added automatic schedule loading at startup
  - Added graph update trigger after schedule data load
  - Verified data format consistency across all related files:
    - Main.py: load_schedule()
    - schedule_window.py: load_data()
    - DatabaseManager: save_schedule(), load_schedule()

### Fixed
- Bug: Edit schedule gives an error
  - Root cause: Data format inconsistency between files
  - Fixed data format handling in schedule_window.py
  - Ensured consistent dictionary format: 
    {'CycleType', 'StartTemp', 'EndTemp', 'CycleTime', 'Notes'}
  - Added data format validation in load_data()
  - Added debug logging for data format tracking
  - Lesson learned: Always check ALL files when changing data formats

## [1.0.1] - 2024-03-18
### Added
- Temperature display now shows current value
- Added automatic graph updates
- Implemented schedule loading at startup

### Fixed
- Graph not updating in real-time
- Temperature display flickering
- Schedule selector not showing all available schedules

## [1.0.0] - 2024-03-15
### Added
- Initial release
- Basic temperature control
- Schedule creation and editing
- Real-time graph display
- Theme support 
Test suite hanging:
@pytest.fixture(autouse=True)
def cleanup_windows():
    yield
    for window in QApplication.topLevelWidgets():
        window.close()
        window.deleteLater()
    QApplication.processEvents()
Right-click menu in combo box:
def eventFilter(self, source, event):
    if event.type() == QEvent.MouseButtonPress and event.button() == Qt.RightButton:
        index = self.view().indexAt(event.pos())
        if index.isValid():
            text = self.itemText(index.row())
            if text and text != "Add Schedule":
                self.setCurrentIndex(index.row())
                self.context_menu.exec_(self.view().mapToGlobal(event.pos()))
                return True
    return super().eventFilter(source, event)
Graph regeneration KeyError:
def regenerate_graph(self):
    for cycle in self.current_schedule:
        # Changed from cycle['Duration'] to cycle['CycleTime']
        cycle_time_minutes = self.time_to_minutes(cycle['CycleTime'])
        x_data.extend([current_time, current_time + cycle_time_minutes])
Message box styling:
def get_message_box_style():
    theme = ThemeManager.get_current_theme()
    return f"""
        QMessageBox {{
            background-color: {theme['background']};
        }}
        QMessageBox QLabel {{
            color: {theme['text']};
        }}
    """

### Added
- Type hints:
```python
def validate_and_collect_entries(self, show_warnings: bool = True) -> Optional[List[Dict]]:
    """Validate and collect all entries from the table."""

## [1.0.0] - 2024-03-19
### Added
- Initial release 
Bug: Schedule loads but graph doesn't update on GUI open
Before:

def load_schedule(self, schedule_name):
    try:
        self.current_schedule = []
        data = DatabaseManager.load_schedule(schedule_name)
        if data:
            for row in data:
                cycle = {
                    'CycleType': row[2],
                    'StartTemp': float(row[3]),
                    'EndTemp': float(row[4]),
                    'CycleTime': self.time_to_minutes(row[5])
                }
                self.current_schedule.append(cycle)
            self.regenerate_graph()
            return True
        return False
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return False
After:

def load_schedule(self, schedule_name):
    try:
        self.current_schedule = []
        data = DatabaseManager.load_schedule(schedule_name)
        if data:
            for row in data:
                cycle = {
                    'CycleType': row['CycleType'],
                    'StartTemp': float(row['StartTemp']),
                    'EndTemp': float(row['EndTemp']),
                    'CycleTime': row['CycleTime']
                }
                self.current_schedule.append(cycle)
            self.start_cycle_time = self.get_start_cycle_time()
            self.update_graph()
            return True
        return False
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return False
Changes:

Fixed data format mismatch in load_schedule()
Removed redundant regenerate_graph() method
Consolidated all graph updates into update_graph()
Added automatic schedule loading at startup
Added graph update trigger after schedule data load

## [Unreleased]
### Changed
- Refactored database structure to use a more robust two-table system
  - `schedules` table stores schedule metadata (name, created/modified dates)
  - `schedule_entries` table stores individual cycle entries with foreign key to schedules
  - Removed old per-schedule table approach for better data integrity
  - Fixed issue where schedule updates weren't persisting
  - Added proper position tracking for cycle order

Before:
```sql
CREATE TABLE IF NOT EXISTS {schedule_name} (
    id INTEGER PRIMARY KEY,
    CycleType TEXT,
    StartTemp INTEGER,
    EndTemp INTEGER,
    CycleTime TEXT,
    Notes TEXT
)
```

After:
```sql
CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schedule_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER,
    cycle_type TEXT NOT NULL,
    start_temp INTEGER NOT NULL,
    end_temp INTEGER NOT NULL,
    duration TEXT NOT NULL,
    notes TEXT,
    position INTEGER,
    FOREIGN KEY (schedule_id) REFERENCES schedules (id)
        ON DELETE CASCADE
)
```