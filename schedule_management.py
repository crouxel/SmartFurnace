import tkinter as tk
from tkinter import ttk, messagebox
from database import save_schedule, fetch_all_schedules, delete_schedule
from graph import regenerate_graph

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

def delete_selected_schedule(root, schedule_var):
    selected_schedule = schedule_var.get()
    if selected_schedule == "Add Schedule":
        messagebox.showerror("Error", "Cannot delete 'Add Schedule'")
        return

    if messagebox.askyesno("Delete Schedule", f"Are you sure you want to delete the schedule '{selected_schedule}'?"):
        delete_schedule(selected_schedule)
        schedule_menu['values'] = fetch_all_schedules() + ["Add Schedule"]
        schedule_var.set("A2")  # Reset the selection to a valid schedule
        regenerate_graph(fig, ax, "A2")  # Update the graph with the default schedule

def edit_selected_schedule(root, schedule_var):
    selected_schedule = schedule_var.get()
    if selected_schedule == "Add Schedule":
        messagebox.showerror("Error", "Cannot edit 'Add Schedule'")
        return

    # Implement the logic to edit the selected schedule
    # This can involve opening a new window with the schedule details pre-filled for editing
    pass