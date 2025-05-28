import maxheap
import random
from datetime import datetime, timedelta

# --- Constants ---
FUEL_EMERGENCY_THRESHOLD = 15
HOLDING_PATTERN_FUEL_BURN = 1
MAX_HOLDING_TIME = 30
SIMULATION_SPEED = 1.0

# --- Global Variables ---
landing_queues = {
    "Small": maxheap.create_heap_priority_queue(),  # Small planes
    "Medium": maxheap.create_heap_priority_queue(), # Medium planes
    "Large": maxheap.create_heap_priority_queue()   # Large planes
}
takeoff_queues = {
    "Small": maxheap.create_heap_priority_queue(),
    "Medium": maxheap.create_heap_priority_queue(),
    "Large": maxheap.create_heap_priority_queue()
}

runways = []
active_flights = {}
diverted_flights = 0
completed_flights = 0
emergency_flights = []
system_time = datetime.now()

def init_runways():
    """Initialize the runway configuration."""
    global runways
    runways = [
        {"id": 1, "length": 6000, "is_occupied": False, "time_available": system_time, "current_plane": None},  
        {"id": 2, "length": 6500, "is_occupied": False, "time_available": system_time, "current_plane": None}, 
        {"id": 3, "length": 8000, "is_occupied": False, "time_available": system_time, "current_plane": None},  
        {"id": 4, "length": 9500, "is_occupied": False, "time_available": system_time, "current_plane": None},  
        {"id": 5, "length": 11000, "is_occupied": False, "time_available": system_time, "current_plane": None},
        {"id": 6, "length": 12000, "is_occupied": False, "time_available": system_time, "current_plane": None}, 
        {"id": 7, "length": 13500, "is_occupied": False, "time_available": system_time, "current_plane": None}
    ]

def generate_plane(is_arrival=True):
    """Generate a random plane with appropriate attributes."""
    plane_types = [
        {"type": "Small", "size": 1, "min_runway": 6000, "operation_time": 10},
        {"type": "Medium", "size": 2, "min_runway": 8000, "operation_time": 15},
        {"type": "Large", "size": 3, "min_runway": 10000, "operation_time": 20}
    ]
    plane_type = random.choice(plane_types)
    plane_id = f"{'A' if is_arrival else 'D'}{random.randint(100, 999)}"
    fuel = random.randint(30, 120) if is_arrival else 120
    plane = {
        "id": plane_id, "type": plane_type["type"], "size": plane_type["size"],
        "min_runway": plane_type["min_runway"], "operation_time": plane_type["operation_time"],
        "fuel_remaining": fuel, "scheduled_time": system_time + timedelta(minutes=random.randint(0, 5)),
        "is_vip": random.random() < 0.05, "is_medevac": random.random() < 0.03,
        "has_tight_connection": random.random() < 0.1, "is_emergency": random.random() < 0.03 if plane_id[0] == "D" else False,
        "in_holding": False, "holding_since": None, "status": "Scheduled"
    }
    return plane

def calculate_landing_priority(plane):
    """Calculate priority score for a landing aircraft."""
    if plane['status'] in ["Completed", "Diverted"]:
        return 0

    size_priority = plane["size"] * 10
    if plane["is_emergency"]:
        return 10000
    special_factor = 0
    if plane["is_medevac"]: special_factor += 50
    if plane["is_vip"]: special_factor += 30
    if plane["has_tight_connection"]: special_factor += 20
    fuel_factor = (FUEL_EMERGENCY_THRESHOLD / plane['fuel_remaining']) * 100 
    time_diff = abs((plane["scheduled_time"] - system_time).total_seconds() / 60)
    time_factor = max(0, 30 - time_diff)
    return size_priority + special_factor + fuel_factor + time_factor

def calculate_takeoff_priority(plane):
    """Calculate priority score for a takeoff aircraft."""
    size_priority = plane["size"] * 10
    special_factor = 0
    if plane["is_medevac"]: special_factor += 50
    if plane["is_vip"]: special_factor += 30
    time_diff = (system_time - plane["scheduled_time"]).total_seconds() / 60
    time_factor = max(0, time_diff) * 2
    return special_factor + size_priority + time_factor

def log_event(message):
    """Log an event with timestamp."""
    timestamp = system_time.strftime("%H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)  # Keep console output for debugging
    

def find_runway(plane):
    """Finds the shortest available runway that meets the plane's minimum length requirement."""
    available_runways = []
    for runway in runways:
        if not runway["is_occupied"] and runway["length"] >= plane["min_runway"]:
            available_runways.append((runway["length"], runway["id"]))

    if available_runways:
        available_runways.sort()
        runway_id_to_use = available_runways[0][1]
        for runway in runways:
            if runway["id"] == runway_id_to_use:
                return runway
    return None