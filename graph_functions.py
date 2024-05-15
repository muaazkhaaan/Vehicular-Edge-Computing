import networkx as nx
from offloading_functions import *

def print_graph_details(graph):
    print("Current Graph Details:")
    print(f"Number of Nodes: {graph.number_of_nodes()}")
    print(f"Number of Edges: {graph.number_of_edges()}")
    for node in graph.nodes(data=True):
        print(f"Node: {node}")
    for edge in graph.edges(data=True):
        print(f"Edge from {edge[0]} to {edge[1]}, weight={edge[2]['weight']}")

def print_vu_states(VUs):
    print("Current VU states:")
    for vu_id, vu in VUs.items():
        print(f"{vu_id}: Position={vu['position']}, Direction={vu['direction']}, Tasks={len(vu['tasks'])}")

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
