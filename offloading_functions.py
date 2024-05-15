from model import *

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
    decision_vector = {}  # Initialise the decision vector
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

