import math
import copy

class Gate:
    def __init__(self, name, qubits, label):
        self.name = name
        self.qubits = qubits
        self.label = label

# The following function will check if there are dependencies between two gates
def are_dependencies(gate_prev, gate):   
    qubits1 = gate_prev.qubits
    qubits2 = gate.qubits
    if qubits1[0] in qubits2 or qubits1[1] in qubits2:
        return True
    else:
        return False

# The following function will create a dependency graph
def create_dependency_graph(circuit):
    graph = {}
    for gate in circuit:
        for gate_prev in circuit:
            if gate_prev == gate:
                break
            elif are_dependencies(gate_prev, gate):
                if gate.label not in graph:
                    graph[gate.label] = set()
                for values in list(graph[gate.label]):
                    if values in graph[gate_prev.label]:
                        graph[gate.label].remove(values)
                graph[gate.label].add(gate_prev.label)
    return graph

# The following function will create a qubit interaction graph. Two qubits are considered interacting if there
# is a two qubit gate acting on them
def create_qubit_interaction_graph(circuit):
    last_gate = {}
    interaction_graph = {}
    for gate in circuit:
        qubits = gate.qubits
        last_gate[qubits[0]] = gate.label
        last_gate[qubits[1]] = gate.label
        if qubits[0] in interaction_graph:
            interaction_graph[qubits[0]].append(qubits[1])
        else:
            initial_list = [qubits[1]]
            interaction_graph[qubits[0]] = initial_list
        if qubits[1] in interaction_graph:
            interaction_graph[qubits[1]].append(qubits[0])
        else:
            initial_list = [qubits[0]]
            interaction_graph[qubits[1]] = initial_list
    return interaction_graph, last_gate # last_gate is the list containing the last gates of each qubit in the circuit

def resizing_opportunities(qubit_reuse_pairs, qubit_interaction_graph):
    n = len(qubit_interaction_graph)
    dp = [[[] for _ in range(len(qubit_reuse_pairs) + 1)] for _ in range(len(qubit_reuse_pairs) + 1)]
    value_dp = [[0 for _ in range(len(qubit_reuse_pairs) + 1)] for _ in range(len(qubit_reuse_pairs) + 1)]
    for ind in range(len(qubit_reuse_pairs)):
        dp[ind][0] = qubit_reuse_pairs[ind]
        dp[0][ind] = qubit_reuse_pairs[ind]
        value_dp[ind][0] = 1
        value_dp[0][ind] = 1
    for ind in range(1, len(qubit_reuse_pairs) + 1):
        for ind2 in range(1, len(qubit_reuse_pairs) + 1):
            # new_list = list(qubit_reuse_pairs[ind][ind2])
            qubs = list(qubit_reuse_pairs[ind2-1])
            if qubs[0] in dp[ind][ind2-1] or qubs[1] in dp[ind][ind2-1]:
                if value_dp[ind][ind2-1] == value_dp[ind2-1][ind]:
                    dp[ind][ind2] = dp[ind][ind2-1]
                    value_dp[ind][ind2] = value_dp[ind][ind2-1]
                elif value_dp[ind][ind2-1] > value_dp[ind2-1][ind]:
                    dp[ind][ind2] = dp[ind][ind2-1]
                    value_dp[ind][ind2] = value_dp[ind][ind2-1]
                elif value_dp[ind][ind2-1] < value_dp[ind2-1][ind]:
                    dp[ind][ind2] = dp[ind2-1][ind]
                    value_dp[ind][ind2] = value_dp[ind2-1][ind]
            else:
                if (1 + value_dp[ind][ind2-1]) == value_dp[ind2-1][ind]:
                    dp[ind][ind2] = list(dp[ind][ind2-1]) + qubs
                    value_dp[ind][ind2] = 1 + value_dp[ind][ind2-1]
                elif (1 + value_dp[ind][ind2-1]) > value_dp[ind2-1][ind]:
                    dp[ind][ind2] = list(dp[ind][ind2-1]) + qubs
                    value_dp[ind][ind2] = 1 + value_dp[ind][ind2-1]
                elif (1 + value_dp[ind][ind2-1]) < value_dp[ind2-1][ind]:
                    dp[ind][ind2] = dp[ind2-1][ind]
                    value_dp[ind][ind2] = value_dp[ind2-1][ind]
    return dp, value_dp

#This is Depth-First-Search which will be used to find cyclical dependency among qubits
def dfs(dependency_graph, start_gate, target_gate):
    if start_gate not in dependency_graph or target_gate not in dependency_graph:
        return False
    for nodes in dependency_graph[start_gate]:
        if nodes == target_gate:
            return True
        elif dfs(dependency_graph, nodes, target_gate):
            return True
    return False

# This function will basically arrange the tuples in order such that in (qi, qj), qi is reused by qj
def correct_tuples(reuse_pairs, last_gate, circuit):
    pairs_to_delete = []
    pairs_to_add = []
    for pair in reuse_pairs:
        for gate in circuit:
            if gate.label == last_gate[pair[0]]:
                break
            elif gate.label == last_gate[pair[1]]:
                temp_list = list(pair)
                temp_var = temp_list[0]
                temp_list[0] = temp_list[1]
                temp_list[1] = temp_var
                pairs_to_delete.append(pair)
                new_pair = tuple(temp_list)
                pairs_to_add.append(new_pair)
                break
    for pair in pairs_to_delete:
        reuse_pairs.remove(pair)
    for pair in pairs_to_add:
        reuse_pairs.append(pair)
    return reuse_pairs

# This function checks the two conditions for qubit_reusability: (i) No gate among those qubits
# (ii) No future dependence between the qubits.
def check_conditions(qubit_interaction_graph, dependency_graph, circuit):
    reuse_pair_candidate = []
    n = len(qubit_interaction_graph)
    for i in range(n):
        for j in range(i+1, n):
            if j not in qubit_interaction_graph[i]:
                reuse_pair_candidate.append(tuple((i, j)))
    
    # Collect pairs to remove instead of removing during iteration
    pairs_to_remove = []
    for pairs in reuse_pair_candidate:
        qubit1 = pairs[0]
        qubit2 = pairs[1]
        gate_list1 = []
        gate_list2 = []
        for gate in circuit:
            qubits = gate.qubits
            if qubits[0] == qubit1 or qubits[1] == qubit1:
                gate_list1.append(gate.label)
            elif qubits[0] == qubit2 or qubits[1] == qubit2:
                gate_list2.append(gate.label)
        flag = True
        for gate1 in gate_list1:
            for gate2 in gate_list2:
                if dfs(dependency_graph, gate1, gate2):
                    if dfs(dependency_graph, gate2, gate1):
                        pairs_to_remove.append(pairs)
                        flag = False
                        break
            if not flag:
                break   
    
    # Remove collected pairs
    for pair in pairs_to_remove:
        reuse_pair_candidate.remove(pair)
    
    return reuse_pair_candidate

def refine_circuit(circuit):
    gates_to_remove = []
    for gate in circuit:
        if len(gate.qubits) == 1:
            gates_to_remove.append(gate)
    for gate in gates_to_remove:
        circuit.remove(gate)
    return circuit

if __name__ == "__main__":
    circuit = [
        Gate('CX', [0, 2], 'g0'),
        Gate('X', [4], 'g1'),
        Gate('CX', [2, 4], 'g2'),
        Gate('CX', [0, 4], 'g3'),
        Gate('H', [2], 'g4'),
        Gate('CX', [1, 2], 'g5'),
        Gate('CX', [1, 3], 'g6'),
        Gate('CX', [3, 2], 'g7')
    ]
    circuit = refine_circuit(circuit)
    dependency_graph = create_dependency_graph(circuit)
    qubit_interaction_graph, last_gate_dict = create_qubit_interaction_graph(circuit)
    qubit_reuse_pairs = check_conditions(qubit_interaction_graph, dependency_graph, circuit)
    qubit_reuse_pairs = correct_tuples(qubit_reuse_pairs, last_gate_dict, circuit)
    
    dp, value_dp = resizing_opportunities(qubit_reuse_pairs, qubit_interaction_graph)
    optimal_qubit_resize = value_dp[len(qubit_reuse_pairs)][len(qubit_reuse_pairs)]
    set_of_tuples = set()

    for i in range(len(qubit_reuse_pairs), -1, -1):
        for j in range(len(qubit_reuse_pairs), -1, -1):
            if value_dp[i][j] != optimal_qubit_resize:
                continue
            temp_list = []
            for ind in range(0, len(dp[i][j]), 2):
                temp_list.append((dp[i][j][ind], dp[i][j][ind+1]))
            temp_list.sort()
            set_of_tuples.add(tuple(temp_list))

    print(f'The following best resizing opportunities are present in the given circuit which will reduce the circuit size from {len(qubit_interaction_graph)} to {len(qubit_interaction_graph) - optimal_qubit_resize}:')
    for opportunities in set_of_tuples:
        print('-------------------------------')
        for pairs in opportunities:
            print(f'Qubit {pairs[0]} can be reused for qubit {pairs[1]}')