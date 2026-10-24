"""Build extras/visual.html: an interactive replay of the Stone Drop duel and
Master Hyo's alpha-beta tree.  NOT part of the submission.

It imports thornwood.py, so every number on the page is computed by your own
code.  Run from the repo root:   python extras/export_visual_data.py

Reads  extras/visual_template.html  and writes  extras/visual.html.
"""

import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import thornwood as t  # noqa: E402

INF = t.INF


def enc(x):
    """JSON-friendly number: infinities become the strings 'inf' / '-inf'."""
    if x == INF:
        return "inf"
    if x == -INF:
        return "-inf"
    return x


def top_first(board):
    """Board as 5 strings, top row first (same layout as the Scroll Box)."""
    return ["".join(board[r]) for r in range(t.ROWS - 1, -1, -1)]


# ----------------------------------------------------------------------
# Stone Drop: best line of play for every first move
# ----------------------------------------------------------------------
_memo = {}


def value(board, player):
    """Exact minimax value (memoised here only, never inside thornwood.py)."""
    key = (tuple(tuple(r) for r in board), player)
    if key not in _memo:
        u = t.terminal_utility(board)
        if u is not None:
            _memo[key] = u
        else:
            vals = [value(t.drop(board, c, player), t.other_player(player))
                    for c in t.legal_moves(board, t.FULL_ORDER)]
            _memo[key] = max(vals) if player == "X" else min(vals)
    return _memo[key]


def landing_row(board, col):
    """Row where a stone dropped in `col` would land."""
    for r in range(t.ROWS):
        if board[r][col] == ".":
            return r
    raise ValueError("column full")


def line_of_play(first_col):
    """Principal variation after X's first move: both sides play their best,
    taking the first column (order 0..4) among equally good ones."""
    board = t.initial_board()
    steps = []
    player = "X"
    col = first_col
    while True:
        row = landing_row(board, col)
        board = t.drop(board, col, player)
        steps.append({"p": player, "col": col, "row": row, "board": top_first(board)})
        if t.terminal_utility(board) is not None:
            break
        player = t.other_player(player)
        target = value(board, player)
        col = next(c for c in t.legal_moves(board, t.FULL_ORDER)
                   if value(t.drop(board, c, player), t.other_player(player)) == target)
    who = t.winner(board)
    cells = []
    if who:
        for window in t.WINDOWS:
            if all(board[r][c] == who for r, c in window):
                cells = [list(cell) for cell in window]
                break
    empty = sum(row.count(".") for row in board)
    return steps, {"winner": who, "empty": empty,
                   "utility": t.terminal_utility(board), "cells": cells}


def stone_drop_data():
    start = t.initial_board()
    moves = []
    for col in t.legal_moves(start, t.FULL_ORDER):
        steps, result = line_of_play(col)
        moves.append({"col": col,
                      "value": value(t.drop(start, col, "X"), "O"),
                      "steps": steps, "result": result})
    return top_first(start), moves


# ----------------------------------------------------------------------
# Master Hyo's tree: event trace of the same fail-soft alpha-beta
# ----------------------------------------------------------------------
def tree_shape(node):
    if "value" in node:
        return {"name": node["name"], "value": node["value"]}
    return {"name": node["name"], "children": [tree_shape(c) for c in node["children"]]}


def trace_tree(reverse):
    """Replay the alpha-beta of thornwood.tree_alphabeta, recording events."""
    root = t.build_tree()
    events = []

    def go(node, is_max, alpha, beta):
        if "value" in node:
            events.append({"k": "leaf", "n": node["name"], "v": node["value"],
                           "a": enc(alpha), "b": enc(beta)})
            return node["value"]
        events.append({"k": "visit", "n": node["name"], "a": enc(alpha), "b": enc(beta)})
        kids = node["children"][::-1] if reverse else node["children"]
        v = -INF if is_max else INF
        fired, skipped, fa, fb = False, [], alpha, beta
        for i, child in enumerate(kids):
            r = go(child, not is_max, alpha, beta)
            if is_max:
                v = max(v, r)
                if v >= beta:
                    fired, skipped, fa, fb = True, [k["name"] for k in kids[i + 1:]], alpha, beta
                    break
                alpha = max(alpha, v)
            else:
                v = min(v, r)
                if v <= alpha:
                    fired, skipped, fa, fb = True, [k["name"] for k in kids[i + 1:]], alpha, beta
                    break
                beta = min(beta, v)
        events.append({"k": "ret", "n": node["name"], "v": v, "fired": fired,
                       "skipped": skipped, "a": enc(fa), "b": enc(fb)})
        return v

    go(root, True, -INF, INF)
    return events


# ----------------------------------------------------------------------
# Mission 1: hill climbing, random restart, simulated annealing
# ----------------------------------------------------------------------
def climb_path(start):
    """Cells visited by steepest-ascent hill climbing (same rule as
    thornwood.hill_climb), including the start cell."""
    cell = start
    path = [list(cell)]
    while True:
        r, c = cell
        best_cell, best_value = cell, t.GRID[r][c]
        for _, (nr, nc) in t.neighbours(r, c):
            if t.GRID[nr][nc] > best_value:
                best_value, best_cell = t.GRID[nr][nc], (nr, nc)
        if best_cell == cell:
            return path
        cell = best_cell
        path.append(list(cell))


def sa_trace(seed, start_temperature):
    """Same draws, in the same order, as thornwood.simulated_annealing, but
    recording every iteration so the page can replay it.

    d = direction drawn, a = 1 accepted / 0 rejected downhill / 2 off the map,
    r = the acceptance draw (or -1 when none was drawn).
    """
    rng = random.Random(seed)
    cur = (0, 0)
    cur_value = t.GRID[0][0]
    best_value = cur_value
    temperature = start_temperature
    accepted = 0
    dirs, acc, draws = [], [], []
    for _ in range(200):
        d = int(rng.random() * 4)
        dr, dc = t.DIRECTIONS[d]
        nr, nc = cur[0] + dr, cur[1] + dc
        dirs.append(d)
        if 0 <= nr < len(t.GRID) and 0 <= nc < len(t.GRID[0]):
            delta = t.GRID[nr][nc] - cur_value
            if delta >= 0:
                move, r = True, -1
            else:
                r = rng.random()
                move = r < math.exp(delta / temperature)
            acc.append(1 if move else 0)
            draws.append(round(r, 4) if r >= 0 else -1)
            if move:
                cur, cur_value = (nr, nc), t.GRID[nr][nc]
                accepted += 1
                best_value = max(best_value, cur_value)
        else:
            acc.append(2)
            draws.append(-1)
        temperature *= 0.97
    expected = t.simulated_annealing(seed, start_temperature)
    assert (cur, cur_value, best_value, accepted) == expected, (seed, start_temperature)
    return {"d": dirs, "a": acc, "r": draws, "final": list(cur), "finalValue": cur_value,
            "best": best_value, "accepted": accepted}


def mission1_data():
    starts = [(0, 0), (4, 0), (7, 0), (0, 4)]
    climbs = []
    for s in starts:
        path = climb_path(s)
        final, value, steps = t.hill_climb(s)
        assert path[-1] == list(final) and len(path) - 1 == steps
        climbs.append({"start": list(s), "path": path, "value": value, "steps": steps})
    rr_value, rr_start, rr_steps = t.random_restart(starts)
    assert rr_value == max(c["value"] for c in climbs)
    assert rr_steps == sum(c["steps"] for c in climbs)
    runs = {}
    success = {}
    for heat in (20.0, 40.0):
        key = str(int(heat))
        runs[key] = {str(seed): sa_trace(seed, heat) for seed in range(1, 21)}
        success[key] = sum(1 for r in runs[key].values() if r["finalValue"] == 95)
    assert success["20"] == t.fate_test(range(1, 21))
    return {"grid": t.GRID, "climbs": climbs, "bestStart": list(rr_start),
            "runs": runs, "success": success}


# ----------------------------------------------------------------------
# Mission 2: genetic algorithm vs the true optimum
# ----------------------------------------------------------------------
TOOL_NAMES = ["Kunai set", "Wire spool", "Smoke bombs", "Paper bombs", "Energy pills",
              "Flash tags", "Messenger scroll", "Giant shuriken", "Spare rations",
              "Wind shuriken", "Twin blades", "Caltrops", "Medical kit",
              "Grappling hook", "Binding tags"]


def ga_trace(seed=12, generations=50):
    """Same loop as thornwood.genetic_algorithm, built from its own helper
    functions in the same order, recording best/average/chromosome per generation."""
    rng = random.Random(seed)
    pop = [[int(b) for b in chrom] for chrom in t.GEN0]
    best, avg, chrom = [], [], []
    for g in range(generations + 1):
        ranked = t.rank_population(pop)
        fits = [t.fitness(c) for c in pop]
        best.append(fits[ranked[0]])
        avg.append(round(sum(fits) / len(fits), 2))
        chrom.append("".join(map(str, pop[ranked[0]])))
        if g == generations:
            break
        nxt = [list(pop[ranked[0]]), list(pop[ranked[1]])]
        while len(nxt) < 20:
            p1 = t.tournament(pop, rng)
            p2 = t.tournament(pop, rng)
            c1, c2 = t.crossover(p1, p2, rng)
            nxt.append(t.mutate(c1, rng))
            nxt.append(t.mutate(c2, rng))
        pop = nxt
    return best, avg, chrom


def mission2_data():
    ga = t.genetic_algorithm()
    best, avg, chrom = ga_trace()
    assert best == [ga["history"][g] for g in range(51)]
    assert chrom[-1] == ga["best_chromosome"]
    assert abs(avg[-1] - ga["final_average"]) < 0.005
    opt_fitness, opt_chrom = t.brute_force_optimum()

    feasible = better = 0
    for mask in range(1 << 15):
        bits = [(mask >> k) & 1 for k in range(15)]
        load = sum(b * tool[0] for b, tool in zip(bits, t.TOOLS))
        volume = sum(b * tool[1] for b, tool in zip(bits, t.TOOLS))
        if load <= t.MAX_LOAD and volume <= t.MAX_VOLUME:
            feasible += 1
            if t.fitness(bits) > ga["best_fitness"]:
                better += 1
    tools = [{"name": TOOL_NAMES[i], "load": l, "vol": v, "use": u}
             for i, (l, v, u) in enumerate(t.TOOLS)]
    return {"tools": tools, "limits": {"load": t.MAX_LOAD, "vol": t.MAX_VOLUME},
            "best": best, "avg": avg, "chrom": chrom,
            "ga": {"chromosome": ga["best_chromosome"], "fitness": ga["best_fitness"],
                   "firstGen": ga["first_generation"], "finalAvg": ga["final_average"]},
            "opt": {"chromosome": opt_chrom, "fitness": opt_fitness},
            "pouches": {"total": 1 << 15, "feasible": feasible, "better": better}}


def main():
    start, moves = stone_drop_data()

    mm_value, mm_move, mm_nodes, mm_leaves = t.solve_minimax()
    dl_value, dl_move, dl_nodes = t.solve_depth_limited()
    ab1 = t.solve_alphabeta(None, t.FULL_ORDER)
    ab2 = t.solve_alphabeta(None, t.MIDDLE_FIRST)
    ab3 = t.solve_alphabeta(4, t.FULL_ORDER)

    lr = trace_tree(False)
    rl = trace_tree(True)
    tv, tm, lr_leaves, lr_list, b2 = t.solve_tree()
    rl_leaves = t.solve_tree(reverse=True)[2]

    # Guard against drift between the trace and thornwood.py
    assert [e["n"] for e in lr if e["k"] == "leaf"] == lr_list
    assert sum(1 for e in rl if e["k"] == "leaf") == rl_leaves
    assert lr[-1]["v"] == tv
    best_col = max(moves, key=lambda m: m["value"])["col"]
    assert best_col == mm_move and max(m["value"] for m in moves) == mm_value

    data = {
        "m1": mission1_data(),
        "m2": mission2_data(),
        "start": start,
        "moves": moves,
        "mm": {"value": mm_value, "move": mm_move, "nodes": mm_nodes, "leaves": mm_leaves},
        "counts": {"mm": mm_nodes, "ab1": ab1[2], "ab2": ab2[2],
                   "dl": dl_nodes, "ab3": ab3[2]},
        "status": "SUCCESS" if mm_value > 0 else "FAILED",
        "tree": tree_shape(t.build_tree()),
        "trace": {"lr": lr, "rl": rl},
        "treeSummary": {"value": tv, "move": tm, "lrLeaves": lr_leaves,
                        "rlLeaves": rl_leaves,
                        "b2": [enc(b2[0]), enc(b2[1])]},
    }

    with open(os.path.join(HERE, "visual_template.html"), encoding="utf-8") as f:
        template = f.read()
    page = template.replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
    out = os.path.join(HERE, "visual.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"wrote {out} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
