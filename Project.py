import random
import networkx as nx
import heapq

# Define constants
VU_m = 2  # Number of Vehicle Units (VUs)
RSU_n = 3  # Number of Roadside Units (RSUs)
l = 50  # Road length in meters
VU_speed = 6  # Speed of VUs in m/s
VU_GFLOPS = 8  # GFLOPS for VUs
RSU_GFLOPS = 80  # GFLOPS for RSUs
RSU_coverage = 20  # Coverage radius in meters for RSUs
HAP_GFLOPS = 150  # GFLOPS for HAP
max_tasks_per_VU = 40 # Maximum number of tasks a VU can have

# Initialise the properties of VUs, RSUs, and HAP
VUs = {f'VU_{i+1}': {
    'speed': VU_speed,
    'GFLOPS': VU_GFLOPS,
    'position': random.uniform(0, l),
    'direction': random.choice(['left', 'right']),
    'tasks': [{
        'id': f'Task {j+1}',
        'size_MB': random.randint(1, 5), # Task size in Mb
        'max_latency_ms': random.randint(300, 10000) # Max latency of task
    } for j in range(random.randint(1, max_tasks_per_VU))],
    'task_count': 0,  # Track number of tasks currently being offloaded
    'max_tasks': 1   # VUs can only offload one task at a time
} for i in range(VU_m)}

RSUs = {f'RSU_{i+1}': {
    'GFLOPS': RSU_GFLOPS,
    'position': (i + 1) * (l / (RSU_n + 1)), # Spread the RSUs equally across the road
    'coverage': RSU_coverage,
    'max_tasks': 5,
    'task_count': 0
} for i in range(RSU_n)}

HAP = {
    'GFLOPS': HAP_GFLOPS,
    'coverage': l,
    'max_tasks': 2,
    'task_count': 0
}

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

def find_valid_rsu(VU, RSUs):
    best_rsu = None
    min_distance_to_leave_coverage = float('inf')  # Initialise with a very large number

    for rsu_id, rsu in RSUs.items():
        distance_to_rsu_center = abs(VU['position'] - rsu['position'])
        if distance_to_rsu_center <= rsu['coverage']:
            if VU['direction'] == 'right':
                distance_to_leave_coverage = (rsu['position'] + rsu['coverage']) - VU['position']
            else:  # VU direction is left
                distance_to_leave_coverage = VU['position'] - (rsu['position'] - rsu['coverage'])
            
            # Calculate sojourn time in milliseconds
            sojourn_time = (abs(distance_to_leave_coverage) / VU['speed']) * 1000
            
            # Check if this RSU is the nearest one within coverage the VU will interact with
            if distance_to_leave_coverage < min_distance_to_leave_coverage:
                min_distance_to_leave_coverage = distance_to_leave_coverage
                best_rsu = {
                    'rsu_id': rsu_id,
                    'rsu_details': rsu,
                    'distance_to_leave_coverage': distance_to_leave_coverage,
                    'sojourn_time': sojourn_time
                }

    return best_rsu

def create_offloading_graph(VUs, RSUs, HAP):
    G = nx.DiGraph()
    for vu_id, vu in VUs.items():
        for task in vu['tasks']:
            task_node = f"{vu_id}_{task['id']}"
            G.add_node(task_node)
            latencies = calculate_latency(task, vu, RSUs, HAP)

            valid_rsu = find_valid_rsu(vu, RSUs)
            if valid_rsu and latencies['RSU_latency'] <= task['max_latency_ms']:
                rsu_id = valid_rsu['rsu_id']  
                G.add_edge(task_node, rsu_id, weight=latencies['RSU_latency'], type='RSU')

            if latencies['HAP_latency'] <= task['max_latency_ms']:
                G.add_edge(task_node, "HAP", weight=latencies['HAP_latency'], type='HAP')

    return G

def print_sol(graph):
    # Display nodes
    print("Nodes in the graph:")
    print(list(graph.nodes()))
    
    # Display edges
    print("Edges in the graph:")
    print(list(graph.edges(data=True)))
    
    return list(graph.nodes())

# Create the graph
graph = create_offloading_graph(VUs, RSUs, HAP)

# Print graph
solution = print_sol(graph)

# import matplotlib.pyplot as plt

# # Set node colors based on type
# color_map = []
# for node in graph:
#     if 'VU' in node:
#         color_map.append('pink')
#     elif 'RSU' in node:
#         color_map.append('lightgreen')
#     elif 'HAP' in node:
#         color_map.append('salmon')
#     else:  # Task nodes
#         color_map.append('lightgrey')

# # Set node sizes based on type
# size_map = []
# for node in graph:
#     if 'VU' in node or 'RSU' in node or 'HAP' in node:
#         size_map.append(700)
#     else:  # Task nodes
#         size_map.append(300)

# # Use a spring layout for spreading nodes evenly
# pos = nx.spring_layout(graph, k=0.15, iterations=20)

# # Draw the network
# nx.draw(graph, pos, node_color=color_map, node_size=size_map, with_labels=True, font_size=8)

# # Show the plot
# plt.show()

def offload_task(G, task_node, capacity):
    edges = list(G.out_edges(task_node, data=True))
    random.shuffle(edges)  # Randomise edge selection to prevent bias
    for edge in edges:
        _, target, data = edge
        if target.startswith('RSU') and capacity[target] < 10 or target == 'HAP' and capacity[target] < 5:
            capacity[target] += 1
            return target, data['weight']

    return None, None  # If no valid offload found

def generate_initial_solution(G):
    solution = {}
    capacity = {'HAP': 0, **{f'RSU_{i}': 0 for i in range(1, RSU_n + 1)}}

    tasks_to_remove = []
    for task_node in G.nodes():
        target, weight = offload_task(G, task_node, capacity)
        if target:
            solution[task_node] = (target, weight)
            tasks_to_remove.append(task_node)
        else:
            print(f"Task {task_node} could not be offloaded due to capacity limits.")

    # Remove tasks that have been offloaded from the graph
    G.remove_nodes_from(tasks_to_remove)
    
    return solution, bool(tasks_to_remove)


def update_vehicle_positions(VUs, elapsed_time_sec):
    for vu_id, vu in VUs.items():
        speed = vu['speed']
        direction = vu['direction']
        distance_moved = speed * elapsed_time_sec
        if direction == 'right':
            vu['position'] = min(vu['position'] + distance_moved, l)
            print(vu['position'])
        else:
            vu['position'] = max(vu['position'] - distance_moved, 0)
            print(vu['position'])
    
    return VUs
            
def update_graph(G, VUs, RSUs, HAP):
    # Remove unnecessary edges first
    edges_to_remove = [edge for edge in G.edges(data=True) if 'RSU' in edge[1] or edge[1] == 'HAP']
    G.remove_edges_from(edges_to_remove)

    # Process each node correctly based on its type
    for task_node in list(G.nodes()):
        if task_node.startswith('RSU') or task_node == 'HAP':
            # These are not VU task nodes, skip processing
            continue

        # The format is 'VU_1_Task 1', split by '_' and extract 'VU_1' as vu_id
        parts = task_node.split('_')
        if len(parts) < 3:
            print(f"Invalid task node format: {task_node}")
            continue
        
        vu_id = '_'.join(parts[:2])  # Join the first two parts to form VU_id e.g., 'VU_1'
        task_id = '_'.join(parts[2:])  # The rest is the task_id e.g., 'Task 1'

        if vu_id not in VUs:
            print(f"Error: VU ID {vu_id} from task node {task_node} not found in VUs.")
            continue

        vu = VUs[vu_id]
        task = next((t for t in vu['tasks'] if t['id'] == task_id), None)

        if task:  # Ensure the task exists
            latencies = calculate_latency(task, vu, RSUs, HAP)
            
            # Reconnect RSUs and HAP if conditions are met
            for rsu_id, rsu in RSUs.items():
                valid_rsu = find_valid_rsu(vu, RSUs)
                if valid_rsu and latencies['RSU_latency'] <= task['max_latency_ms']:
                    G.add_edge(task_node, rsu_id, weight=latencies['RSU_latency'], type='RSU')

            if latencies['HAP_latency'] <= task['max_latency_ms']:
                G.add_edge(task_node, "HAP", weight=latencies['HAP_latency'], type='HAP')
    
    return G

while graph.number_of_edges() > 0:
    solution, offloaded_any = generate_initial_solution(graph)
    update_vehicle_positions(VUs, 504.5/1000)
    update_graph(graph, VUs, RSUs, HAP)
    
    if not offloaded_any:
        print("No more tasks can be offloaded due to capacity limits.")
        break
    
    print("\nTasks offloaded in this timestep:", solution)