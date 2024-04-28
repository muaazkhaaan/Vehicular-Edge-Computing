import random
import networkx as nx

# Define constants
VU_m = 10  # Number of Vehicle Units (VUs)
RSU_n = 8  # Number of Roadside Units (RSUs)
l = 1000  # Road length in meters
VU_speed = 6  # Speed of VUs in m/s
VU_GFLOPS = 8  # GFLOPS for VUs
RSU_GFLOPS = 80  # GFLOPS for RSUs
RSU_coverage = 20  # Coverage radius in meters for RSUs
HAP_GFLOPS = 150  # GFLOPS for HAP
max_tasks_per_VU = 15 # Maximum number of tasks a VU can have

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

def store_initial_vu_states(VUs):
    initial_states = {}
    for vu_id, vu in VUs.items():
        initial_states[vu_id] = vu.copy()  
    return initial_states

# Store the initial state before any test runs
initial_vu_states = store_initial_vu_states(VUs)

def reset_vus_to_initial_state(VUs, initial_states):
    for vu_id, vu in VUs.items():
        vu.update(initial_states[vu_id])  # Reset each VU to its initial state

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

def offload_task(G, task_node, capacity):
    edges = list(G.out_edges(task_node, data=True))
    random.shuffle(edges)  # Randomise edge selection to prevent bias
    for edge in edges:
        _, target, data = edge
        if target.startswith('RSU') and capacity[target] < 10 or target == 'HAP' and capacity[target] < 5:
            capacity[target] += 1
            return target, data['weight']

    return None, None  # If no valid offload found

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

total_max_latency = 0  # Initialize the total of maximum latencies

def generate_initial_solution(G, alpha):
    solution = {}
    capacity = {'HAP': 0, **{f'RSU_{i}': 0 for i in range(1, RSU_n + 1)}}
    tasks_to_remove = []

    for task_node in G.nodes():
        edges = list(G.out_edges(task_node, data=True))
        if not edges:
            continue
        # Apply a randomised selection based on alpha
        edges = sorted(edges, key=lambda x: x[2]['weight'])
        threshold = int(len(edges) * alpha)
        selected_edge = random.choice(edges[:max(1, threshold)])

        _, target, data = selected_edge
        if target.startswith('RSU') and capacity[target] < 10 or target == 'HAP' and capacity[target] < 5:
            capacity[target] += 1
            solution[task_node] = (target, data['weight'])
            tasks_to_remove.append(task_node)

    G.remove_nodes_from(tasks_to_remove)
    return solution, bool(tasks_to_remove)

def local_search(solution, G, VUs, RSUs, HAP):
    improved = True
    decision_vector = {}  # Initialize the decision vector
    while improved:
        improved = False
        for task_node, (assigned_to, latency) in list(solution.items()):
            decision_vector[task_node] = get_offloading_option(assigned_to)  # Initial assignment
            for edge in G.edges(task_node, data=True):
                target = edge[1]
                new_latency = edge[2]['weight']

                if new_latency < latency:
                    if (target.startswith('RSU') and RSUs[target]['task_count'] < RSUs[target]['max_tasks']) or \
                       (target == 'HAP' and HAP['task_count'] < HAP['max_tasks']):
                        solution[task_node] = (target, new_latency)
                        
                        if assigned_to.startswith('RSU'):
                            RSUs[assigned_to]['task_count'] -= 1
                        elif assigned_to == 'HAP':
                            HAP['task_count'] -= 1

                        if target.startswith('RSU'):
                            RSUs[target]['task_count'] += 1
                        elif target == 'HAP':
                            HAP['task_count'] += 1
                        
                        decision_vector[task_node] = get_offloading_option(target)  # Update decision
                        improved = True
                        break

    return solution, decision_vector

def print_vu_states(VUs):
    print("Current VU states:")
    for vu_id, vu in VUs.items():
        print(f"{vu_id}: Position={vu['position']}, Direction={vu['direction']}, Tasks={len(vu['tasks'])}")

def print_graph_details(graph):
    print("Current Graph Details:")
    print(f"Number of Nodes: {graph.number_of_nodes()}")
    print(f"Number of Edges: {graph.number_of_edges()}")
    for node in graph.nodes(data=True):
        print(f"Node: {node}")
    for edge in graph.edges(data=True):
        print(f"Edge from {edge[0]} to {edge[1]}, weight={edge[2]['weight']}")

def get_offloading_option(target):
    if 'RSU' in target:
        return 0  # RSU offloading
    elif 'HAP' in target:
        return 1  # HAP offloading
    else:
        return -1  # Undefined or error case

def format_decision_vector(decision_vector):
    # Sort tasks by VU and Task number
    sorted_tasks = sorted(
        decision_vector.items(),
        key=lambda x: (int(x[0].split('_')[1]), int(x[0].split('_')[2][5:]))  # Current format "VU_1_Task_1"
    )
    # Create a string of decisions from the sorted list
    decision_string = ''.join(str(dec) for _, dec in sorted_tasks)
    return decision_string

alpha_values = [0.1 * i for i in range(1, 10)]  # Generates [0.1, 0.2, ..., 0.9]
results = {}

for alpha in alpha_values:
    graph = create_offloading_graph(VUs, RSUs, HAP)
    reset_vus_to_initial_state(VUs, initial_vu_states)

    total_max_latency = 0
    final_decision_vector = {}  # To combine decisions from multiple phases

    while graph.number_of_edges() > 0:
        solution, offloaded_any = generate_initial_solution(graph, alpha)
        if not offloaded_any:
            print("No more tasks can be offloaded due to capacity limits.")
            break

        solution, decision_vector = local_search(solution, graph, VUs, RSUs, HAP)
        update_vehicle_positions(VUs, 504.5 / 1000)
        update_graph(graph, VUs, RSUs, HAP)

        final_decision_vector.update(decision_vector)  # Combine current decisions

        max_latency_this_loop = max((data[1] for data in solution.values()), default=0)
        total_max_latency += max_latency_this_loop

    results[alpha] = total_max_latency
    decision_string = format_decision_vector(final_decision_vector)
    print(f"End of Test with Alpha {alpha:.1f}: Total Max Latency (ms)= {total_max_latency:.4f}, Decisions = {decision_string}")



