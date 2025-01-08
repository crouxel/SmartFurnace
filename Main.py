import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import os

# File to store the start cycle time
START_CYCLE_FILE = 'start_cycle_time.txt'

def set_start_cycle():
    start_cycle_time = datetime.now()
    with open(START_CYCLE_FILE, 'w') as f:
        f.write(start_cycle_time.isoformat())
    start_time_label.config(text=f"Start Time: {start_cycle_time.strftime('%Y-%m-%d %H:%M:%S')}")
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
                current_temp = cycle[1] + (temp_per_minute * elapsed_time.total_seconds() / 60)
            elif cycle[3].lower() == 'soak':
                current_temp = cycle[1]
            current_cycle_label.config(text=f"Current Cycle Step: {cycle[0]}")
            break
        else:
            elapsed_time -= cycle_time

    if current_temp is None:
        raise ValueError("Elapsed time exceeds total cycle time")

    conn.close()
    return current_temp

def fetch_schedule(schedule='A2'):
    # Connect to the database
    conn = sqlite3.connect('SmartFurnace.db')
    cursor = conn.cursor()

    # Fetch the schedule from the database
    cursor.execute(f"SELECT Cycle, StartTemp, EndTemp, CycleType, CycleTime FROM {schedule}")
    cycles = cursor.fetchall()

    conn.close()
    return cycles

def update_temperature_label():
    try:
        current_temp = get_current_temperature()
        temperature_label.config(text=f"Current Temperature: {current_temp:.2f}°C")
    except ValueError as e:
        temperature_label.config(text=str(e))
    root.after(1000, update_temperature_label)

def animate(i):
    try:
        start_time = get_start_cycle_time()
        current_time = datetime.now()
        elapsed_time = (current_time - start_time).total_seconds() / 60  # in minutes

        cycles = fetch_schedule()
        times = []
        temps = []
        total_time = 0
        min_temp = float('inf')
        max_temp = float('-inf')

        for cycle in cycles:
            cycle_time_minutes = int(cycle[4].split()[0])
            print(f"Processing cycle: {cycle}")  # Debug print statement
            if cycle[3].lower() == 'ramp':
                times.extend([total_time, total_time + cycle_time_minutes])
                temps.extend([cycle[1], cycle[2]])
                min_temp = min(min_temp, cycle[1], cycle[2])
                max_temp = max(max_temp, cycle[1], cycle[2])
            elif cycle[3].lower() == 'soak':
                times.extend([total_time, total_time + cycle_time_minutes])
                temps.extend([cycle[1], cycle[1]])
                min_temp = min(min_temp, cycle[1])
                max_temp = max(max_temp, cycle[1])
            total_time += cycle_time_minutes

        print(f"Min Temp: {min_temp}, Max Temp: {max_temp}")  # Debug print statement

        ax.clear()
        ax.plot(times, temps, label='Temperature Schedule')
        ax.axvline(x=elapsed_time, color='r', linestyle='--', label='Current Time')
        ax.set_xlim(0, total_time)  # Set X-axis limits from start to end time
        ax.set_ylim(min_temp - 10, max_temp + 10)  # Set Y-axis limits based on min and max temperatures

        # Update X-axis with actual time
        actual_times = [start_time + timedelta(minutes=t) for t in times]
        actual_time_labels = [t.strftime('%I:%M %p') for t in actual_times]
        ax.set_xticks(times)
        ax.set_xticklabels(actual_time_labels, rotation=45, ha='right')

        ax.set_xlabel('Time')
        ax.set_ylabel('Temperature (°C)')
        ax.legend()

        # Adjust layout to prevent labels from being cut off
        fig.tight_layout()
    except ValueError:
        pass

# Create the main window
root = tk.Tk()
root.title("Smart Furnace Control")

# Create a frame for the controls
control_frame = ttk.Frame(root)
control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

# Create a button to set the start cycle time
start_cycle_button = ttk.Button(control_frame, text="Set Start Time", command=set_start_cycle)
start_cycle_button.pack(side=tk.LEFT, padx=5)

# Create a dropdown menu to select the schedule
schedule_label = ttk.Label(control_frame, text="Select Schedule:")
schedule_label.pack(side=tk.LEFT, padx=5)
schedule_var = tk.StringVar(value="A2")
schedule_menu = ttk.Combobox(control_frame, textvariable=schedule_var, values=["A2"])
schedule_menu.pack(side=tk.LEFT, padx=5)

# Create a label to display the start time
start_time_label = ttk.Label(root, text="Start Time: N/A")
start_time_label.pack(side=tk.TOP, pady=5)

# Create a label to display the current cycle step
current_cycle_label = ttk.Label(root, text="Current Cycle Step: N/A")
current_cycle_label.pack(side=tk.TOP, pady=5)

# Create a label to display the current temperature
temperature_label = ttk.Label(root, text="Current Temperature: N/A")
temperature_label.pack(side=tk.TOP, pady=10)

# Create a figure for the graph
fig = Figure(figsize=(10, 5), dpi=100)  # Increased figure size
ax = fig.add_subplot(111)

# Create a canvas to display the graph
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Set up the animation
ani = animation.FuncAnimation(fig, animate, interval=1000)

# Start the temperature update loop
update_temperature_label()

# Start the Tkinter main loop
root.mainloop()