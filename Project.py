import random
import heapq

# Define the number of Vehicle Units (VUs), Roadside Units (RSUs), and road length (l) in meters
VU_m = 10
RSU_n = 8
l = 1000

# Define the properties of VUs and RSUs
VU_speed = 6  # m/s for VUs
VU_GFLOPS = 8  # GFLOPS for VUs
RSU_GFLOPS = 80  # GFLOPS for RSUs
RSU_coverage = 20  # Coverage radius in meters for RSUs
HAP_GFLOPS = 150  # GFLOPS for HAP

# Maximum number of tasks a VU can have
max_tasks_per_VU = 5

# Initialize VUs with their properties, randomly place them on the road, assign a random direction, and generate their tasks
VUs = {}
for i in range(VU_m):
    vu_id = f'VU_{i+1}'
    num_tasks = random.randint(1, max_tasks_per_VU)  # Random number of tasks for each VU
    tasks = [{
        'id': f'Task {j+1}',
        'size_MB': random.randint(1, 5),  # Size in MB
        'max_latency_ms': random.randint(300, 10000)  # Max required latency in ms
    } for j in range(num_tasks)]
    VUs[vu_id] = {
        'speed': VU_speed,
        'GFLOPS': VU_GFLOPS,
        'position': random.uniform(0, l),
        'direction': random.choice(['left', 'right']),
        'tasks': tasks
    }

# Calculate the interval between RSUs
interval = l / (RSU_n + 1)

# Initialize RSUs with their properties and place them evenly along the road
RSUs = {
    f'RSU_{i+1}': {
        'GFLOPS': RSU_GFLOPS,
        'position': interval * (i + 1),  # Position each RSU at equal intervals
        'coverage': RSU_coverage,
        'max_tasks': 10
    } for i in range(RSU_n)
}

# Define the HAP with its properties
HAP = {
    'GFLOPS': HAP_GFLOPS,  # Computational capacity of the HAP
    'coverage': l,  # The HAP covers the entire road length
    'max_tasks': 5
}

def find_valid_rsu(VU, RSUs):
    results = []
    for rsu_id, rsu in RSUs.items():
        distance_to_rsu_center = abs(VU['position'] - rsu['position'])
        if distance_to_rsu_center <= rsu['coverage']:
            distance_to_rsu_edge = None
            if VU['direction'] == 'right':
                distance_to_rsu_edge = (rsu['position'] + rsu['coverage']) - VU['position']
            else:  # VU direction is 'left'
                distance_to_rsu_edge = VU['position'] - (rsu['position'] - rsu['coverage'])
                
            sojourn_time = (abs(distance_to_rsu_edge) / VU['speed']) * 1000 # sojourn time in ms
            
            results.append({
                'rsu_id': rsu_id,
                'rsu_details': rsu,
                'distance_to_leave_coverage': distance_to_rsu_edge,
                'sojourn_time': sojourn_time
            })

    return results

def calculate_latency(task, VU, RSUs, HAP, Bandwidth_uplink=10, Bandwidth_downlink=20):
    # Correctly convert bandwidth from Gbps to bps for calculation
    Bandwidth_uplink_bps = Bandwidth_uplink * 10**9
    Bandwidth_downlink_bps = Bandwidth_downlink * 10**9

    # Convert task_MB into bits for calculation
    task_bits = task['size_MB'] * 8 * 10**6

    # Calculate uplink and downlink transmission latency (in ms)
    uplink_latency = (task_bits / Bandwidth_uplink_bps) * 1000  # Convert seconds to milliseconds
    downlink_latency = (task_bits / (5 *Bandwidth_downlink_bps)) * 1000  # Convert seconds to milliseconds
    
    # VU Processing Latency (No transmission latency considered)
    vu_processing_latency = ((1000* task_bits) / (VU['GFLOPS'] * 10**9)) * 1000  
    
    # Assuming RSU is chosen based on coverage and load; similarly for HAP
    rsu_processing_latency = ((1000 * task_bits) / (RSU_GFLOPS * 10**9)) * 1000
    hap_processing_latency = ((1000 * task_bits) / (HAP_GFLOPS * 10**9)) * 1000
    
    # Total latency for offloading to RSU and HAP includes transmission and processing latencies
    rsu_total_latency = uplink_latency + rsu_processing_latency + downlink_latency
    hap_total_latency = uplink_latency + hap_processing_latency + downlink_latency
    
    return {
        'VU_latency': vu_processing_latency,
        'RSU_latency': rsu_total_latency,
        'HAP_latency': hap_total_latency
    }


for vu_id, VU in VUs.items():
    valid_rsu_results = find_valid_rsu(VU, RSUs)
    print(f"Results for {vu_id}:")
    for result in valid_rsu_results:
        print(f"  RSU {result['rsu_id']} is valid with sojourn time {result['sojourn_time']} ms and distance to leave coverage {result['distance_to_leave_coverage']} meters.")


# Initialize the priority queue
task_priority_queue = []
# Initialize RSU task counts. Assume RSUs is a dict of RSU details.
rsu_task_counts = {rsu_id: 0 for rsu_id in RSUs}

# Initialize HAP task count
hap_task_count = 0

def offload_tasks_sorted(VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue):
    # Gather all tasks with their VU and task details
    all_tasks = []
    for vu_id, VU in VUs.items():
        for task in VU['tasks']:
            all_tasks.append((task['max_latency_ms'], vu_id, task))
    
    # Sort tasks by their max latency in ascending order
    all_tasks.sort(key=lambda x: x[0])
    
    offloading_decisions = []
    # Iterate over sorted tasks to make offloading decisions
    for max_latency_ms, vu_id, task in all_tasks:
        VU = VUs[vu_id]  # Get the VU details

        # Calculate latencies for current task
        latencies = calculate_latency(task, VU, RSUs, HAP)
        valid_rsus = find_valid_rsu(VU, RSUs)

        # Initially set to not having made a decision
        decision_made = False
        
        # RSU offloading check first
        for rsu in valid_rsus:
            if latencies['RSU_latency'] <= task['max_latency_ms'] and rsu_task_counts[rsu['rsu_id']] < RSUs[rsu['rsu_id']]['max_tasks']:
                offloading_decisions.append({
                    'vu_id': vu_id, 'task_id': task['id'],
                    'offloading_type': 'RSU', 'estimated_latency_ms': latencies['RSU_latency'],
                    'rsu_id': rsu['rsu_id']  # Include RSU ID for clarity
                })
                rsu_task_counts[rsu['rsu_id']] += 1
                decision_made = True
                break  # Assign to the first suitable RSU
        
        # HAP offloading check
        if not decision_made and hap_task_count < HAP['max_tasks'] and latencies['HAP_latency'] <= task['max_latency_ms']:
            offloading_decisions.append({
                'vu_id': vu_id, 'task_id': task['id'],
                'offloading_type': 'HAP', 'estimated_latency_ms': latencies['HAP_latency']
            })
            hap_task_count += 1
            decision_made = True

        # VU processing as the last option
        if not decision_made:
            # Check if VU processing meets the latency requirement
            if latencies['VU_latency'] <= task['max_latency_ms']:
                offloading_decisions.append({
                    'vu_id': vu_id, 'task_id': task['id'],
                    'offloading_type': 'VU', 'estimated_latency_ms': latencies['VU_latency']
                })
                decision_made = True
            else:
                # Task goes into the priority queue if no offloading option is viable
                heapq.heappush(task_priority_queue, (task['max_latency_ms'], {'vu_id': vu_id, 'task': task}))

    # Return the decisions, updated task counts for RSUs and HAP, and the task priority queue
    return offloading_decisions, rsu_task_counts, hap_task_count, task_priority_queue

def update_vehicle_positions(VUs, elapsed_time_sec):
    for vu_id, vu in VUs.items():
        speed = vu['speed']  # Speed in meters per second
        direction = vu['direction']
        distance_moved = speed * elapsed_time_sec  # Distance moved in the elapsed time
        
        if direction == 'right':
            # Update position, ensuring the VU doesn't go beyond the road length l
            vu['position'] = min(vu['position'] + distance_moved, l)
        else:  # Assuming direction is 'left'
            # Update position, ensuring the VU doesn't move past the start of the road
            vu['position'] = max(vu['position'] - distance_moved, 0)


# def simulate(VUs, RSUs, HAP, task_priority_queue, total_simulation_duration_ms=10000, time_step_ms=510):
#     simulation_time_ms = 0
#     active_tasks = []  # List to track ongoing tasks with their completion times

#     while simulation_time_ms < total_simulation_duration_ms:
#         # Update vehicle positions
#         update_vehicle_positions(VUs, time_step_ms / 1000.0)
        
#         # Check and update RSU/HAP counters based on task completions
#         check_and_update_task_completions(active_tasks, simulation_time_ms, rsu_task_counts, hap_task_count)
        
#         # Process the priority queue and attempt to offload tasks
#         offloading_decisions, rsu_task_counts, hap_task_count, task_priority_queue, new_active_tasks = offload_tasks_sorted(
#             VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue, simulation_time_ms)
        
#         # Add new active tasks to the tracking list
#         active_tasks.extend(new_active_tasks)
        
#         simulation_time_ms += time_step_ms
    
#     return offloading_decisions, rsu_task_counts, hap_task_count, task_priority_queue



# # Print offloading decisions for review
# for decision in offloading_decisions:
#     print(decision)
# print(task_priority_queue)









# def update_vehicle_positions(VUs, time_step_seconds):
#     for vu_id, vu_details in VUs.items():
#         # Calculate the distance moved in this time step
#         distance_moved = vu_details['speed'] * time_step_seconds

#         if vu_details['direction'] == 'right':
#             # Move to the right, ensure not exceeding road length
#             vu_details['position'] += distance_moved
#             vu_details['position'] = min(vu_details['position'], l)
#         else:
#             # Move to the left, ensure not going below 0
#             vu_details['position'] -= distance_moved
#             vu_details['position'] = max(vu_details['position'], 0)


# def offload_tasks_until_queue_empty(VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue, time_step_ms):
#     current_time = 0
#     total_simulation_time = 510000  # Example: total time you want the simulation to run (in ms)

#     while current_time < total_simulation_time and task_priority_queue:
#         rsu_task_counts = 0 
#         hap_task_count = 0
        
#         # Update vehicle positions based on the elapsed time
#         update_vehicle_positions(VUs, time_step_ms / 1000.0)  # Convert ms to seconds

#         # Attempt to offload tasks at the current time step
#         offloading_decisions, rsu_task_counts, hap_task_count, task_priority_queue = offload_tasks_sorted(
#             VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue)

#         # Increment the simulation time
#         current_time += time_step_ms

#         # Optional: Here, you could also decrement task counters for RSUs and HAP based on task completions
#         # This would require keeping track of task durations and completion times.

#     return offloading_decisions, rsu_task_counts, hap_task_count, task_priority_queue, current_time

# offloading_decisions, rsu_task_counts, hap_task_count, task_priority_queue, current_time = offload_tasks_until_queue_empty(
#     VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue, time_step_ms=510)

# # After calling the function, print the results:
# print(f"Offloading Decisions (summary): {len(offloading_decisions)} decisions made.")
# print("Final RSU Task Counts:", rsu_task_counts)
# print("Final HAP Task Count:", hap_task_count)
# print(f"Tasks remaining in the priority queue: {len(task_priority_queue)}")
# print(f"Total simulation time: {current_time} ms")
