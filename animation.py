from matplotlib.animation import FuncAnimation
from database import get_start_cycle_time, fetch_schedule
from datetime import datetime, timedelta

def animate(i, fig, ax, schedule_var):
    try:
        start_time = get_start_cycle_time()
        current_time = datetime.now()
        elapsed_time = (current_time - start_time).total_seconds() / 60  # in minutes

        schedule = schedule_var.get()
        if schedule == "Add Schedule":
            return

        print(f"Animating schedule: {schedule}")
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

def setup_animation(fig, ax, schedule_var):
    ani = FuncAnimation(fig, animate, fargs=(fig, ax, schedule_var), interval=1000, cache_frame_data=False)
    return ani