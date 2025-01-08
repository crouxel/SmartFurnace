import sqlite3
from datetime import datetime, timedelta
import argparse
import os

# File to store the start cycle time
START_CYCLE_FILE = 'start_cycle_time.txt'

def set_start_cycle():
    start_cycle_time = datetime.now()
    with open(START_CYCLE_FILE, 'w') as f:
        f.write(start_cycle_time.isoformat())
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
            if cycle[3] == 'ramp':
                temp_diff = cycle[2] - cycle[1]
                temp_per_minute = temp_diff / cycle_time_minutes
                current_temp = cycle[1] + (temp_per_minute * elapsed_time.total_seconds() / 60)
            elif cycle[3] == 'soak':
                current_temp = cycle[1]
            break
        else:
            elapsed_time -= cycle_time

    if current_temp is None:
        raise ValueError("Elapsed time exceeds total cycle time")

    conn.close()
    return current_temp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Furnace Temperature Control")
    parser.add_argument("action", choices=["StartCycle", "GetCurrentTemp"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "StartCycle":
        set_start_cycle()
    elif args.action == "GetCurrentTemp":
        try:
            current_temp = get_current_temperature()
            print(f"The current temperature is: {current_temp:.2f}°C")
        except ValueError as e:
            print(e)