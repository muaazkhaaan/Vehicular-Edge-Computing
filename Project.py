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
            else:  # VU direction is left
                distance_to_rsu_edge = VU['position'] - (rsu['position'] - rsu['coverage'])
                ''
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

    # Calculate uplink and downlink transmission latency in ms
    uplink_latency = (task_bits / Bandwidth_uplink_bps) * 1000  # Convert seconds to ms
    downlink_latency = (task_bits / (5 *Bandwidth_downlink_bps)) * 1000  # Convert seconds to ms
    
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
# Initialize RSU task counts
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
        else:  # Assuming direction is left
            # Update position, ensuring the VU doesn't move past the start of the road
            vu['position'] = max(vu['position'] - distance_moved, 0)

offloading_decisions = offload_tasks_sorted(VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue)

# Print offloading decisions for review
for decision in offloading_decisions:
    print(decision,'\n')


def offload_remaining_tasks(VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue):
    # Reset counters 
    rsu_task_counts = {rsu_id: 0 for rsu_id in RSUs}
    hap_task_count = 0
    # Temporary storage for offloading decisions
    new_offloading_decisions = []
    
    # Work on a copy of the queue to avoid modifying the queue during iteration
    tasks_to_revaluate = list(task_priority_queue)
    print("tasks to reeval", tasks_to_revaluate)
    
    # Check if there are no tasks to reevaluate
    if not tasks_to_revaluate:
        print("No tasks to reevaluate, exiting function.")
        return new_offloading_decisions, rsu_task_counts, hap_task_count
    
    # Clear the original priority queue and re-insert tasks if they still can't be offloaded
    task_priority_queue.clear()

    while tasks_to_revaluate:
        # Pop the task with the highest priority (smallest max_latency_ms)
        max_latency_ms, task_info = heapq.heappop(tasks_to_revaluate)
        vu_id = task_info['vu_id']
        task = task_info['task']
        VU = VUs[vu_id]

        # Calculate latencies for the current task
        latencies = calculate_latency(task, VU, RSUs, HAP)
        print("latency:", latencies)
        valid_rsus = find_valid_rsu(VU, RSUs)
        print("valid rsu:", valid_rsus)

        # Initially set to not having made a decision
        decision_made = False

        # Attempt RSU offloading again
        for rsu in valid_rsus:
            if latencies['RSU_latency'] <= task['max_latency_ms'] and rsu_task_counts[rsu['rsu_id']] < RSUs[rsu['rsu_id']]['max_tasks']:
                new_offloading_decisions.append({
                    'vu_id': vu_id, 'task_id': task['id'],
                    'offloading_type': 'RSU', 'estimated_latency_ms': latencies['RSU_latency'],
                    'rsu_id': rsu['rsu_id']
                })
                rsu_task_counts[rsu['rsu_id']] += 1
                decision_made = True
                break

        # Attempt HAP offloading again
        if not decision_made and hap_task_count < HAP['max_tasks'] and latencies['HAP_latency'] <= task['max_latency_ms']:
            new_offloading_decisions.append({
                'vu_id': vu_id, 'task_id': task['id'],
                'offloading_type': 'HAP', 'estimated_latency_ms': latencies['HAP_latency']
            })
            hap_task_count += 1
            decision_made = True

        # Attempt local VU processing again
        if not decision_made and latencies['VU_latency'] <= task['max_latency_ms']:
            new_offloading_decisions.append({
                'vu_id': vu_id, 'task_id': task['id'],
                'offloading_type': 'VU', 'estimated_latency_ms': latencies['VU_latency']
            })
            decision_made = True

        # If no offloading option is viable, push the task back into the priority queue
        if not decision_made:
            heapq.heappush(task_priority_queue, (task['max_latency_ms'], {'vu_id': vu_id, 'task': task}))

    # Return the new offloading decisions and updated task counts
    return new_offloading_decisions, rsu_task_counts, hap_task_count



import time

def simulate(VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue, total_simulation_time_ms):
    current_time_ms = 0
    timestep_ms = 54.5

    # Continue the simulation for the specified total simulation time
    while current_time_ms <= total_simulation_time_ms and task_priority_queue:
        print(current_time_ms)
        # Offload tasks that are currently in the priority queue
        offloading_decisions, rsu_task_counts, hap_task_count = offload_remaining_tasks(
            VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue
        )

        # Update the environment?? here or earlier??

        # Wait for the next time step
        time.sleep(timestep_ms / 1000.0)  # Convert milliseconds to seconds for sleep function
        current_time_ms += timestep_ms
        print(offloading_decisions)
        print("rsu", rsu_task_counts)
        print("hap", hap_task_count)
    
    return rsu_task_counts, hap_task_count, task_priority_queue


rsu_task_counts_final, hap_task_count_final, task_priority_queue_final = simulate(
    VUs, RSUs, HAP, rsu_task_counts, hap_task_count, task_priority_queue, total_simulation_time_ms=550
)

print("done")
print(task_priority_queue)



