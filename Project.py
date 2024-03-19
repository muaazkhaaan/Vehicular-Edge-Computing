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

# Number of tasks
num_tasks = 20  

# Initialize VUs with their properties, randomly place them on the road, and assign a random direction
VUs = {
    f'VU_{i+1}': {
        'speed': VU_speed,
        'GFLOPS': VU_GFLOPS,
        'position': random.uniform(0, l),
        'direction': random.choice(['left', 'right'])  
    } for i in range(VU_m)
}

# Initialize RSUs with their properties and randomly place them on the road
RSUs = {
    f'RSU_{i+1}': {
        'GFLOPS': RSU_GFLOPS,
        'position': random.uniform(0, l),
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

# Generate tasks with size and max required latency
tasks = [
    {
        'id': f'Task {i+1}',
        'size_MB': random.randint(1, 5),  # Size in MB
        'max_latency_ms': random.randint(100, 5000)  # Max required latency in ms
    } for i in range(num_tasks)
]
