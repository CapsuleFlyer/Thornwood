"""Thornwood Rescue - Owl Cipher report.

Python 3.10+, standard library only. Takes no input and prints only the
36-line Owl Cipher report (Scroll Box 5).

Randomness rule: create rng = random.Random(seed) and call ONLY rng.random().
Whole number in 0..k-1: int(rng.random() * k). Draw in the exact order the
scroll box describes, and make no other draws.
"""

import math
import random
import itertools  # noqa: F401  (allowed; remove if unused)

INF = float("inf")

# ======================================================================
# DATA (typed exactly from the Scroll Boxes)
# ======================================================================

# --- Scroll Box 1: safety map, GRID[row][col] ---
GRID = [
    [52, 58, 52, 46, 40, 46, 53, 46],
    [58, 64, 58, 52, 46, 58, 60, 53],
    [64, 70, 64, 58, 53, 60, 67, 60],
    [58, 64, 58, 53, 60, 67, 74, 67],
    [52, 58, 53, 50, 67, 74, 81, 74],
    [46, 53, 60, 67, 74, 81, 88, 81],
    [53, 60, 67, 74, 81, 88, 95, 88],
    [46, 53, 60, 67, 74, 81, 88, 81],
]
# Direction numbers 0,1,2,3 = up, right, down, left as (d_row, d_col)
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

# --- Scroll Box 2: tools as (load, volume, usefulness), index = tool number ---
TOOLS = [
    (18, 9, 36),   # 0 Kunai set
    (11, 8, 9),    # 1 Wire spool
    (12, 5, 10),   # 2 Smoke bombs
    (9, 3, 32),    # 3 Paper bombs
    (5, 7, 31),    # 4 Energy pills
    (5, 6, 8),     # 5 Flash tags
    (11, 3, 33),   # 6 Messenger scroll
    (20, 6, 27),   # 7 Giant shuriken
    (13, 6, 5),    # 8 Spare rations
    (11, 2, 35),   # 9 Wind shuriken
    (14, 6, 21),   # 10 Twin blades
    (15, 9, 13),   # 11 Caltrops
    (8, 8, 26),    # 12 Medical kit
    (10, 9, 19),   # 13 Grappling hook
    (10, 7, 38),   # 14 Binding tags
]
MAX_LOAD = 86
MAX_VOLUME = 44

GEN0 = [
    "110101101111101", "100010101111010", "010111011011001",
    "000010110111000", "010001001010000", "110111110111011",
    "000011100111110", "111100000010000", "111011111111111",
    "001111100111111", "011001010000111", "000110000001011",
    "111001000111110", "001001000011010", "011001110010001",
    "011000010011110", "111011001000011", "110110010001011",
    "000001000010100", "001000111111000",
]

# --- Scroll Box 3: Stone Drop starting position (top row first) ---
COLS, ROWS = 5, 5
START_TOP_FIRST = [
    ".....",   # row 4
    ".O.X.",   # row 3
    "XX.O.",   # row 2
    "OXOO.",   # row 1
    "OXXXO",   # row 0
]

# --- Scroll Box 4, Part B: Master Hyo's trial tree ---
# Leaf lists are in left-to-right order; leaves are named L1..L60 in that order.
# R (MAX) -> A,B,C (MIN) -> x1,x2,.. (MAX) -> x1a,x1b,.. (MIN) -> leaves
TREE_SPEC = {
    "A": {
        "A1": {"A1a": [4, -27, -22], "A1b": [-28, 16, 13],
               "A1c": [2, -20, 10], "A1d": [-15, 17, -4]},
        "A2": {"A2a": [24, -29, 12], "A2b": [-21, -22], "A2c": [8, 0]},
        "A3": {"A3a": [-15, 22, 7], "A3b": [-29, 17],
               "A3c": [24, 4, 4], "A3d": [2, -28]},
    },
    "B": {
        "B1": {"B1a": [12, 5, -10], "B1b": [24, 12, -3],
               "B1c": [24, 14, -18], "B1d": [26, 30]},
        "B2": {"B2a": [30, 9], "B2b": [25, -3, 8], "B2c": [-21, -27, -24]},
    },
    "C": {
        "C1": {"C1a": [5, 15, 19], "C1b": [-27, -4], "C1c": [-7, 8]},
        "C2": {"C2a": [-10, -24, -4], "C2b": [30, -4]},
    },
}


# ======================================================================
# MISSION 1: Lookout climb (Scroll Box 1)
# ======================================================================

def neighbours(r, c):
    """Return in-map neighbours in up, right, down, left order."""
    result = []
    for direction, (dr, dc) in enumerate(DIRECTIONS):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(GRID) and 0 <= nc < len(GRID[0]):
            result.append((direction, (nr, nc)))
    return result


def hill_climb(start):
    """Steepest-ascent hill climbing; return (final_cell, value, steps)."""
    cell = start
    steps = 0
    while True:
        r, c = cell
        current_value = GRID[r][c]
        best_cell = cell
        best_value = current_value
        for _, (nr, nc) in neighbours(r, c):
            value = GRID[nr][nc]
            if value > best_value:
                best_value = value
                best_cell = (nr, nc)
        if best_cell == cell:
            return cell, current_value, steps
        cell = best_cell
        steps += 1


def random_restart(starts):
    """Run hill climbing from each start and return best value, first start, total steps."""
    best_value = None
    best_start = None
    total_steps = 0
    for start in starts:
        _, value, steps = hill_climb(start)
        total_steps += steps
        if best_value is None or value > best_value:
            best_value = value
            best_start = start
    return best_value, best_start, total_steps


def simulated_annealing(seed, start_temperature=20.0):
    """Run the specified 200-step simulated annealing procedure."""
    rng = random.Random(seed)
    current = (0, 0)
    current_value = GRID[current[0]][current[1]]
    best_value = current_value
    temperature = start_temperature
    accepted = 0

    for _ in range(200):
        direction = int(rng.random() * 4)
        dr, dc = DIRECTIONS[direction]
        nr, nc = current[0] + dr, current[1] + dc
        if 0 <= nr < len(GRID) and 0 <= nc < len(GRID[0]):
            neighbour = (nr, nc)
            neighbour_value = GRID[nr][nc]
            delta = neighbour_value - current_value
            move = delta >= 0
            if delta < 0:
                move = rng.random() < math.exp(delta / temperature)
            if move:
                current = neighbour
                current_value = neighbour_value
                accepted += 1
                if current_value > best_value:
                    best_value = current_value
        temperature *= 0.97

    return current, current_value, best_value, accepted


def fate_test(seeds):
    """Count seeded simulated-annealing runs ending at value 95."""
    count = 0
    for seed in seeds:
        final_cell, final_value, _, _ = simulated_annealing(seed)
        if final_value == 95:
            count += 1
    return count

# ======================================================================
# MISSION 2: Tool pouch (Scroll Box 2)
# ======================================================================

def fitness(chrom):
    """Return usefulness if both pouch limits are respected; otherwise zero."""
    total_load = 0
    total_volume = 0
    total_usefulness = 0
    for bit, (load, volume, usefulness) in zip(chrom, TOOLS):
        if bit:
            total_load += load
            total_volume += volume
            total_usefulness += usefulness
    if total_load <= MAX_LOAD and total_volume <= MAX_VOLUME:
        return total_usefulness
    return 0


def rank_population(pop):
    """Indices ranked by fitness descending, then original position ascending."""
    return sorted(range(len(pop)), key=lambda i: (-fitness(pop[i]), i))


def tournament(pop, rng):
    """Select the fittest of three drawn positions; ties favor first drawn."""
    draws = [int(rng.random() * 20) for _ in range(3)]
    winner_index = draws[0]
    winner_fitness = fitness(pop[winner_index])
    for index in draws[1:]:
        candidate_fitness = fitness(pop[index])
        if candidate_fitness > winner_fitness:
            winner_index = index
            winner_fitness = candidate_fitness
    return pop[winner_index]


def crossover(p1, p2, rng):
    """Apply one-point crossover with probability 0.9, returning independent lists."""
    if rng.random() < 0.9:
        cut = int(rng.random() * 14) + 1
        child1 = list(p1[:cut]) + list(p2[cut:])
        child2 = list(p2[:cut]) + list(p1[cut:])
    else:
        child1 = list(p1)
        child2 = list(p2)
    return child1, child2


def mutate(chrom, rng):
    """Mutate each bit independently with probability 1/15; return a new list."""
    child = list(chrom)
    for i in range(15):
        if rng.random() < 1 / 15:
            child[i] = 1 - child[i]
    return child


def genetic_algorithm(seed=12, generations=50):
    """Run the specified genetic algorithm and return data for GA report lines."""
    rng = random.Random(seed)
    population = [[int(bit) for bit in chromosome] for chromosome in GEN0]
    generation_best = {}
    best_chromosome = None
    best_fitness = None
    first_generation = None
    final_average = 0.0

    for generation in range(generations + 1):
        ranked = rank_population(population)
        fitnesses = [fitness(chrom) for chrom in population]
        top_index = ranked[0]
        top_fitness = fitnesses[top_index]
        top_chromosome = population[top_index]
        generation_best[generation] = top_fitness
        final_average = sum(fitnesses) / len(fitnesses)

        if generation == generations:
            best_chromosome = ''.join(map(str, top_chromosome))
            best_fitness = top_fitness
            first_generation = next(
                g for g in range(generations + 1)
                if generation_best[g] == best_fitness
            )
            break

        next_population = [
            list(population[ranked[0]]),
            list(population[ranked[1]])
        ]
        while len(next_population) < 20:
            parent1 = tournament(population, rng)
            parent2 = tournament(population, rng)
            child1, child2 = crossover(parent1, parent2, rng)
            next_population.append(mutate(child1, rng))
            next_population.append(mutate(child2, rng))
        population = next_population

    checkpoints = [generation_best[g] for g in (0, 10, 20, 30, 40, generations)]
    return {
        "generation_best": checkpoints,
        "best_chromosome": best_chromosome,
        "best_fitness": best_fitness,
        "first_generation": first_generation,
        "final_average": final_average,
        "history": generation_best,
    }


def brute_force_optimum():
    """Find the exact best pouch by examining all 2^15 bit combinations."""
    best_fitness = -1
    best_chromosome = None
    for mask in range(1 << 15):
        chrom = [(mask >> bit) & 1 for bit in range(15)]
        score = fitness(chrom)
        if score > best_fitness:
            best_fitness = score
            best_chromosome = ''.join(map(str, chrom))
    return best_fitness, best_chromosome

# ======================================================================
# MISSION 3: Stone Drop (Scroll Box 3)
# ======================================================================

def initial_board():
    """Build the starting board from START_TOP_FIRST (row 0 = bottom)."""
    # TODO
    raise NotImplementedError


def legal_moves(board, order):
    """Columns in `order` that are not full."""
    # TODO
    raise NotImplementedError


def drop(board, col, player):
    """Return a NEW board with player's stone dropped into col."""
    # TODO
    raise NotImplementedError


def winner(board):
    """Return 'X', 'O' or None (four in a line: horiz, vert, both diagonals)."""
    # TODO
    raise NotImplementedError


def all_windows():
    """The 28 four-cell windows of the 5x5 board."""
    # TODO
    raise NotImplementedError


def terminal_utility(board):
    """Utility of a finished game: X wins -> 1+E, O wins -> -(1+E), full board
    no line -> 0, where E = empty cells. Return None if not finished."""
    # TODO
    raise NotImplementedError


def evaluate(board):
    """Window evaluation: k>=1 X and no O adds k^2; k>=1 O and no X subtracts
    k^2; otherwise 0."""
    # TODO
    raise NotImplementedError


def minimax(board, player, order, counters):
    """Full-depth minimax. Counts every call as a node, finished positions as
    leaves. No memoization. Return the value."""
    # TODO
    raise NotImplementedError


def minimax_depth(board, player, depth, order, counters):
    """Depth-limited minimax (root depth 4). Finished game -> utility * 1000;
    depth 0 unfinished -> evaluate(). Return the value."""
    # TODO
    raise NotImplementedError


def solve_minimax():
    """Return (value, best_move, nodes, leaves) for the full search,
    order 0,1,2,3,4. Best move = first column strictly better than all earlier."""
    # TODO
    raise NotImplementedError


def solve_depth_limited():
    """Return (value, best_move, nodes) for depth 4, order 0,1,2,3,4."""
    # TODO
    raise NotImplementedError


# ======================================================================
# MISSION 4: Alpha-beta (Scroll Box 4)
# ======================================================================

def alphabeta(board, player, depth, alpha, beta, order, counters):
    """Fail-soft alpha-beta for Stone Drop. MAX: prune if v >= beta;
    MIN: prune if v <= alpha. Return v itself when pruning.
    depth=None means full depth."""
    # TODO
    raise NotImplementedError


def solve_alphabeta(depth, order):
    """Return (value, best_move, nodes). Root is an ordinary MAX node;
    best move = first column strictly better than every earlier one."""
    # TODO
    raise NotImplementedError


def build_tree():
    """Turn TREE_SPEC into a nested structure with leaves named L1..L60
    (numbered left to right)."""
    # TODO
    raise NotImplementedError


def tree_alphabeta(node, is_max, alpha, beta, log, windows):
    """Fail-soft alpha-beta over Master Hyo's tree.

    log collects evaluated leaf names in order; windows records the (alpha, beta)
    each named node receives when called (needed for TREE_B2_WINDOW).
    """
    # TODO
    raise NotImplementedError


def solve_tree(reverse=False):
    """Return (value, best_move 'A'/'B'/'C', leaves_evaluated, leaf_list,
    b2_window). reverse=True visits children right to left at every node."""
    # TODO
    raise NotImplementedError


# ======================================================================
# REPORT (Scroll Box 5): exactly 36 lines, nothing else printed
# ======================================================================

def fmt_cell(cell):
    """(r,c) with no spaces."""
    return f"({cell[0]},{cell[1]})"


def fmt_num(x):
    """Write infinities as -inf and inf; everything else as an integer."""
    if x == INF:
        return "inf"
    if x == -INF:
        return "-inf"
    return str(x)


def main():
    """Run all four missions and print the Owl Cipher report."""
    # TODO: compute everything (no hard-coded answers), then print the lines
    # in EXACTLY this order. One space after each colon, no trailing spaces.
    #
    # print("=== OWL CIPHER ===")
    # print(f"HC_FINAL: {fmt_cell(...)}")
    # print(f"HC_VALUE: {...}")
    # print(f"HC_STEPS: {...}")
    # print(f"RR_BEST_VALUE: {...}")
    # print(f"RR_BEST_START: {fmt_cell(...)}")
    # print(f"RR_TOTAL_STEPS: {...}")
    # print(f"SA_FINAL: {fmt_cell(...)}")
    # print(f"SA_FINAL_VALUE: {...}")
    # print(f"SA_BEST_VALUE: {...}")
    # print(f"SA_ACCEPTED: {...}")
    # print(f"SA_SUCCESS_1_TO_20: {...}")
    # print(f"GA_GEN_BEST: {g0},{g10},{g20},{g30},{g40},{g50}")
    # print(f"GA_BEST_CHROMOSOME: {...}")
    # print(f"GA_BEST_FITNESS: {...}")
    # print(f"GA_FIRST_GEN: {...}")
    # print(f"GA_FINAL_AVG: {avg:.2f}")
    # print(f"OPT_FITNESS: {...}")
    # print(f"OPT_CHROMOSOME: {...}")
    # print(f"MM_VALUE: {...}")
    # print(f"MM_MOVE: {...}")
    # print(f"MM_NODES: {...}")
    # print(f"MM_LEAVES: {...}")
    # print(f"DL_VALUE: {...}")
    # print(f"DL_MOVE: {...}")
    # print(f"DL_NODES: {...}")
    # print(f"AB1: {value},{move},{nodes}")
    # print(f"AB2: {value},{move},{nodes}")
    # print(f"AB3: {value},{move},{nodes}")
    # print(f"TREE_VALUE: {...}")
    # print(f"TREE_MOVE: {...}")
    # print(f"TREE_LR_LEAVES: {...}")
    # print(f"TREE_LR_LIST: {','.join(leaf_list)}")
    # print(f"TREE_B2_WINDOW: ({fmt_num(a)},{fmt_num(b)})")
    # print(f"TREE_RL_LEAVES: {...}")
    # print(f"MISSION_STATUS: {'SUCCESS' if mm_value > 0 else 'FAILED'}")
    raise NotImplementedError


if __name__ == "__main__":
    main()
