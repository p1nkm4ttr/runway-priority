import random
import time
from datetime import datetime, timedelta
import core_functions as cf
import gui_functions as gui

simulation_running = False

def add_landing(plane):
    """
    Add an arrival plane to its appropriate landing queue based on size.
    
    Args:
        plane: Dictionary containing plane details
    """
    priority = cf.calculate_landing_priority(plane)
    size = plane["type"]
    cf.maxheap.add(cf.landing_queues[size], priority, plane)
    cf.active_flights[plane["id"]] = plane
    cf.log_event(f"Flight {plane['id']} ({size}) added to landing queue (Priority: {priority:.1f}) Scheduled at {plane['scheduled_time']} ")

def add_takeoff(plane):
    """
    Add a departure plane to its appropriate takeoff queue based on size.
    
    Args:
        plane: Dictionary containing plane details
    """
    priority = cf.calculate_takeoff_priority(plane)
    size = plane["type"]
    cf.maxheap.add(cf.takeoff_queues[size], priority, plane)
    cf.active_flights[plane["id"]] = plane
    plane["status"] = "In Takeoff Queue"
    cf.log_event(f"Flight {plane['id']} ({size}) added to takeoff queue (Priority: {priority:.1f})")

def update_runways():
    """
    Check all runways and free them if their current operation is complete.
    """
    for runway in cf.runways:
        if runway["is_occupied"] and cf.system_time >= runway["time_available"]:
            plane = runway["current_plane"]
            cf.log_event(f"Runway {runway['id']} available ({plane['id']} {plane['status']} complete)")
            runway["is_occupied"] = False
            plane["status"] = "Completed"
            cf.completed_flights += 1
            if plane["id"] in cf.active_flights:
                 del cf.active_flights[plane["id"]]
            runway["current_plane"] = None

def update_plane_state():
    """
    Update status of all active flights, handling fuel consumption, emergencies, and diversions.
    """
    planes_to_remove = []

    for plane_id, plane in list(cf.active_flights.items()):

        if plane['status'] == 'Landing':
            continue

        if plane["status"] == "Holding":
            plane["fuel_remaining"] -= cf.HOLDING_PATTERN_FUEL_BURN

            # Detect low fuel emergency condition
            if plane["fuel_remaining"] <= cf.FUEL_EMERGENCY_THRESHOLD and not plane["is_emergency"]:
                plane["is_emergency"] = True
                plane["status"] = "Emergency (Low Fuel)"
                if plane not in cf.emergency_flights:
                    cf.emergency_flights.append(plane)
                cf.log_event(f"EMERGENCY (Low Fuel): Flight {plane['id']} fuel {plane['fuel_remaining']} min while holding. Priority set to 10000.")
    
            # Handle diversion for planes in holding pattern too long
            if plane["in_holding"]:
                 holding_time = (cf.system_time - plane["holding_since"]).total_seconds() / 60
                 if holding_time > cf.MAX_HOLDING_TIME or plane["fuel_remaining"] < 5:
                     plane["status"] = "Diverted"
                     reason = "Max holding time" if holding_time > cf.MAX_HOLDING_TIME else "Critical fuel"
                     cf.log_event(f"Flight {plane['id']} DIVERTED ({reason}). Fuel: {plane['fuel_remaining']}, Held: {int(holding_time)}m")
                     cf.diverted_flights += 1
                     planes_to_remove.append(plane_id)
                     if plane in cf.emergency_flights:
                         cf.emergency_flights.remove(plane)

        # Place arriving planes in holding pattern if all suitable runways are occupied
        elif (plane["id"][0] == "A" and plane["scheduled_time"] < cf.system_time and (all(x["is_occupied"] == True for x in cf.runways if
          (plane["type"] == "Small" and x["length"] >= 6000) or
          (plane["type"] == "Medium" and x["length"] >= 8000) or
          (plane["type"] == "Large" and x["length"] >= 10000)))):
            plane['status'] = 'Holding'
            plane["in_holding"] = True
            plane["holding_since"] = cf.system_time
            cf.log_event(f"Flight {plane['id']} ({plane['type']}) entering holding. Fuel: {plane['fuel_remaining']}")

        # Update priority for emergency flights
        if plane["is_emergency"]:
            if plane_id[0] == "A":
                cf.maxheap.update_priority(cf.landing_queues[plane['type']], plane, 10000)
            elif plane_id[0] == "D":
                cf.maxheap.update_priority(cf.takeoff_queues[plane['type']], plane, 10000)

    # Remove diverted planes from active flights
    for plane_id in planes_to_remove:
        if plane_id in cf.active_flights:
            size = cf.active_flights[plane_id]["type"]
            if plane_id[0] == "A":
                cf.maxheap.remove(cf.landing_queues[size], cf.active_flights[plane_id])
            del cf.active_flights[plane_id]

def process_landing():
    """
    Process the highest priority landing request, prioritizing emergencies and larger aircraft.
    
    Returns:
        bool: True if a landing was processed, False otherwise
    """
    # First handle emergency landings regardless of aircraft size
    for size in ["Large", "Medium", "Small"]:
        if not cf.maxheap.is_empty(cf.landing_queues[size]):
            key, plane = cf.maxheap.peek_max(cf.landing_queues[size])
            if plane["is_emergency"]:
                if process_landing_helper(plane, size):
                    return True
    
    # Then process by size (largest to smallest)
    for size in ["Large", "Medium", "Small"]:
        if not cf.maxheap.is_empty(cf.landing_queues[size]):
            key, plane = cf.maxheap.peek_max(cf.landing_queues[size])
            if process_landing_helper(plane,size):
                return True
    
    return False

def process_landing_helper(plane, size):
    """
    Helper function to process a specific landing plane.
    
    Args:
        plane: The plane to process
        size: Size category of the plane
        
    Returns:
        bool: True if landing was processed, False otherwise
    """
    if plane["id"] not in cf.active_flights:
        return False  # Skip if already processed
    
    if plane["scheduled_time"] <= cf.system_time:
        runway = cf.find_runway(plane)
        if runway:
            key, plane = cf.maxheap.remove_max(cf.landing_queues[size])
            runway["is_occupied"] = True
            runway["current_plane"] = plane
            runway["time_available"] = cf.system_time + timedelta(minutes=plane["operation_time"])
            plane["status"] = "Emergency Landing" if plane["is_emergency"] else "Landing"
            cf.log_event(f"{plane['status'].upper()}: {plane['id']} ({plane['type']}) on Runway {runway['id']}")
            plane["in_holding"] = False
            plane["holding_since"] = None
            return True
    else:
        return False
   
def process_takeoff():
    """
    Process the highest priority takeoff request.
    
    Returns:
        bool: True if a takeoff was processed, False otherwise
    """
    # Process by size (largest to smallest)
    for size in ["Large", "Medium", "Small"]:
        if not cf.maxheap.is_empty(cf.takeoff_queues[size]):
            key, plane = cf.maxheap.peek_max(cf.takeoff_queues[size])
            if process_takeoff_helper(plane, size):
                return True
    
    return False

def process_takeoff_helper(plane, size):
    """
    Helper function to process a specific takeoff plane.
    
    Args:
        plane: The plane to process
        size: Size category of the plane
        
    Returns:
        bool: True if takeoff was processed, False otherwise
    """
    if plane["id"] not in cf.active_flights:
        return False
    
    runway = cf.find_runway(plane)
    if plane["scheduled_time"] <= cf.system_time:
        if runway:
            key, plane = cf.maxheap.remove_max(cf.takeoff_queues[size])
            runway["is_occupied"] = True
            runway["current_plane"] = plane
            runway["time_available"] = cf.system_time + timedelta(minutes=plane["operation_time"])
            plane["status"] = "Taking Off"
            cf.log_event(f"TAKEOFF: {plane['id']} ({plane['type']}) from Runway {runway['id']}")
            return True
        else:
            plane["status"] = "In Takeoff Queue"
            return False
    else:
        return False

def generate_traffic():
    """
    Randomly generate new arrival and departure planes based on probability.
    """
    if random.random() < 0.3:
        add_landing(cf.generate_plane(is_arrival=True))
    if random.random() < 0.07:
        add_takeoff(cf.generate_plane(is_arrival=False))

def simulation_step():
    """
    Execute one minute of simulation time, updating all system components.
    """
    cf.system_time += timedelta(minutes=1 * cf.SIMULATION_SPEED)
    cf.log_event(f"--- Simulation Time: {cf.system_time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    update_runways()
    update_plane_state()
    generate_traffic()

    # Update priorities for emergency planes
    for plane in cf.emergency_flights[:]:
        if plane["id"] in cf.active_flights:
            size = plane["type"]
            if plane["id"][0] == 'A':  # Only for arrivals
                cf.maxheap.update_priority(cf.landing_queues[size], plane, 10000)
                plane["status"] = "Emergency (Priority Landing)"
        else:
            if plane in cf.emergency_flights:
                cf.emergency_flights.remove(plane)

    # Determine which operation has higher priority
    highest_landing_priority = -1
    highest_landing_size = None
    highest_takeoff_priority = -1
    highest_takeoff_size = None
    
    # Find highest priority landing plane
    for size in ["Large", "Medium", "Small"]:
        if not cf.maxheap.is_empty(cf.landing_queues[size]):
            priority, _ = cf.maxheap.peek_max(cf.landing_queues[size])
            if priority > highest_landing_priority:
                highest_landing_priority = priority
                highest_landing_size = size
    
    # Find highest priority takeoff plane
    for size in ["Large", "Medium", "Small"]:
        if not cf.maxheap.is_empty(cf.takeoff_queues[size]):
            priority, _ = cf.maxheap.peek_max(cf.takeoff_queues[size])
            if priority > highest_takeoff_priority:
                highest_takeoff_priority = priority
                highest_takeoff_size = size
    
    # Execute higher priority operation first, then try the other if runways available
    if highest_landing_priority >= highest_takeoff_priority and highest_landing_size is not None:
        process_landing()
        process_takeoff()
    elif highest_takeoff_size is not None:
        process_takeoff()
        process_landing()

def run_simulation():
    """
    Main simulation loop that triggers periodic simulation steps.
    """
    if simulation_running:
        simulation_step()
        gui.update_gui_elements()
        gui.root.after(int(1000 / cf.SIMULATION_SPEED), run_simulation)

def start_simulation():
    """
    Start the simulation loop and update UI controls.
    """
    global simulation_running
    if not simulation_running:
        simulation_running = True
        gui.start_button.config(state=gui.tk.DISABLED)
        gui.stop_button.config(state=gui.tk.NORMAL)
        cf.log_event("Simulation Started")
        run_simulation()

def stop_simulation():
    """
    Stop the simulation loop and update UI controls.
    """
    global simulation_running
    if simulation_running:
        simulation_running = False
        gui.start_button.config(state=gui.tk.NORMAL)
        gui.stop_button.config(state=gui.tk.DISABLED)
        cf.log_event("Simulation Stopped")

def create_emergency():
    """
    Flag a random active flight as an emergency situation.
    """
    if cf.active_flights:
        candidates = [p for p, f in cf.active_flights.items() if f["status"] in ["In Landing Queue", "Holding", "In Takeoff Queue"] and not f["is_emergency"]]

        if candidates:
            plane_id = random.choice(candidates)
            plane = cf.active_flights[plane_id]
            plane["is_emergency"] = True
            plane["status"] = "Emergency Declared"
            if plane not in cf.emergency_flights: cf.emergency_flights.append(plane)
            cf.log_event(f"MANUAL EMERGENCY: Flight {plane['id']}")
            size = plane["type"]
            cf.maxheap.update_priority(cf.landing_queues[size], plane, 10000)
            cf.log_event(f"Priority for emergency flight {plane['id']} set to 10000")
        else: cf.log_event("No non-emergency flights available.")
    else: cf.log_event("No active flights.")

def create_flight():
    """
    Create a new random flight (either arrival or departure).
    """

    is_arrival = random.random() < 0.5
    plane = cf.generate_plane(is_arrival)
    if is_arrival:
        add_landing(plane)
    else:
        add_takeoff(plane)
    cf.log_event(f"Flight {plane['id']} added")

def main():

    cf.init_runways()
    gui.setup_gui()
    gui.update_gui_elements()
    cf.log_event("System Initialized. Ready to start simulation.")
    gui.root.mainloop()

if __name__ == "__main__":
    main()