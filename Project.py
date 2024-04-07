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
        'max_latency_ms': random.randint(100, 5000)  # Max required latency in ms
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

def find_rsu_and_calculate_distance(VU, RSUs):
    results = []
    for rsu_id, rsu in RSUs.items():
        distance_to_rsu_center = abs(VU['position'] - rsu['position'])
        if distance_to_rsu_center <= rsu['coverage']:
            distance_to_rsu_edge = None
            if VU['direction'] == 'right':
                distance_to_rsu_edge = (rsu['position'] + rsu['coverage']) - VU['position']
            else:  # VU direction is 'left'
                distance_to_rsu_edge = VU['position'] - (rsu['position'] - rsu['coverage'])
            
            results.append({
                'rsu_id': rsu_id,
                'rsu_details': rsu,
                'distance_to_leave_coverage': distance_to_rsu_edge
            })

    return results

