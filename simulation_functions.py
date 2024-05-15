from model import *

def store_initial_vu_states(VUs):
    initial_states = {}
    for vu_id, vu in VUs.items():
        initial_states[vu_id] = vu.copy()  
    return initial_states

def reset_vus_to_initial_state(VUs, initial_states):
    for vu_id, vu in VUs.items():
        vu.update(initial_states[vu_id]) # Reset each VU to its initial state

def update_vehicle_positions(VUs, elapsed_time_sec):
    for vu_id, vu in VUs.items():
        speed = vu['speed']
        direction = vu['direction']
        distance_moved = speed * elapsed_time_sec
        if direction == 'right':
            vu['position'] = min(vu['position'] + distance_moved, l)
        else:
            vu['position'] = max(vu['position'] - distance_moved, 0)
    return VUs