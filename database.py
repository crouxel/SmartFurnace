import sqlite3
import os
from datetime import datetime, timedelta

START_CYCLE_FILE = 'start_cycle.txt'

def fetch_all_schedules():
    conn = sqlite3.connect('SmartFurnace.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    schedules = [row[0] for row in cursor.fetchall()]
    conn.close()
    return schedules

def fetch_schedule(schedule):
    conn = sqlite3.connect('SmartFurnace.db')
    cursor = conn.cursor()
    cursor.execute(f"SELECT Cycle, StartTemp, EndTemp, CycleType, CycleTime FROM {schedule}")
    cycles = cursor.fetchall()
    conn.close()
    return cycles

def save_schedule(schedule_name, cycle_entries):
    try:
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {schedule_name} (
            Id INTEGER PRIMARY KEY,
            Cycle INTEGER NOT NULL,
            StartTemp INTEGER NOT NULL,
            EndTemp INTEGER NOT NULL,
            CycleType TEXT NOT NULL,
            CycleTime TIME NOT NULL,
            Notes TEXT NOT NULL
        )
        """)

        # Clear existing entries
        cursor.execute(f"DELETE FROM {schedule_name}")

        # Insert new entries
        cursor.executemany(f"""
        INSERT INTO {schedule_name} (Cycle, CycleType, StartTemp, EndTemp, CycleTime, Notes)
        VALUES (?, ?, ?, ?, ?,?)
        """, cycle_entries)

        conn.commit()
        conn.close()
    except sqlite3.OperationalError as e:
        print(f"Error saving schedule: {e}")

def delete_schedule(schedule_name):
    conn = sqlite3.connect('SmartFurnace.db')
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {schedule_name}")
    conn.commit()
    conn.close()

def set_start_cycle(start_time_label):
    start_cycle_time = datetime.now()
    with open(START_CYCLE_FILE, 'w') as f:
        f.write(start_cycle_time.isoformat())
    start_time_label.config(text=f"Start Time: {start_cycle_time.strftime('%I:%M:%S %p')}")
    print(f"Start cycle time set to: {start_cycle_time}")

def get_start_cycle_time():
    if not os.path.exists(START_CYCLE_FILE):
        raise ValueError("Start time is not set. Please call set_start_cycle() first.")
    with open(START_CYCLE_FILE, 'r') as f:
        start_cycle_time = datetime.fromisoformat(f.read().strip())
    return start_cycle_time

def get_current_temperature(start_time=None, schedule='A2'):
    if start_time is None:
        start_time = get_start_cycle_time()

    # Connect to the database
    conn = sqlite3.connect('SmartFurnace.db')
    cursor = conn.cursor()

    # Fetch the schedule from the database
    cursor.execute(f"SELECT Cycle, StartTemp, EndTemp, CycleType, CycleTime FROM {schedule}")
    cycles = cursor.fetchall()

    # Calculate the current temperature
    current_time = datetime.now()
    elapsed_time = current_time - start_time
    current_temp = None  # Initialize current_temp with a default value

    for cycle in cycles:
        cycle_time_minutes = int(cycle[4].split()[0])
        cycle_time = timedelta(minutes=cycle_time_minutes)

        if elapsed_time <= cycle_time:
            if cycle[3].lower() == 'ramp':
                temp_diff = cycle[2] - cycle[1]
                temp_per_minute = temp_diff / cycle_time_minutes
                current_temp = cycle[1] + (temp_per_minute * (elapsed_time.total_seconds() / 60))
            elif cycle[3].lower() == 'soak':
                current_temp = cycle[1]
            break
        else:
            elapsed_time -= cycle_time

    if current_temp is None:
        current_temp = cycles[-1][2]  # Default to the end temperature of the last cycle

    conn.close()
    return current_temp