import tkinter as tk
from tkinter import ttk
import core_functions as cf
import main as sim

# --- GUI Element Globals ---
root = None
log_text = None
start_button = None
stop_button = None
landing_trees = {}
takeoff_trees = {}
runway_labels = []
landing_label = None
takeoff_label = None
completed_label = None
diverted_label = None
emergency_label = None

def update_treeview(tree, queue_data):
    """Clears and repopulates a Treeview widget."""
    for item in tree.get_children(): tree.delete(item)

    # Data is pre-filtered in update_gui_elements to avoid duplicate iids
    # Items are inserted based on the sorted order from update_gui_elements

    for i, item in enumerate(queue_data):
        priority_str = f"{item['priority']:.1f}"
        fuel_str = f"{item['fuel']} min" if isinstance(item['fuel'], int) else "N/A"
        values = (priority_str, item['id'], item['type'], item['special'], fuel_str, item['status'])
        tree.insert('', tk.END, iid=item['id'], values=values, tags=item['tags'])

def get_priority_queue_data(heap):
    """Extracts and formats data from a heap clone for Treeview display."""
    heap_clone = heap[:]
    result = []
    temp_storage = []

    while not cf.maxheap.is_empty(heap_clone):
        try:
            priority, value = cf.maxheap.remove_max(heap_clone)
            temp_storage.append((priority, value))

            tags = []
            special = ""  # For the 'Special' column display

            # Determine primary background tag based on priority/status
            if value["is_emergency"]:
                tags.append("emergency")
                special = "EMERGENCY"
            elif value["is_medevac"]:
                tags.append("medevac")
                special = "MEDEVAC"
            elif value["is_vip"]:
                tags.append("vip")
                special = "VIP"
            elif value["status"] == "Holding":  # Check for holding status
                tags.append("holding")  # Apply yellow background tag

            # Add secondary tag for low fuel (text color)
            fuel = value.get("fuel_remaining", "N/A")
            if isinstance(fuel, int) and fuel <= cf.FUEL_EMERGENCY_THRESHOLD:
                tags.append("lowfuel")

            result.append({
                "priority": priority, "id": value["id"], "type": value["type"],
                "status": value["status"], "special": special, "fuel": fuel,
                "tags": tuple(tags)
            })
        except IndexError:
            cf.log_event("Error reading heap clone for display.")
            break
    return result

def update_info_labels():
    """Updates the text labels for runways and queue statistics."""
    for i, runway in enumerate(cf.runways):
        if i < len(runway_labels):
            if runway["is_occupied"]:
                plane = runway["current_plane"]
                time_left = max(0, (runway["time_available"] - cf.system_time).total_seconds())
                status = f"R{runway['id']} ({runway['length']}'): {plane['id']} ({plane['status']}) - {int(time_left // 60)}m {int(time_left % 60)}s"
            else:
                status = f"R{runway['id']} ({runway['length']}'): Available"
            runway_labels[i].config(text=status)

    landing_count = sum(cf.maxheap.__len__(q) for q in cf.landing_queues.values())
    takeoff_count = sum(cf.maxheap.__len__(q) for q in cf.takeoff_queues.values())
    landing_label.config(text=f"Land Q: {landing_count} (S:{cf.maxheap.__len__(cf.landing_queues['Small'])}/M:{cf.maxheap.__len__(cf.landing_queues['Medium'])}/L:{cf.maxheap.__len__(cf.landing_queues['Large'])})")
    takeoff_label.config(text=f"Takeoff Q: {takeoff_count} (S:{cf.maxheap.__len__(cf.takeoff_queues['Small'])}/M:{cf.maxheap.__len__(cf.takeoff_queues['Medium'])}/L:{cf.maxheap.__len__(cf.takeoff_queues['Large'])})")
    completed_label.config(text=f"Completed: {cf.completed_flights}")
    diverted_label.config(text=f"Diverted: {cf.diverted_flights}")
    emergency_label.config(text=f"Emergencies: {len(cf.emergency_flights)}")

def update_gui_elements():
    """Update all Treeviews and Labels."""
    
    # Update each landing queue treeview
    for size in ["Small", "Medium", "Large"]:
        # Process landing queues
        landing_queue_data_raw = get_priority_queue_data(cf.landing_queues[size])
        seen_landing_ids = set()
        filtered_landing_data = []
        landing_queue_data_raw.sort(key=lambda x: x["priority"], reverse=True)
        for item in landing_queue_data_raw:
            if item['id'] not in seen_landing_ids:
                filtered_landing_data.append(item)
                seen_landing_ids.add(item['id'])
        update_treeview(landing_trees[size], filtered_landing_data)
        
        # Process takeoff queues
        takeoff_queue_data_raw = get_priority_queue_data(cf.takeoff_queues[size])
        seen_takeoff_ids = set()
        filtered_takeoff_data = []
        takeoff_queue_data_raw.sort(key=lambda x: x["priority"], reverse=True)
        for item in takeoff_queue_data_raw:
            if item['id'] not in seen_takeoff_ids:
                filtered_takeoff_data.append(item)
                seen_takeoff_ids.add(item['id'])
        update_treeview(takeoff_trees[size], filtered_takeoff_data)
    
    update_info_labels()

def setup_gui():
    """Initializes the Tkinter GUI."""
    global root, log_text, start_button, stop_button
    global landing_trees, takeoff_trees
    global runway_labels, landing_label, takeoff_label, completed_label, diverted_label, emergency_label

    root = tk.Tk()
    root.title("Air Traffic Control Simulation")
    root.geometry("1500x950")

    style = ttk.Style()
    style.configure("Treeview", rowheight=25)
    style.map("Treeview", background=[('selected', '#cccccc')])

    # --- Frames ---
    control_frame = tk.Frame(root, padx=10, pady=5)
    control_frame.pack(fill=tk.X)
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    left_frame = tk.Frame(main_frame, width=800)
    left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
    left_frame.pack_propagate(False)
    right_frame = tk.Frame(main_frame, width=650)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    right_frame.pack_propagate(False)

    # --- Controls ---
    start_button = tk.Button(control_frame, text="Start", command=sim.start_simulation, width=10)
    start_button.pack(side=tk.LEFT, padx=5)
    stop_button = tk.Button(control_frame, text="Stop", command=sim.stop_simulation, state=tk.DISABLED, width=10)
    stop_button.pack(side=tk.LEFT, padx=5)
    emergency_button = tk.Button(control_frame, text="Create Emergency", command=sim.create_emergency, width=15)
    emergency_button.pack(side=tk.LEFT, padx=5)
    add_flight = tk.Button(control_frame, text="Add Flight", command=sim.create_flight, width=15)
    add_flight.pack(side=tk.LEFT, padx=5)

    # --- Info Area (Left Top) ---
    info_frame = tk.Frame(left_frame, padx=5, pady=5)
    info_frame.pack(fill=tk.X)
    runway_frame = tk.LabelFrame(info_frame, text="Runways", padx=10, pady=5)
    runway_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    queue_stats_frame = tk.LabelFrame(info_frame, text="Stats", padx=10, pady=5)
    queue_stats_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    # Runway Labels
    runway_labels = []
    for i in range(len(cf.runways)):
        label = tk.Label(runway_frame, text=f"R{i+1}: ...", anchor=tk.W, justify=tk.LEFT)
        label.pack(fill=tk.X, pady=1)
        runway_labels.append(label)

    # Stats Labels
    landing_label = tk.Label(queue_stats_frame, text="Land Q: 0", anchor=tk.W)
    landing_label.pack(fill=tk.X, pady=1)
    takeoff_label = tk.Label(queue_stats_frame, text="Takeoff Q: 0", anchor=tk.W)
    takeoff_label.pack(fill=tk.X, pady=1)
    completed_label = tk.Label(queue_stats_frame, text="Completed: 0", anchor=tk.W)
    completed_label.pack(fill=tk.X, pady=1)
    diverted_label = tk.Label(queue_stats_frame, text="Diverted: 0", anchor=tk.W)
    diverted_label.pack(fill=tk.X, pady=1)
    emergency_label = tk.Label(queue_stats_frame, text="Emergencies: 0", anchor=tk.W, fg='red', font=('Arial', 10, 'bold'))
    emergency_label.pack(fill=tk.X, pady=1)

    # --- Treeview Area (Left Bottom) ---
    queue_display_frame = tk.Frame(left_frame)
    queue_display_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
    
    # Add vertical scrollbar for entire queue display
    queue_canvas = tk.Canvas(queue_display_frame)
    queue_scrollbar_y = tk.Scrollbar(queue_display_frame, orient="vertical", command=queue_canvas.yview)
    queue_scrollbar_x = tk.Scrollbar(queue_display_frame, orient="horizontal", command=queue_canvas.xview)
    queue_scrollable_frame = tk.Frame(queue_canvas)

    
    
    queue_scrollable_frame.bind(
        "<Configure>",
        lambda e: queue_canvas.configure(scrollregion=queue_canvas.bbox("all"))
    )
    
    queue_canvas.create_window((0, 0), window=queue_scrollable_frame, anchor="nw")
    queue_canvas.configure(yscrollcommand=queue_scrollbar_y.set)
    queue_canvas.configure(xscrollcommand=queue_scrollbar_x.set)
    
    
    # Pack the canvas and scrollbar
    queue_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    queue_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    queue_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    
    # Move landing and takeoff sections into the scrollable frame
    landing_section = tk.LabelFrame(queue_scrollable_frame, text="Landing Priority Queues")
    landing_section.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
    
    # Initialize landing and takeoff trees dictionaries
    landing_trees = {}
    takeoff_trees = {}
    
    # Common column configurations
    
    cols = {"Priority": 65, "ID": 70, "Type": 60, "Sp": 80, "Fuel": 60, "Status": 140}
    headings = {"Priority": "Priority", "ID": "ID", "Type": "Type", "Sp": "Special", "Fuel": "Fuel", "Status": "Status"}
    
    # Create landing queue treeviews by size (side by side)
    
    for size in ["Large", "Medium", "Small"]:
        size_frame = tk.LabelFrame(landing_section, text=f"{size} Aircraft")
        size_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        lq_scroll_y = tk.Scrollbar(size_frame, orient=tk.VERTICAL)
        lq_scroll_x = tk.Scrollbar(size_frame, orient=tk.HORIZONTAL)
        landing_trees[size] = ttk.Treeview(size_frame, columns=tuple(cols.keys()), show="headings",
                                          yscrollcommand=lq_scroll_y.set, xscrollcommand=lq_scroll_x.set)
        lq_scroll_y.config(command=landing_trees[size].yview)
        lq_scroll_x.config(command=landing_trees[size].xview)
        lq_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        lq_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        landing_trees[size].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure columns
        for col, width in cols.items():
            landing_trees[size].column(col, width=width, stretch=tk.NO, anchor=tk.W)
        for col, heading in headings.items():
            landing_trees[size].heading(col, text=heading, anchor=tk.W)
    
    # Create takeoff queue section with main scrollbars
    takeoff_section = tk.LabelFrame(queue_scrollable_frame, text="Takeoff Priority Queues")
    takeoff_section.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
    
    # Create takeoff queue treeviews by size (side by side)
    for size in ["Large", "Medium", "Small"]:
        size_frame = tk.LabelFrame(takeoff_section, text=f"{size} Aircraft")
        size_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=2)
        tq_scroll_y = tk.Scrollbar(size_frame, orient=tk.VERTICAL)
        tq_scroll_x = tk.Scrollbar(size_frame, orient=tk.HORIZONTAL)
        takeoff_trees[size] = ttk.Treeview(size_frame, columns=tuple(cols.keys()), show="headings",
                                          yscrollcommand=tq_scroll_y.set, xscrollcommand=tq_scroll_x.set)
        tq_scroll_y.config(command=takeoff_trees[size].yview)
        tq_scroll_x.config(command=takeoff_trees[size].xview)
        tq_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tq_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        takeoff_trees[size].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure columns
        for col, width in cols.items():
            takeoff_trees[size].column(col, width=width, stretch=tk.NO, anchor=tk.W)
        for col, heading in headings.items():
            takeoff_trees[size].heading(col, text=heading, anchor=tk.W)

    # --- Event Log (Right Frame) ---
    log_frame = tk.LabelFrame(right_frame, text="Event Log", padx=5, pady=5)
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_scrollbar = tk.Scrollbar(log_frame)
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text = tk.Text(log_frame, height=40, width=80, font=("Courier New", 9), wrap=tk.WORD,
                      yscrollcommand=log_scrollbar.set, state=tk.DISABLED)
    log_text.pack(fill=tk.BOTH, expand=True)
    log_scrollbar.config(command=log_text.yview)

    # Configure tags for all treeviews
    common_tags = {
        'emergency': {'background': 'red'},
        'vip': {'background': 'light green'},
        'medevac': {'background': 'light blue'},
        'holding': {'background': 'yellow'},
        'lowfuel': {'foreground': 'dark orange', 'font':('TkDefaultFont', 9, 'bold')}
    }
    
    for size in ["Large", "Medium", "Small"]:
        for tag_name, config in common_tags.items():
            landing_trees[size].tag_configure(tag_name, **config)
            takeoff_trees[size].tag_configure(tag_name, **config)

    # --- Legend ---
    legend_frame = tk.LabelFrame(root, text="Legend (Queue Highlight)", padx=10, pady=3)
    legend_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
    legend_items = [
        ("Emergency", "red", "black"), ("VIP", "light green", "black"),
        ("Medevac", "light blue", "black"), ("Holding", "yellow", "black"),
        ("Low Fuel", "dark orange", "black"), ("Normal", "white", "black")
    ]
    for text, bgcolor, fgcolor in legend_items:
        frame = tk.Frame(legend_frame)
        frame.pack(side=tk.LEFT, padx=10)
        swatch = tk.Label(frame, text='  ', bg=bgcolor, relief=tk.RAISED, borderwidth=1)
        swatch.pack(side=tk.LEFT)
        label_fg = fgcolor if text != "Low Fuel" else bgcolor
        label = tk.Label(frame, text=text, fg=label_fg)
        label.pack(side=tk.LEFT, padx=5)
    
    # Connect log_event function to the GUI
    # Add a special method to handle GUI log updates
    def update_log_text(message):
        """Updates the GUI log text widget with a new message."""
        if log_text:
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, message + "\n")
            log_text.config(state=tk.DISABLED)
            log_text.yview(tk.END)
    
    # Monkey patch the core log_event function to update GUI
    original_log_event = cf.log_event
    def gui_log_event(message):
        full_message = original_log_event(message)
        if isinstance(full_message, str):  # If the original returns the formatted message
            update_log_text(full_message)
        else:  # If it doesn't return anything
            timestamp = cf.system_time.strftime("%H:%M:%S")
            update_log_text(f"[{timestamp}] {message}")
        return full_message
    
    # Only apply the monkey patch if the original doesn't already handle GUI updates
    if "log_text" not in cf.log_event.__code__.co_varnames:
        cf.log_event = gui_log_event
    
    update_info_labels()