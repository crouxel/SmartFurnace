# Changelog

## [Unreleased] - 2024-03-19 16:00 UTC
### Fixed
- Bug: Schedule loads but graph doesn't update on GUI open

Before:
```python
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
```

After:
```python
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
```

Changes:
- Fixed data format mismatch in load_schedule()
- Removed redundant regenerate_graph() method
- Consolidated all graph updates into update_graph()
- Added automatic schedule loading at startup
- Added graph update trigger after schedule data load

[Previous changes remain unchanged...] 