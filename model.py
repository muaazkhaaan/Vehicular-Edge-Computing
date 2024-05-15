import random

# Define constants
VU_m = 10  # Number of Vehicle Users (VUs)
RSU_n = 20  # Number of Roadside Units (RSUs)
l = 1000  # Road length in meters
VU_speed = 6  # Speed of VUs in m/s
VU_GFLOPS = 8  # GFLOPS for VUs
RSU_GFLOPS = 80  # GFLOPS for RSUs
RSU_coverage = 20  # Coverage radius in meters for RSUs
HAP_GFLOPS = 150  # GFLOPS for HAP
max_tasks_per_VU = 10 # Maximum number of tasks a VU can have

def initialise_VUs():
    VUs = {f'VU_{i+1}': {
        'speed': VU_speed,
        'GFLOPS': VU_GFLOPS,
        'position': random.uniform(0, l),
        'direction': random.choice(['left', 'right']),
        'tasks': [{
            'id': f'Task {j+1}',
            # 'size_MB': random.randint(1, 5), # Task size in Mb
            'size_MB': 1, # Task size in Mb for tests 
            'max_latency_ms': random.randint(300, 10000) # Max latency of task
        } 
        # for j in range(random.randint(1, max_tasks_per_VU))], # For random task generation
        for j in range(max_tasks_per_VU)], # Same as max_tasks
    } for i in range(VU_m)}
    return VUs

def initialise_RSUs():
    RSUs = {f'RSU_{i+1}': {
        'GFLOPS': RSU_GFLOPS,
        'position': (i + 1) * (l / (RSU_n + 1)), # Spread the RSUs equally across the road
        'coverage': RSU_coverage,
        'max_tasks': 10,
        'task_count': 0
    } for i in range(RSU_n)}
    return RSUs

def initialise_HAP():
    return {
        'GFLOPS': HAP_GFLOPS,
        'coverage': l,
        'max_tasks': 5,
        'task_count': 0
    }
