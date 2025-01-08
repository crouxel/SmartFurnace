import sqlite3
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import os
import re

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

        cycles = fetch_schedule(schedule_var.get())
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

def add_schedule():
    def save_schedule():
        schedule_name = schedule_name_entry.get()
        if not schedule_name:
            messagebox.showerror("Error", "Schedule name cannot be empty")
            return

        # Validate cycle time format
        time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}$')
        for i in range(len(cycle_entries)):
            cycle_time = cycle_entries[i][3].get()
            if not time_pattern.match(cycle_time):
                messagebox.showerror("Error", f"Invalid time format for cycle {i+1}. Please use HH:MM:SS format.")
                return

        # Connect to the database
        conn = sqlite3.connect('SmartFurnace.db')
        cursor = conn.cursor()

        # Create a new table for the schedule
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schedule_name} (
                Cycle INTEGER PRIMARY KEY,
                StartTemp REAL,
                EndTemp REAL,
                CycleType TEXT,
                CycleTime TEXT,
                Notes TEXT
            )
        """)

        # Insert the entered values into the new table
        for i in range(len(cycle_entries)):
            cycle = i + 1
            start_temp = cycle_entries[i][0].get()
            end_temp = cycle_entries[i][1].get()
            cycle_type = cycle_entries[i][2].get()
            cycle_time = cycle_entries[i][3].get()
            notes = cycle_entries[i][4].get()
            cursor.execute(f"""
                INSERT INTO {schedule_name} (Cycle, StartTemp, EndTemp, CycleType, CycleTime, Notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (cycle, start_temp, end_temp, cycle_type, cycle_time, notes))

        conn.commit()
        conn.close()

        # Update the dropdown menu
        schedule_menu['values'] = list(schedule_menu['values']) + [schedule_name]
        add_schedule_window.destroy()

    add_schedule_window = tk.Toplevel(root)
    add_schedule_window.title("Add Schedule")

    tk.Label(add_schedule_window, text="Schedule Name:").grid(row=0, column=0, padx=5, pady=5)
    schedule_name_entry = tk.Entry(add_schedule_window)
    schedule_name_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_schedule_window, text="Cycle").grid(row=1, column=0, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Start Temp [°C]").grid(row=1, column=1, padx=5, pady=5)
    tk.Label(add_schedule_window, text="End Temp [°C]").grid(row=1, column=2, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Cycle Type").grid(row=1, column=3, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Cycle Time (HH:MM:SS)").grid(row=1, column=4, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Notes").grid(row=1, column=5, padx=5, pady=5)

    cycle_entries = []
    for i in range(10):  # Assuming a maximum of 10 cycles for simplicity
        cycle_entries.append([
            tk.Entry(add_schedule_window),
            tk.Entry(add_schedule_window),
            ttk.Combobox(add_schedule_window, values=["Ramp", "Soak"]),
            tk.Entry(add_schedule_window),
            tk.Entry(add_schedule_window)
        ])
        cycle_entries[-1][0].grid(row=i+2, column=1, padx=5, pady=5)
        cycle_entries[-1][1].grid(row=i+2, column=2, padx=5, pady=5)
        cycle_entries[-1][2].grid(row=i+2, column=3, padx=5, pady=5)
        cycle_entries[-1][3].grid(row=i+2, column=4, padx=5, pady=5)
        cycle_entries[-1][4].grid(row=i+2, column=5, padx=5, pady=5)
        tk.Label(add_schedule_window, text=str(i+1)).grid(row=i+2, column=0, padx=5, pady=5)

    save_button = tk.Button(add_schedule_window, text="Save Schedule", command=save_schedule)
    save_button.grid(row=12, column=0, columnspan=6, pady=10)

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
schedule_menu = ttk.Combobox(control_frame, textvariable=schedule_var, values=["A2", "Add Schedule"])
schedule_menu.pack(side=tk.LEFT, padx=5)

# Bind the selection event to open the add schedule form
def on_schedule_select(event):
    if schedule_var.get() == "Add Schedule":
        add_schedule()
        schedule_var.set("A2")  # Reset the selection to a valid schedule

schedule_menu.bind("<<ComboboxSelected>>", on_schedule_select)

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

# Handle window close event to ensure database connection is closed
def on_closing():
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start the Tkinter main loop
root.mainloop()