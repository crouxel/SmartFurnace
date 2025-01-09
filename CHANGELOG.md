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