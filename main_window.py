import tkinter as tk
from tkinter import ttk, messagebox
from schedule_management import add_schedule, delete_selected_schedule, edit_selected_schedule
from graph import regenerate_graph
from database import set_start_cycle, get_start_cycle_time, get_current_temperature, fetch_all_schedules
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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

    # Bind right-click event to show context menu
    schedule_menu.bind("<Button-3>", lambda event: show_context_menu(event, root))

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

    return fig, ax, schedule_var

def on_schedule_select(event, root):
    selected_schedule = schedule_var.get()
    if selected_schedule == "Add Schedule":
        add_schedule(root)
        schedule_var.set("A2")  # Reset the selection to a valid schedule
    else:
        regenerate_graph(fig, ax, selected_schedule)  # Regenerate the graph with the new schedule

def show_context_menu(event, root):
    context_menu = tk.Menu(root, tearoff=0)
    context_menu.add_command(label="Edit Schedule", command=lambda: edit_selected_schedule(root, schedule_var))
    context_menu.add_command(label="Delete Schedule", command=lambda: delete_selected_schedule(root, schedule_var))
    context_menu.post(event.x_root, event.y_root)

def update_temperature_label(root):
    try:
        current_temp = get_current_temperature()
        temperature_label.config(text=f"Current Temperature: {current_temp:.2f}°C")
    except ValueError as e:
        temperature_label.config(text=str(e))
    root.after(1000, update_temperature_label, root)

def on_closing(root):
    root.destroy()