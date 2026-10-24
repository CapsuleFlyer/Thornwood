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
# The board is a list of 5 rows: board[row][col], and row 0 is the BOTTOM row
# (stones fall towards row 0). Every cell is '.', 'X' or 'O'.
# X (the Pine team) is the MAX player, O (Vesper) is the MIN player.

PLAYER_MAX = "X"
PLAYER_MIN = "O"
FULL_ORDER = [0, 1, 2, 3, 4]     # column order used by most runs
MIDDLE_FIRST = [2, 1, 3, 0, 4]   # column order for run AB2


def other_player(player):
    """Return the opponent of `player` ('X' <-> 'O')."""
    return PLAYER_MIN if player == PLAYER_MAX else PLAYER_MAX


def initial_board():
    """Build the starting board from START_TOP_FIRST.

    The text is written with the top row first, so we reverse it to make
    row 0 the bottom row, and turn each string into a list of characters.
    """
    return [list(row) for row in reversed(START_TOP_FIRST)]


def legal_moves(board, order):
    """Columns in `order` that are not full.

    A column is full when its top cell (row ROWS-1) is already taken, so
    that is the only cell we need to look at.
    """
    return [col for col in order if board[ROWS - 1][col] == "."]


def drop(board, col, player):
    """Return a NEW board with `player`'s stone dropped into column `col`.

    The stone falls to the lowest empty cell. We copy every row first so the
    parent board is never changed (the search needs it back unchanged).
    """
    new_board = [row[:] for row in board]
    for row in range(ROWS):
        if new_board[row][col] == ".":
            new_board[row][col] = player
            break
    return new_board


def all_windows():
    """Return the 28 four-cell windows (lines of four) of the 5x5 board.

    A window is a start cell plus a direction: across, up, diagonal up-right
    and diagonal up-left. It only counts if its last cell is still on the board.
    Count: 10 across + 10 up + 4 + 4 diagonals = 28.
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


# Built once, so the search never has to rebuild the windows.
WINDOWS = all_windows()


def winner(board):
    """Return 'X' or 'O' if that player has four in a line, else None."""
    for window in WINDOWS:
        first = board[window[0][0]][window[0][1]]
        if first != "." and all(board[r][c] == first for r, c in window):
            return first
    return None


def terminal_utility(board):
    """Return the utility of a finished game, or None if the game goes on.

    X wins -> 1 + E, O wins -> -(1 + E), full board with no line -> 0, where
    E is the number of empty cells (so faster wins score higher).
    NOTE: a draw returns 0, so callers must test `is not None`, never `if utility`.
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
    """Heuristic score of an unfinished position (used when depth runs out).

    Look at all 28 windows. A window with k >= 1 X stones and no O stone is
    still open for X and adds k*k; the same for O subtracts k*k. Windows with
    both colours (or none) are dead and add 0. Squaring rewards fuller lines.
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
    """Full-depth minimax: search every line of play to the end of the game.

    X picks the child with the highest value and O the lowest, because we
    assume Vesper always plays her best. Every call counts as a node, and
    every finished position reached counts as a leaf. No memoization.
    `counters` is a dict {"nodes": .., "leaves": ..} updated in place.
    """
    counters["nodes"] += 1
    utility = terminal_utility(board)
    if utility is not None:                      # game over: this is a leaf
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
    """Depth-limited minimax: look `depth` moves ahead, then trust evaluate().

    A finished game returns utility * 1000 (so a real win or loss always beats
    any heuristic guess). An unfinished position at depth 0 returns evaluate().
    The finished-game test comes first, so a game that ends exactly at depth 0
    is still scored as a real result.
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
    """Full minimax from the starting position, order 0,1,2,3,4.

    Returns (value, best_move, nodes, leaves). The root is handled here (not in
    minimax) so we can remember WHICH column gave the best value. Best move =
    the first column whose value is strictly better than every earlier column.
    """
    board = initial_board()
    counters = {"nodes": 1, "leaves": 0}         # the root position is one node
    best_value, best_move = -INF, None
    for col in legal_moves(board, FULL_ORDER):
        value = minimax(drop(board, col, PLAYER_MAX), PLAYER_MIN, FULL_ORDER, counters)
        if value > best_value:                   # strictly better -> ties keep the first
            best_value, best_move = value, col
    return best_value, best_move, counters["nodes"], counters["leaves"]


def solve_depth_limited():
    """Depth-4 minimax with the evaluation, order 0,1,2,3,4.

    Returns (value, best_move, nodes). The root has depth 4, so its children
    are searched with depth 3.
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


# ======================================================================
# MISSION 4: Alpha-beta (Scroll Box 4)
# ======================================================================
# Same game and same answers as minimax, but we skip branches that cannot
# change the result. alpha = best value MAX is already sure of, beta = best
# value MIN is already sure of.

def alphabeta(board, player, depth, alpha, beta, order, counters):
    """Fail-soft alpha-beta search for Stone Drop.

    depth=None means search to the end of the game (finished games score as
    plain utility). Otherwise it is the depth-limited version (finished games
    score utility * 1000, depth 0 scores evaluate()).
    MAX node: stop as soon as v >= beta. MIN node: stop as soon as v <= alpha.
    Fail-soft: when we stop, return v itself, never alpha or beta.
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
            if v >= beta:                        # MIN above will never allow this
                return v
            alpha = max(alpha, v)
        return v

    v = INF
    for col in legal_moves(board, order):
        child = drop(board, col, player)
        v = min(v, alphabeta(child, other, child_depth, alpha, beta, order, counters))
        if v <= alpha:                           # MAX above already has better
            return v
        beta = min(beta, v)
    return v


def solve_alphabeta(depth, order):
    """Alpha-beta from the starting position. Returns (value, best_move, nodes).

    The root is an ordinary MAX node starting with alpha=-inf, beta=+inf. We
    loop over its children here so we can remember the best column (first one
    strictly better than all earlier ones). Pruned siblings return values <= alpha,
    so they can never wrongly replace the best move.
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
        if best_value >= beta:                   # never true at the root (beta = inf)
            break
        alpha = max(alpha, best_value)
    return best_value, best_move, counters["nodes"]


def build_tree():
    """Turn TREE_SPEC into a tree of dicts, naming leaves L1..L60.

    Internal node: {"name": .., "children": [..]}. Leaf: {"name": "L7", "value": 2}.
    Leaves are numbered left to right in the order they appear in TREE_SPEC.
    """
    leaf_counter = [0]                            # list so the inner function can change it

    def make(name, spec):
        if isinstance(spec, dict):                # more levels below
            return {"name": name,
                    "children": [make(k, v) for k, v in spec.items()]}
        children = []                             # spec is a list of leaf values
        for value in spec:
            leaf_counter[0] += 1
            children.append({"name": f"L{leaf_counter[0]}", "value": value})
        return {"name": name, "children": children}

    return make("R", TREE_SPEC)


def tree_alphabeta(node, is_max, alpha, beta, log, windows, reverse=False):
    """Fail-soft alpha-beta over Master Hyo's tree.

    `log` collects the names of evaluated leaves in the order they are reached.
    `windows` maps each node's name to the (alpha, beta) it received when the
    search called it. reverse=True visits children right to left.
    """
    windows[node["name"]] = (alpha, beta)
    if "value" in node:                           # a leaf: read its value
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
    """Run alpha-beta on Master Hyo's tree from the root R (a MAX node).

    Returns (value, best_move, leaves_evaluated, leaf_list, b2_window), where
    best_move is A, B or C (first child strictly better than the earlier ones)
    and b2_window is the (alpha, beta) that node B2 received.
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
    # --- Mission 1 ---
    hc_cell, hc_value, hc_steps = hill_climb((0, 0))
    rr_value, rr_start, rr_steps = random_restart([(0, 0), (4, 0), (7, 0), (0, 4)])
    sa_cell, sa_value, sa_best, sa_accepted = simulated_annealing(2)
    sa_success = fate_test(range(1, 21))

    # --- Mission 2 ---
    ga = genetic_algorithm()
    opt_fitness, opt_chromosome = brute_force_optimum()

    # --- Mission 3 ---
    mm_value, mm_move, mm_nodes, mm_leaves = solve_minimax()
    dl_value, dl_move, dl_nodes = solve_depth_limited()

    # --- Mission 4 ---
    ab1 = solve_alphabeta(None, FULL_ORDER)       # full depth, columns 0..4
    ab2 = solve_alphabeta(None, MIDDLE_FIRST)     # full depth, middle first
    ab3 = solve_alphabeta(4, FULL_ORDER)          # depth 4 with evaluation
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
