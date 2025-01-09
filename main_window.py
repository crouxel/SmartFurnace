def load_last_schedule(self):
    """Load the last opened schedule on startup."""
    last_schedule = self.settings.value('last_schedule', '')
    if last_schedule:
        self.load_schedule(last_schedule)
        self.update_graph() 

def load_schedule(self, schedule_name):
    """Load a schedule and show its graph."""
    try:
        self.current_schedule = []
        data = DatabaseManager.load_schedule(schedule_name)
        if data:
            print(f"Loading schedule data: {data}")  # Debug print
            for row in data:
                cycle = {
                    'CycleType': row[2],
                    'StartTemp': float(row[3]),
                    'EndTemp': float(row[4]),
                    'CycleTime': self.time_to_minutes(row[5])
                }
                self.current_schedule.append(cycle)
            print(f"Processed schedule: {self.current_schedule}")  # Debug print
            self.start_cycle_time = self.get_start_cycle_time()  # Reset start time
            self.update_graph()  # Draw everything
            return True
        return False
    except Exception as e:
        print(f"Error loading schedule: {e}")
        return False 

def update_graph(self):
    """Update the graph display."""
    if not self.current_schedule:  # Add guard clause
        self.plot_widget.clear()
        self.temp_display.setText("---°C")
        return

    if self.start_cycle_time is None:
        self.start_cycle_time = self.get_start_cycle_time()

    elapsed_time = (datetime.now() - self.start_cycle_time).total_seconds() / 60
    self.plot_widget.clear()
    
    theme = get_plot_theme()
    
    # Calculate total duration by converting time strings to minutes
    total_duration = sum(self.time_to_minutes(cycle['CycleTime']) for cycle in self.current_schedule)
    
    # Add current time line with updated style
    self.plot_widget.addLine(
        x=elapsed_time, 
        pen=pg.mkPen(theme['current_time'], width=2, style=Qt.DashLine)
    ) 