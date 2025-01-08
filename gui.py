import tkinter as tk
from tkinter import ttk, messagebox
from database import set_start_cycle, fetch_schedule, save_schedule, get_current_temperature, get_start_cycle_time, fetch_all_schedules, delete_schedule, print_schedule
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re
from animation import animate

def create_main_window(root):
    global start_time_label, temperature_label, schedule_menu, schedule_var, fig, ax

    # Create a frame for the controls
    control_frame = ttk.Frame(root)
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

    # Create a button to set the start cycle time
    start_cycle_button = ttk.Button(control_frame, text="Set Start Time", command=lambda: set_start_cycle(start_time_label))
    start_cycle_button.pack(side=tk.LEFT, padx=5)

    # Create a dropdown menu to select the schedule
    schedule_label = ttk.Label(control_frame, text="Select Schedule:")
    schedule_label.pack(side=tk.LEFT, padx=5)
    schedule_var = tk.StringVar(value="A2")
    schedule_menu = ttk.Combobox(control_frame, textvariable=schedule_var, values=fetch_all_schedules() + ["Add Schedule"])
    schedule_menu.pack(side=tk.LEFT, padx=5)

    # Bind the selection event to open the add schedule form
    schedule_menu.bind("<<ComboboxSelected>>", lambda event: on_schedule_select(event, root))

    # Create a frame for the start time and temperature labels
    info_frame = ttk.Frame(root)
    info_frame.pack(side=tk.TOP, pady=5)

    # Create a label to display the start time
    start_time_label = ttk.Label(info_frame, text="Start Time: N/A")
    start_time_label.pack(side=tk.LEFT, padx=5)

    # Create a label to display the current temperature
    temperature_label = ttk.Label(info_frame, text="Current Temperature: N/A")
    temperature_label.pack(side=tk.LEFT, padx=5)

    # Try to read the start time from the file and update the label
    try:
        start_cycle_time = get_start_cycle_time()
        start_time_label.config(text=f"Start Time: {start_cycle_time.strftime('%I:%M:%S %p')}")
    except ValueError:
        pass

    # Create a figure for the graph
    fig = Figure(figsize=(10, 5), dpi=100)  # Increased figure size
    ax = fig.add_subplot(111)

    # Create a canvas to display the graph
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Add right-click context menu for editing and deleting schedules
    schedule_menu.bind("<Button-3>", lambda event: show_context_menu(event, root))

    return fig, ax, schedule_var

def on_schedule_select(event, root):
    selected_schedule = schedule_var.get()
    if selected_schedule == "Add Schedule":
        add_schedule(root)
        schedule_var.set("A2")  # Reset the selection to a valid schedule
    else:
        print_schedule(selected_schedule)  # Print the selected schedule
        regenerate_graph(fig, ax, selected_schedule)  # Regenerate the graph with the new schedule

def regenerate_graph(fig, ax, schedule):
    cycles = fetch_schedule(schedule)
    times = []
    temps = []
    total_time = 0
    min_temp = float('inf')
    max_temp = float('-inf')

    for cycle in cycles:
        cycle_time_parts = cycle[4].split(':')
        cycle_time_minutes = int(cycle_time_parts[0]) * 60 + int(cycle_time_parts[1])
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

    ax.clear()
    ax.plot(times, temps, label='Temperature Schedule')
    
    # Add current time vertical line
    start_time = get_start_cycle_time()
    current_time = datetime.now()
    elapsed_time = (current_time - start_time).total_seconds() / 60  # in minutes
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

def add_schedule(root):
    def save_new_schedule():
        schedule_name = schedule_name_entry.get()
        if not schedule_name:
            messagebox.showerror("Error", "Schedule name cannot be empty")
            return

        # Validate cycle time format
        time_pattern = re.compile(r'^\d{2}:\d{2}$')
        valid_entries = []
        for i in range(len(cycle_entries)):
            cycle_type = cycle_entries[i][0].get()
            start_temp = cycle_entries[i][1].get()
            end_temp = cycle_entries[i][2].get()
            cycle_time = cycle_entries[i][3].get()
            notes = cycle_entries[i][4].get()

            # Skip empty rows
            if not cycle_type and not start_temp and not end_temp and not cycle_time and not notes:
                continue

            if not time_pattern.match(cycle_time) or cycle_time == "00:00":
                messagebox.showerror("Error", f"Invalid time format for cycle {i+1}. Please use HH:MM format and ensure time is not 00:00.")
                return

            valid_entries.append([cycle_type, start_temp, end_temp, cycle_time, notes])

        # Save the schedule to the database
        save_schedule(schedule_name, valid_entries)

        # Update the dropdown menu
        schedule_menu['values'] = fetch_all_schedules() + ["Add Schedule"]
        add_schedule_window.destroy()

    def on_cycle_type_change(event, start_temp_entry, end_temp_entry, cycle_time_entry, row):
        cycle_type = event.widget.get()
        if row > 0:
            prev_end_temp = cycle_entries[row - 1][2].get()
            start_temp_entry.delete(0, tk.END)
            start_temp_entry.insert(0, prev_end_temp)
        if cycle_type == "Soak":
            end_temp_entry.config(state=tk.NORMAL)
            end_temp_entry.delete(0, tk.END)
            end_temp_entry.insert(0, start_temp_entry.get())
            end_temp_entry.config(state=tk.DISABLED)
        else:
            end_temp_entry.config(state=tk.NORMAL)
        cycle_time_entry.delete(0, tk.END)
        cycle_time_entry.insert(0, "00:00")

        # Add a new row if this is the last row
        if row == len(cycle_entries) - 1:
            add_cycle_row()

    def add_cycle_row():
        row = len(cycle_entries)
        cycle_number_label = tk.Label(add_schedule_window, text=str(row + 1))
        cycle_type_combobox = ttk.Combobox(add_schedule_window, values=["Ramp", "Soak"])
        start_temp_entry = tk.Entry(add_schedule_window)
        end_temp_entry = tk.Entry(add_schedule_window)
        cycle_time_entry = tk.Entry(add_schedule_window)
        notes_entry = tk.Entry(add_schedule_window)

        cycle_number_label.grid(row=row+2, column=0, padx=5, pady=5)
        cycle_type_combobox.grid(row=row+2, column=1, padx=5, pady=5)
        start_temp_entry.grid(row=row+2, column=2, padx=5, pady=5)
        end_temp_entry.grid(row=row+2, column=3, padx=5, pady=5)
        cycle_time_entry.grid(row=row+2, column=4, padx=5, pady=5)
        notes_entry.grid(row=row+2, column=5, padx=5, pady=5)

        cycle_type_combobox.bind("<<ComboboxSelected>>", lambda event, start_temp_entry=start_temp_entry, end_temp_entry=end_temp_entry, cycle_time_entry=cycle_time_entry, row=row: on_cycle_type_change(event, start_temp_entry, end_temp_entry, cycle_time_entry, row))

        cycle_entries.append([cycle_type_combobox, start_temp_entry, end_temp_entry, cycle_time_entry, notes_entry])

        # Set the first start temp to 25°C
        if row == 0:
            start_temp_entry.insert(0, "25")

    add_schedule_window = tk.Toplevel(root)
    add_schedule_window.title("Add Schedule")

    tk.Label(add_schedule_window, text="Schedule Name:").grid(row=0, column=0, padx=5, pady=5)
    schedule_name_entry = tk.Entry(add_schedule_window)
    schedule_name_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(add_schedule_window, text="#").grid(row=1, column=0, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Cycle Type").grid(row=1, column=1, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Start Temp [°C]").grid(row=1, column=2, padx=5, pady=5)
    tk.Label(add_schedule_window, text="End Temp [°C]").grid(row=1, column=3, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Cycle Time (HH:MM)").grid(row=1, column=4, padx=5, pady=5)
    tk.Label(add_schedule_window, text="Notes").grid(row=1, column=5, padx=5, pady=5)

    cycle_entries = []
    add_cycle_row()  # Add the first row

    save_button = tk.Button(add_schedule_window, text="Save Schedule", command=save_new_schedule)
    save_button.grid(row=12, column=0, columnspan=6, pady=10)

def show_context_menu(event, root):
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Edit Schedule", command=lambda: edit_selected_schedule(root))
    context_menu.add_command(label="Delete Schedule", command=lambda: delete_selected_schedule(root))
    context_menu.post(event.x_root, event.y_root)

def edit_selected_schedule(root):
    selected_schedule = schedule_var.get()
    if selected_schedule == "Add Schedule":
        messagebox.showerror("Error", "Cannot edit 'Add Schedule'")
        return

    # Fetch the schedule data
    schedule_data = fetch_schedule(selected_schedule)

    # Create a new window to edit the schedule
    edit_schedule_window = tk.Toplevel(root)
    edit_schedule_window.title(f"Edit Schedule: {selected_schedule}")

    tk.Label(edit_schedule_window, text="Schedule Name:").grid(row=0, column=0, padx=5, pady=5)
    schedule_name_entry = tk.Entry(edit_schedule_window)
    schedule_name_entry.insert(0, selected_schedule)
    schedule_name_entry.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(edit_schedule_window, text="#").grid(row=1, column=0, padx=5, pady=5)
    tk.Label(edit_schedule_window, text="Cycle Type").grid(row=1, column=1, padx=5, pady=5)
    tk.Label(edit_schedule_window, text="Start Temp [°C]").grid(row=1, column=2, padx=5, pady=5)
    tk.Label(edit_schedule_window, text="End Temp [°C]").grid(row=1, column=3, padx=5, pady=5)
    tk.Label(edit_schedule_window, text="Cycle Time (HH:MM)").grid(row=1, column=4, padx=5, pady=5)
    tk.Label(edit_schedule_window, text="Notes").grid(row=1, column=5, padx=5, pady=5)

    cycle_entries = []

    def save_edited_schedule():
        new_schedule_name = schedule_name_entry.get()
        if not new_schedule_name:
            messagebox.showerror("Error", "Schedule name cannot be empty")
            return

        # Validate cycle time format
        time_pattern = re.compile(r'^\d{2}:\d{2}$')
        valid_entries = []
        for i in range(len(cycle_entries)):
            cycle_type = cycle_entries[i][0].get()
            start_temp = cycle_entries[i][1].get()
            end_temp = cycle_entries[i][2].get()
            cycle_time = cycle_entries[i][3].get()
            notes = cycle_entries[i][4].get()

            # Skip empty rows
            if not cycle_type and not start_temp and not end_temp and not cycle_time and not notes:
                continue

            if not time_pattern.match(cycle_time) or cycle_time == "00:00":
                messagebox.showerror("Error", f"Invalid time format for cycle {i+1}. Please use HH:MM format and ensure time is not 00:00.")
                return

            valid_entries.append([cycle_type, start_temp, end_temp, cycle_time, notes])

        # Delete the old schedule and save the new one
        delete_schedule(selected_schedule)
        save_schedule(new_schedule_name, valid_entries)

        # Update the dropdown menu
        schedule_menu['values'] = fetch_all_schedules() + ["Add Schedule"]
        edit_schedule_window.destroy()

    def on_cycle_type_change(event, start_temp_entry, end_temp_entry, cycle_time_entry, row):
        cycle_type = event.widget.get()
        if row > 0:
            prev_end_temp = cycle_entries[row - 1][2].get()
            start_temp_entry.delete(0, tk.END)
            start_temp_entry.insert(0, prev_end_temp)
        if cycle_type == "Soak":
            end_temp_entry.config(state=tk.NORMAL)
            end_temp_entry.delete(0, tk.END)
            end_temp_entry.insert(0, start_temp_entry.get())
            end_temp_entry.config(state=tk.DISABLED)
        else:
            end_temp_entry.config(state=tk.NORMAL)
        cycle_time_entry.delete(0, tk.END)
        cycle_time_entry.insert(0, "00:00")

        # Add a new row if this is the last row
        if row == len(cycle_entries) - 1:
            add_cycle_row()

    def add_cycle_row():
        row = len(cycle_entries)
        cycle_number_label = tk.Label(edit_schedule_window, text=str(row + 1))
        cycle_type_combobox = ttk.Combobox(edit_schedule_window, values=["Ramp", "Soak"])
        start_temp_entry = tk.Entry(edit_schedule_window)
        end_temp_entry = tk.Entry(edit_schedule_window)
        cycle_time_entry = tk.Entry(edit_schedule_window)
        notes_entry = tk.Entry(edit_schedule_window)

        cycle_number_label.grid(row=row+2, column=0, padx=5, pady=5)
        cycle_type_combobox.grid(row=row+2, column=1, padx=5, pady=5)
        start_temp_entry.grid(row=row+2, column=2, padx=5, pady=5)
        end_temp_entry.grid(row=row+2, column=3, padx=5, pady=5)
        cycle_time_entry.grid(row=row+2, column=4, padx=5, pady=5)
        notes_entry.grid(row=row+2, column=5, padx=5, pady=5)

        cycle_type_combobox.bind("<<ComboboxSelected>>", lambda event, start_temp_entry=start_temp_entry, end_temp_entry=end_temp_entry, cycle_time_entry=cycle_time_entry, row=row: on_cycle_type_change(event, start_temp_entry, end_temp_entry, cycle_time_entry, row))

        cycle_entries.append([cycle_type_combobox, start_temp_entry, end_temp_entry, cycle_time_entry, notes_entry])

        # Set the first start temp to 25°C
        if row == 0:
            start_temp_entry.insert(0, "25")

    # Populate the edit window with the existing schedule data
    for cycle in schedule_data:
        add_cycle_row()
        cycle_entries[-1][0].set(cycle[3])  # Cycle Type
        cycle_entries[-1][1].insert(0, cycle[1])  # Start Temp
        cycle_entries[-1][2].insert(0, cycle[2])  # End Temp
        cycle_entries[-1][3].insert(0, cycle[4])  # Cycle Time
        cycle_entries[-1][4].insert(0, cycle[5])  # Notes

    save_button = tk.Button(edit_schedule_window, text="Save Schedule", command=save_edited_schedule)
    save_button.grid(row=12, column=0, columnspan=6, pady=10)

def delete_selected_schedule(root):
    selected_schedule = schedule_var.get()
    if selected_schedule == "Add Schedule":
        messagebox.showerror("Error", "Cannot delete 'Add Schedule'")
        return

    if messagebox.askyesno("Delete Schedule", f"Are you sure you want to delete the schedule '{selected_schedule}'?"):
        delete_schedule(selected_schedule)
        schedule_menu['values'] = fetch_all_schedules() + ["Add Schedule"]
        schedule_var.set("A2")  # Reset the selection to a valid schedule
        regenerate_graph(fig, ax, "A2")  # Update the graph with the default schedule

def update_temperature_label(root):
    try:
        current_temp = get_current_temperature()
        temperature_label.config(text=f"Current Temperature: {current_temp:.2f}°C")
    except ValueError as e:
        temperature_label.config(text=str(e))
    root.after(1000, update_temperature_label, root)

def on_closing(root):
    root.destroy()