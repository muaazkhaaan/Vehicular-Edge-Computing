import random

# Define the number of Vehicle Units (VUs), Roadside Units (RSUs), and road length (l) in meters
VU_m = 10
RSU_n = 8
l = 1000

# Define the properties of VUs and RSUs
VU_speed = 6  # m/s for VUs
VU_GFLOPS = 8  # GFLOPS for VUs
RSU_GFLOPS = 80  # GFLOPS for RSUs
RSU_coverage = 20  # Coverage radius in meters for RSUs
HAP_GFLOPS = 50  # GFLOPS for HAP

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
        'max_latency_ms': random.randint(100, 10000)  # Max required latency in ms
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
    downlink_latency = (task_bits / Bandwidth_downlink_bps) * 1000  # Convert seconds to milliseconds
    
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
    
def offload_tasks(VUs, RSUs, HAP):
    offloading_decisions = []

    for vu_id, VU in VUs.items():
        for task in VU['tasks']:
            latencies = calculate_latency(task, VU, RSUs, HAP)
            valid_rsus = find_valid_rsu(VU, RSUs)

            # Initially set decision to VU offloading with its latency
            decision_info = {'vu_id': vu_id, 'vu_position': VU['position'], 'task_id': task['id'], 'offloading_type': 0, 'estimated_latency_ms': latencies['VU_latency']}

            # Update decision if RSU offloading is valid and offers lower latency without exceeding max allowed latency
            if any(rsu['sojourn_time'] >= latencies['RSU_latency'] for rsu in valid_rsus) and latencies['RSU_latency'] < decision_info['estimated_latency_ms'] and latencies['RSU_latency'] <= task['max_latency_ms']:
                decision_info.update({'offloading_type': 1, 'estimated_latency_ms': latencies['RSU_latency']})

            # Update decision if HAP offloading offers the lowest latency without exceeding max allowed latency
            if latencies['HAP_latency'] < decision_info['estimated_latency_ms'] and latencies['HAP_latency'] <= task['max_latency_ms']:
                decision_info.update({'offloading_type': 2, 'estimated_latency_ms': latencies['HAP_latency']})

            offloading_decisions.append(decision_info)

    return offloading_decisions







for vu_id, VU in VUs.items():
    valid_rsu_results = find_valid_rsu(VU, RSUs)
    print(f"Results for {vu_id}:")
    for result in valid_rsu_results:
        print(f"  RSU {result['rsu_id']} is valid with sojourn time {result['sojourn_time']} ms and distance to leave coverage {result['distance_to_leave_coverage']} meters.")

offloading_decisions = offload_tasks(VUs, RSUs, HAP)
for decision in offloading_decisions:
    print(decision)
