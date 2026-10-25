"""Thornwood Rescue: prints the 36-line Owl Cipher report.

Standard library only, no input. For randomness each run makes
rng = random.Random(seed) and only ever calls rng.random().
"""

import math
import random

INF = float("inf")

# ---- data from the scroll boxes ----

# Scroll Box 1: safety map, GRID[row][col]
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
# directions 0..3 are up, right, down, left, as (row change, column change)
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

# Scroll Box 2: each tool is (load, volume, usefulness), list index = tool number
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

# Scroll Box 3: Stone Drop starting board, written top row first
COLS, ROWS = 5, 5
START_TOP_FIRST = [
    ".....",   # row 4
    ".O.X.",   # row 3
    "XX.O.",   # row 2
    "OXOO.",   # row 1
    "OXXXO",   # row 0
]

# Scroll Box 4 part B: Master Hyo's tree. Leaves are named L1..L60 from left to right.
# Levels: R is MAX, A/B/C are MIN, then A1.. are MAX, then A1a.. are MIN, then leaves.
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


# ---- mission 1: lookout climb ----

def neighbours(r, c):
    """In-map neighbours as (direction, cell), in up, right, down, left order."""
    result = []
    for direction, (dr, dc) in enumerate(DIRECTIONS):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(GRID) and 0 <= nc < len(GRID[0]):
            result.append((direction, (nr, nc)))
    return result


def hill_climb(start):
    """Steepest-ascent hill climbing. Returns (final cell, value, steps)."""
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
    """Hill climb from every start. Returns (best value, first start that reached it, total steps)."""
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
    """Simulated annealing for 200 iterations from (0,0).

    Returns (final cell, final value, best value, accepted moves).
    """
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
    """Number of the given seeds whose annealing run ends on 95."""
    count = 0
    for seed in seeds:
        final_cell, final_value, _, _ = simulated_annealing(seed)
        if final_value == 95:
            count += 1
    return count


# ---- mission 2: tool pouch ----

def fitness(chrom):
    """Total usefulness if the pouch is within both limits, otherwise 0."""
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
    """Population indices, best fitness first. Ties keep the lower position."""
    return sorted(range(len(pop)), key=lambda i: (-fitness(pop[i]), i))


def tournament(pop, rng):
    """Draw three positions and return the fittest. A tie goes to the first drawn."""
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
    """One-point crossover with chance 0.9, otherwise plain copies. Returns two new lists."""
    if rng.random() < 0.9:
        cut = int(rng.random() * 14) + 1
        child1 = list(p1[:cut]) + list(p2[cut:])
        child2 = list(p2[:cut]) + list(p1[cut:])
    else:
        child1 = list(p1)
        child2 = list(p2)
    return child1, child2


def mutate(chrom, rng):
    """Flip each bit with chance 1/15. Returns a new list."""
    child = list(chrom)
    for i in range(15):
        if rng.random() < 1 / 15:
            child[i] = 1 - child[i]
    return child


def genetic_algorithm(seed=12, generations=50):
    """Run the genetic algorithm and return what the GA report lines need."""
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
    """Try all 2^15 pouches. Returns (best fitness, its chromosome)."""
    best_fitness = -1
    best_chromosome = None
    for mask in range(1 << 15):
        chrom = [(mask >> bit) & 1 for bit in range(15)]
        score = fitness(chrom)
        if score > best_fitness:
            best_fitness = score
            best_chromosome = ''.join(map(str, chrom))
    return best_fitness, best_chromosome


# ---- mission 3: Stone Drop ----
# The board is board[row][col] with row 0 at the bottom, so stones fall toward row 0.
# Cells are '.', 'X' or 'O'. X (Pine team) maximises, O (Vesper) minimises.

PLAYER_MAX = "X"
PLAYER_MIN = "O"
FULL_ORDER = [0, 1, 2, 3, 4]     # column order for most runs
MIDDLE_FIRST = [2, 1, 3, 0, 4]   # column order for run AB2


def other_player(player):
    """The other player."""
    return PLAYER_MIN if player == PLAYER_MAX else PLAYER_MAX


def initial_board():
    """Starting board, with row 0 at the bottom (the text is written top row first)."""
    return [list(row) for row in reversed(START_TOP_FIRST)]


def legal_moves(board, order):
    """Columns from `order` that still have room (top cell empty)."""
    return [col for col in order if board[ROWS - 1][col] == "."]


def drop(board, col, player):
    """Copy of the board with the player's stone dropped into column `col`.

    The original board is left alone because the search still needs it.
    """
    new_board = [row[:] for row in board]
    for row in range(ROWS):
        if new_board[row][col] == ".":
            new_board[row][col] = player
            break
    return new_board


def all_windows():
    """The 28 lines of four cells on the board: across, up and both diagonals.

    A window is a start cell plus a direction, kept only if its last cell is
    on the board. That gives 10 across, 10 up and 4 + 4 diagonals.
    """
    windows = []
    for d_row, d_col in [(0, 1), (1, 0), (1, 1), (1, -1)]:
        for row in range(ROWS):
            for col in range(COLS):
                last_row = row + 3 * d_row
                last_col = col + 3 * d_col
                if 0 <= last_row < ROWS and 0 <= last_col < COLS:
                    windows.append(tuple(
                        (row + i * d_row, col + i * d_col) for i in range(4)
                    ))
    return windows


# computed once so the search doesn't rebuild it every time
WINDOWS = all_windows()


def winner(board):
    """Return 'X' or 'O' if that player has four in a line, else None."""
    for window in WINDOWS:
        first = board[window[0][0]][window[0][1]]
        if first != "." and all(board[r][c] == first for r, c in window):
            return first
    return None


def terminal_utility(board):
    """Utility of a finished game, or None if play continues.

    X winning is 1 + E, O winning is -(1 + E) and a full board is 0, where E
    is the number of empty cells. A draw is 0, so callers check `is not None`.
    """
    who = winner(board)
    empty = sum(row.count(".") for row in board)
    if who == PLAYER_MAX:
        return 1 + empty
    if who == PLAYER_MIN:
        return -(1 + empty)
    if empty == 0:
        return 0
    return None


def evaluate(board):
    """Score for an unfinished position, used when the depth runs out.

    For each of the 28 windows: k X stones and no O adds k*k, k O stones and
    no X subtracts k*k, anything else adds 0.
    """
    score = 0
    for window in WINDOWS:
        x_count = 0
        o_count = 0
        for r, c in window:
            if board[r][c] == PLAYER_MAX:
                x_count += 1
            elif board[r][c] == PLAYER_MIN:
                o_count += 1
        if x_count > 0 and o_count == 0:
            score += x_count * x_count
        elif o_count > 0 and x_count == 0:
            score -= o_count * o_count
    return score


def minimax(board, player, order, counters):
    """Full minimax to the end of the game. X takes the highest child value, O the lowest.

    Every call is a node and every finished position is a leaf, with no
    memoization. `counters` is {"nodes": .., "leaves": ..}, updated in place.
    """
    counters["nodes"] += 1
    utility = terminal_utility(board)
    if utility is not None:                      # finished game, counts as a leaf
        counters["leaves"] += 1
        return utility

    other = other_player(player)
    if player == PLAYER_MAX:
        best = -INF
        for col in legal_moves(board, order):
            child = drop(board, col, player)
            best = max(best, minimax(child, other, order, counters))
    else:
        best = INF
        for col in legal_moves(board, order):
            child = drop(board, col, player)
            best = min(best, minimax(child, other, order, counters))
    return best


def minimax_depth(board, player, depth, order, counters):
    """Minimax that looks `depth` moves ahead and then falls back on evaluate().

    A finished game scores utility * 1000. That check comes before the depth
    check, so a game ending exactly at depth 0 still gets its real result.
    """
    counters["nodes"] += 1
    utility = terminal_utility(board)
    if utility is not None:
        return utility * 1000
    if depth == 0:
        return evaluate(board)

    other = other_player(player)
    if player == PLAYER_MAX:
        best = -INF
        for col in legal_moves(board, order):
            child = drop(board, col, player)
            best = max(best, minimax_depth(child, other, depth - 1, order, counters))
    else:
        best = INF
        for col in legal_moves(board, order):
            child = drop(board, col, player)
            best = min(best, minimax_depth(child, other, depth - 1, order, counters))
    return best


def solve_minimax():
    """Full minimax from the start position, columns 0 to 4.

    Returns (value, best move, nodes, leaves). The root loop lives here so it
    can keep the first column whose value is strictly better than all earlier ones.
    """
    board = initial_board()
    counters = {"nodes": 1, "leaves": 0}         # the root counts as one node
    best_value, best_move = -INF, None
    for col in legal_moves(board, FULL_ORDER):
        value = minimax(drop(board, col, PLAYER_MAX), PLAYER_MIN, FULL_ORDER, counters)
        if value > best_value:                   # strictly better, so ties keep the first column
            best_value, best_move = value, col
    return best_value, best_move, counters["nodes"], counters["leaves"]


def solve_depth_limited():
    """Depth-4 minimax from the start position, columns 0 to 4.

    Returns (value, best move, nodes). The root is depth 4, so its children get depth 3.
    """
    board = initial_board()
    counters = {"nodes": 1, "leaves": 0}
    best_value, best_move = -INF, None
    for col in legal_moves(board, FULL_ORDER):
        value = minimax_depth(drop(board, col, PLAYER_MAX), PLAYER_MIN, 3,
                              FULL_ORDER, counters)
        if value > best_value:
            best_value, best_move = value, col
    return best_value, best_move, counters["nodes"]


# ---- mission 4: alpha-beta ----
# Same game and same answers as minimax, but branches that can't change the
# result are skipped. alpha is the best value MAX is already sure of, beta is
# the same for MIN.

def alphabeta(board, player, depth, alpha, beta, order, counters):
    """Fail-soft alpha-beta for Stone Drop.

    depth=None searches to the end of the game. Otherwise it is depth-limited:
    finished games score utility * 1000 and depth 0 scores evaluate().
    A MAX node stops once v >= beta, a MIN node once v <= alpha, and in both
    cases returns v itself.
    """
    counters["nodes"] += 1
    utility = terminal_utility(board)
    if utility is not None:
        return utility if depth is None else utility * 1000
    if depth is not None and depth == 0:
        return evaluate(board)

    child_depth = None if depth is None else depth - 1
    other = other_player(player)

    if player == PLAYER_MAX:
        v = -INF
        for col in legal_moves(board, order):
            child = drop(board, col, player)
            v = max(v, alphabeta(child, other, child_depth, alpha, beta, order, counters))
            if v >= beta:                        # the MIN parent would avoid this branch
                return v
            alpha = max(alpha, v)
        return v

    v = INF
    for col in legal_moves(board, order):
        child = drop(board, col, player)
        v = min(v, alphabeta(child, other, child_depth, alpha, beta, order, counters))
        if v <= alpha:                           # the MAX parent already has something better
            return v
        beta = min(beta, v)
    return v


def solve_alphabeta(depth, order):
    """Alpha-beta from the start position. Returns (value, best move, nodes).

    The root is a plain MAX node with alpha=-inf and beta=inf. Its loop is
    here so it can keep the first column that is strictly better than the
    earlier ones.
    """
    board = initial_board()
    counters = {"nodes": 1, "leaves": 0}
    alpha, beta = -INF, INF
    child_depth = None if depth is None else depth - 1
    best_value, best_move = -INF, None
    for col in legal_moves(board, order):
        value = alphabeta(drop(board, col, PLAYER_MAX), PLAYER_MIN, child_depth,
                          alpha, beta, order, counters)
        if value > best_value:
            best_value, best_move = value, col
        if best_value >= beta:                   # can't happen at the root since beta is inf
            break
        alpha = max(alpha, best_value)
    return best_value, best_move, counters["nodes"]


def build_tree():
    """Build the tree from TREE_SPEC as nested dicts, naming leaves L1..L60 left to right.

    Internal nodes are {"name": .., "children": [..]}, leaves are {"name": "L7", "value": 2}.
    """
    leaf_counter = [0]                            # a list so make() can update it

    def make(name, spec):
        """Build one node, recursing into the levels below."""
        if isinstance(spec, dict):                # not at the bottom yet
            return {"name": name,
                    "children": [make(k, v) for k, v in spec.items()]}
        children = []                             # bottom level: spec is a list of leaf values
        for value in spec:
            leaf_counter[0] += 1
            children.append({"name": f"L{leaf_counter[0]}", "value": value})
        return {"name": name, "children": children}

    return make("R", TREE_SPEC)


def tree_alphabeta(node, is_max, alpha, beta, log, windows, reverse=False):
    """Fail-soft alpha-beta on Master Hyo's tree.

    `log` gets the leaf names in the order they are read, and `windows` stores
    the (alpha, beta) each node was called with. reverse=True goes right to left.
    """
    windows[node["name"]] = (alpha, beta)
    if "value" in node:                           # leaf
        log.append(node["name"])
        return node["value"]

    children = node["children"][::-1] if reverse else node["children"]
    if is_max:
        v = -INF
        for child in children:
            v = max(v, tree_alphabeta(child, False, alpha, beta, log, windows, reverse))
            if v >= beta:
                return v
            alpha = max(alpha, v)
        return v

    v = INF
    for child in children:
        v = min(v, tree_alphabeta(child, True, alpha, beta, log, windows, reverse))
        if v <= alpha:
            return v
        beta = min(beta, v)
    return v


def solve_tree(reverse=False):
    """Alpha-beta over Master Hyo's tree from the root R (a MAX node).

    Returns (value, best move A/B/C, leaves read, leaf list, B2's window).
    The best move is the first child strictly better than the earlier ones.
    """
    root = build_tree()
    log, windows = [], {}
    windows["R"] = (-INF, INF)
    alpha, beta = -INF, INF
    best_value, best_move = -INF, None
    children = root["children"][::-1] if reverse else root["children"]
    for child in children:
        value = tree_alphabeta(child, False, alpha, beta, log, windows, reverse)
        if value > best_value:
            best_value, best_move = value, child["name"]
        if best_value >= beta:
            break
        alpha = max(alpha, best_value)
    return best_value, best_move, len(log), log, windows.get("B2")


# ---- report: exactly 36 lines, nothing else is printed ----

def fmt_cell(cell):
    """Format a cell as (r,c) with no spaces."""
    return f"({cell[0]},{cell[1]})"


def fmt_num(x):
    """Infinities as inf and -inf, anything else with str()."""
    if x == INF:
        return "inf"
    if x == -INF:
        return "-inf"
    return str(x)


def main():
    """Run the four missions and print the report."""
    # mission 1
    hc_cell, hc_value, hc_steps = hill_climb((0, 0))
    rr_value, rr_start, rr_steps = random_restart([(0, 0), (4, 0), (7, 0), (0, 4)])
    sa_cell, sa_value, sa_best, sa_accepted = simulated_annealing(2)
    sa_success = fate_test(range(1, 21))

    # mission 2
    ga = genetic_algorithm()
    opt_fitness, opt_chromosome = brute_force_optimum()

    # mission 3
    mm_value, mm_move, mm_nodes, mm_leaves = solve_minimax()
    dl_value, dl_move, dl_nodes = solve_depth_limited()

    # mission 4
    ab1 = solve_alphabeta(None, FULL_ORDER)       # full depth, columns 0..4
    ab2 = solve_alphabeta(None, MIDDLE_FIRST)     # full depth, middle first
    ab3 = solve_alphabeta(4, FULL_ORDER)          # depth 4 with the evaluation
    tree_value, tree_move, lr_leaves, lr_list, b2_window = solve_tree()
    rl_leaves = solve_tree(reverse=True)[2]

    lines = [
        "=== OWL CIPHER ===",
        f"HC_FINAL: {fmt_cell(hc_cell)}",
        f"HC_VALUE: {hc_value}",
        f"HC_STEPS: {hc_steps}",
        f"RR_BEST_VALUE: {rr_value}",
        f"RR_BEST_START: {fmt_cell(rr_start)}",
        f"RR_TOTAL_STEPS: {rr_steps}",
        f"SA_FINAL: {fmt_cell(sa_cell)}",
        f"SA_FINAL_VALUE: {sa_value}",
        f"SA_BEST_VALUE: {sa_best}",
        f"SA_ACCEPTED: {sa_accepted}",
        f"SA_SUCCESS_1_TO_20: {sa_success}",
        "GA_GEN_BEST: " + ",".join(str(v) for v in ga["generation_best"]),
        f"GA_BEST_CHROMOSOME: {ga['best_chromosome']}",
        f"GA_BEST_FITNESS: {ga['best_fitness']}",
        f"GA_FIRST_GEN: {ga['first_generation']}",
        f"GA_FINAL_AVG: {ga['final_average']:.2f}",
        f"OPT_FITNESS: {opt_fitness}",
        f"OPT_CHROMOSOME: {opt_chromosome}",
        f"MM_VALUE: {mm_value}",
        f"MM_MOVE: {mm_move}",
        f"MM_NODES: {mm_nodes}",
        f"MM_LEAVES: {mm_leaves}",
        f"DL_VALUE: {dl_value}",
        f"DL_MOVE: {dl_move}",
        f"DL_NODES: {dl_nodes}",
        f"AB1: {ab1[0]},{ab1[1]},{ab1[2]}",
        f"AB2: {ab2[0]},{ab2[1]},{ab2[2]}",
        f"AB3: {ab3[0]},{ab3[1]},{ab3[2]}",
        f"TREE_VALUE: {tree_value}",
        f"TREE_MOVE: {tree_move}",
        f"TREE_LR_LEAVES: {lr_leaves}",
        "TREE_LR_LIST: " + ",".join(lr_list),
        f"TREE_B2_WINDOW: ({fmt_num(b2_window[0])},{fmt_num(b2_window[1])})",
        f"TREE_RL_LEAVES: {rl_leaves}",
        f"MISSION_STATUS: {'SUCCESS' if mm_value > 0 else 'FAILED'}",
    ]
    print("\n".join(lines))


if __name__ == "__main__":
    main()