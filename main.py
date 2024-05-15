from model import *
from graph_functions import *
from simulation_functions import *
from offloading_functions import *

def find_alpha():
    VUs = initialise_VUs()
    RSUs = initialise_RSUs()
    HAP = initialise_HAP()
    initial_vu_states = store_initial_vu_states(VUs)

    alpha_values = [0.1 * i for i in range(1, 10)]  # Generates [0.1, 0.2, ..., 0.9]
    results = {}
    number_of_runs = 100

    overall_best_alpha = None
    lowest_overall_latency = float('inf')
    overall_best_decision_vector = {}

    for alpha in alpha_values:
        best_latency = float('inf')
        best_decision_vector = {}
        for _ in range(number_of_runs):
            reset_vus_to_initial_state(VUs, initial_vu_states)
            graph = create_offloading_graph(VUs, RSUs, HAP)
            total_max_latency = 0
            final_decision_vector = {}

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

            # Check if the current run has the best latency and update accordingly
            if total_max_latency < best_latency:
                best_latency = total_max_latency
                best_decision_vector = final_decision_vector.copy()

        # Store the best latency and its corresponding decision vector for this alpha
        results[alpha] = (best_latency, best_decision_vector)

        # Update the overall best alpha if the current one has lower latency
        if best_latency < lowest_overall_latency:
            lowest_overall_latency = best_latency
            overall_best_alpha = alpha
            overall_best_decision_vector = best_decision_vector.copy()

    # Print the best results for each alpha
    for alpha, (latency, decision_vector) in results.items():
        decision_string = format_decision_vector(decision_vector)
        print(f"Alpha {alpha:.1f} - Best Latency: {latency:.4f}, Best Decisions: {decision_string}")

    # Print the most optimal alpha
    optimal_decision_string = format_decision_vector(overall_best_decision_vector)
    print(f"The most optimal alpha is {overall_best_alpha:.1f} with the lowest latency of {lowest_overall_latency:.4f}ms. Optimal Decisions: {optimal_decision_string}")

    return overall_best_alpha

def main():
    VUs = initialise_VUs()
    RSUs = initialise_RSUs()
    HAP = initialise_HAP()
    initial_vu_states = store_initial_vu_states(VUs)

    alpha_values = [0.498]
    results = {}
    number_of_runs = 100

    lowest_overall_latency = float('inf')
    overall_best_decision_vector = {}

    for alpha in alpha_values:
        best_latency = float('inf')
        best_decision_vector = {}
        for _ in range(number_of_runs):
            reset_vus_to_initial_state(VUs, initial_vu_states)
            graph = create_offloading_graph(VUs, RSUs, HAP)
            total_max_latency = 0
            final_decision_vector = {}

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

            # Check if the current run has the best latency and update accordingly
            if total_max_latency < best_latency:
                best_latency = total_max_latency
                best_decision_vector = final_decision_vector.copy()

        # Store the best latency and its corresponding decision vector for this alpha
        results[alpha] = (best_latency, best_decision_vector)

        if best_latency < lowest_overall_latency:
            lowest_overall_latency = best_latency
            overall_best_decision_vector = best_decision_vector.copy()

    # Print the best results for each alpha
    for alpha, (latency, decision_vector) in results.items():
        decision_string = format_decision_vector(decision_vector)
        print(f"Alpha {alpha:.3f} - Best Latency: {latency:.4f}, Best Decisions: {decision_string}")

    return decision_string

def test():
    VUs = initialise_VUs()
    RSUs = initialise_RSUs()
    HAP = initialise_HAP()
    initial_vu_states = store_initial_vu_states(VUs)

    alpha_values = [0.498]
    results = {}
    number_of_runs = 100

    lowest_overall_latency = float('inf')
    overall_best_decision_vector = {}

    for alpha in alpha_values:
        best_latency = float('inf')
        best_decision_vector = {}
        for _ in range(number_of_runs):
            reset_vus_to_initial_state(VUs, initial_vu_states)
            graph = create_offloading_graph(VUs, RSUs, HAP)
            total_max_latency = 0
            final_decision_vector = {}

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

            # Check if the current run has the best latency and update accordingly
            if total_max_latency < best_latency:
                best_latency = total_max_latency
                best_decision_vector = final_decision_vector.copy()

        # Store the best latency and its corresponding decision vector for this alpha
        results[alpha] = (best_latency, best_decision_vector)

        if best_latency < lowest_overall_latency:
            lowest_overall_latency = best_latency
            overall_best_decision_vector = best_decision_vector.copy()

    return lowest_overall_latency

def basic():
    VUs = initialise_VUs()
    RSUs = initialise_RSUs()
    HAP = initialise_HAP()
    initial_vu_states = store_initial_vu_states(VUs)

    alpha_values = [0.498]
    results = {}
    number_of_runs = 100

    lowest_overall_latency = float('inf')
    overall_best_decision_vector = {}

    for alpha in alpha_values:
        best_latency = float('inf')
        best_decision_vector = {}
        for _ in range(number_of_runs):
            reset_vus_to_initial_state(VUs, initial_vu_states)
            graph = create_offloading_graph(VUs, RSUs, HAP)
            total_max_latency = 0
            final_decision_vector = {}

            while graph.number_of_edges() > 0:
                solution, offloaded_any = generate_initial_solution(graph, alpha)
                if not offloaded_any:
                    print("No more tasks can be offloaded due to capacity limits.")
                    break

                # solution, decision_vector = local_search(solution, graph, VUs, RSUs, HAP)
                update_vehicle_positions(VUs, 504.5 / 1000)
                update_graph(graph, VUs, RSUs, HAP)

                #final_decision_vector.update(decision_vector)  # Combine current decisions

                max_latency_this_loop = max((data[1] for data in solution.values()), default=0)
                total_max_latency += max_latency_this_loop

            # Check if the current run has the best latency and update accordingly
            if total_max_latency < best_latency:
                best_latency = total_max_latency
                best_decision_vector = final_decision_vector.copy()

        # Store the best latency and its corresponding decision vector for this alpha
        results[alpha] = (best_latency, best_decision_vector)

        if best_latency < lowest_overall_latency:
            lowest_overall_latency = best_latency
            overall_best_decision_vector = best_decision_vector.copy()

    return lowest_overall_latency

# Find optimal alpha
# if __name__ == "__main__":
#     mean_alpha = []
#     for _ in range(100):
#         best_alpha = main()
#         mean_alpha.append(best_alpha)
#         print(mean_alpha)
#     mean = sum(mean_alpha) / len(mean_alpha)
    
#     print(f"The mean of optimal alpha is {mean:.4f}")

# Test runs
# if __name__ == "__main__":
    # num_iterations = 1000
    # total = 0

    # # Loop 1000 times, call test() and sum the results
    # for _ in range(num_iterations):
    #     #total += test()
    #     total += basic()
    #     print(total)

    # # Calculate the mean of the outputs
    # mean_result = total / num_iterations
    # print("Mean of outputs:", mean_result)

# Simulation Runs
if __name__ == "__main__":
    main() 