"""Extra experiments for the debrief (NOT part of the Owl Cipher submission).

Each qN_* function answers one Chapter 5 question.  It reuses thornwood.py
(so every number comes from the submitted code), prints a short readable
section, and returns its numbers as a dict.  extras/build_debrief_pdf.py calls
these same functions, so debrief.pdf and debrief.md can never disagree with
the code.

Where an experiment needs a variation thornwood.py does not offer (another
cooling rate, another mutation rate, a custom move order) the variation is
written here, and an assert checks that its default settings reproduce
thornwood.py exactly.  Randomness follows the course rule: random.Random(seed)
and rng.random() only.

Run from the repo root:   python extras/debrief_runs.py          (about 1 minute)
Quick mode (skips the 200-seed GA study):   python extras/debrief_runs.py --quick
"""

import heapq
import itertools
import math
import os
import random
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import thornwood as t  # noqa: E402

INF = t.INF
SIDE = ("up", "right", "down", "left")


def say(show, text=""):
    if show:
        print(text)


# ======================================================================
# Q1  Kaito: the exact false summit
# ======================================================================
def q1_kaito_local_maximum(show=True):
    """Show the exact cell where hill climbing from (0,0) stopped, all of its
    neighbours, and how much of a dip separates it from the real summit."""
    grid = t.GRID
    final, value, steps = t.hill_climb((0, 0))

    # replay the climb cell by cell, using the same tie rule as thornwood.py
    path, cell = [(0, 0)], (0, 0)
    while True:
        r, c = cell
        best_cell, best_value = cell, grid[r][c]
        for _, (nr, nc) in t.neighbours(r, c):
            if grid[nr][nc] > best_value:
                best_cell, best_value = (nr, nc), grid[nr][nc]
        if best_cell == cell:
            break
        cell = best_cell
        path.append(cell)
    assert path[-1] == final and len(path) - 1 == steps

    neigh = [(SIDE[d], rc, grid[rc[0]][rc[1]]) for d, rc in t.neighbours(*final)]
    strict_peaks = [(r, c, grid[r][c]) for r in range(8) for c in range(8)
                    if all(grid[n[0]][n[1]] < grid[r][c] for _, n in t.neighbours(r, c))]

    # the best route from the false summit to the real one: maximise the
    # lowest cell you must step on (a widest-path search)
    summit = max(((grid[r][c], (r, c)) for r in range(8) for c in range(8)))[1]
    best = {final: grid[final[0]][final[1]]}
    heap = [(-best[final], final)]
    while heap:
        b, cur = heapq.heappop(heap)
        b = -b
        if cur == summit:
            break
        if b < best.get(cur, -1):
            continue
        for _, n in t.neighbours(*cur):
            nb = min(b, grid[n[0]][n[1]])
            if nb > best.get(n, -1):
                best[n] = nb
                heapq.heappush(heap, (-nb, n))
    lowest_on_route = best[summit]

    r0, c0 = final
    window = [[grid[r][c] if 0 <= r < 8 and 0 <= c < 8 else None
               for c in range(c0 - 1, c0 + 2)] for r in range(r0 - 1, r0 + 2)]
    climbs = [(start,) + t.hill_climb(start) for start in [(0, 0), (4, 0), (7, 0), (0, 4)]]
    out = {"path": [(rc, grid[rc[0]][rc[1]]) for rc in path], "stuck": final, "value": value,
           "climbs": climbs,
           "steps": steps, "neighbours": neigh, "strict_peaks": strict_peaks,
           "summit": summit, "summit_value": grid[summit[0]][summit[1]],
           "lowest_on_route": lowest_on_route, "dip": value - lowest_on_route,
           "window": window}

    say(show, "Q1  Kaito: hill climbing from (0,0)")
    say(show, "  path: " + " -> ".join(f"{rc}={v}" for rc, v in out["path"]))
    say(show, f"  stuck at {final} = {value} after {steps} steps")
    say(show, "  neighbours: " + ", ".join(f"{n} {rc}={v}" for n, rc, v in neigh))
    say(show, "  all four climbs (start, final, value, steps): " + "; ".join(str(c) for c in climbs))
    say(show, f"  strict local maxima on the map: {strict_peaks}")
    say(show, f"  best route to the summit {summit}={out['summit_value']} must step on a "
              f"{lowest_on_route}: a dip of {out['dip']}")
    return out


# ======================================================================
# Q2  Gennai: heat and cooling
# ======================================================================
def sa_variant(seed, start_temperature, cooling=0.97, iterations=200):
    """thornwood.simulated_annealing with the cooling rate as a parameter.
    Also counts accepted downhill moves per quarter of the run."""
    grid = t.GRID
    rng = random.Random(seed)
    cur, cur_value, temp = (0, 0), grid[0][0], start_temperature
    downhill = [0, 0, 0, 0]
    for i in range(iterations):
        d = int(rng.random() * 4)
        nr, nc = cur[0] + t.DIRECTIONS[d][0], cur[1] + t.DIRECTIONS[d][1]
        if 0 <= nr < 8 and 0 <= nc < 8:
            delta = grid[nr][nc] - cur_value
            move = delta >= 0
            if delta < 0:
                move = rng.random() < math.exp(delta / temp)
                if move:
                    downhill[i * 4 // iterations] += 1
            if move:
                cur, cur_value = (nr, nc), grid[nr][nc]
        temp *= cooling
    return cur, cur_value, downhill


def q2_gennai_temperature(show=True, dip=17):
    """Explain how starting heat and cooling rate decide success, and re-run
    the 20 seeds with T0 = 40."""
    for seed in range(1, 21):                     # variant must equal thornwood.py
        assert sa_variant(seed, 20.0)[:2] == t.simulated_annealing(seed, 20.0)[:2]
        assert sa_variant(seed, 40.0)[:2] == t.simulated_annealing(seed, 40.0)[:2]

    def study(heat, cooling=0.97):
        runs = [sa_variant(s, heat, cooling) for s in range(1, 21)]
        ends = Counter((cell, v) for cell, v, _ in runs)
        quarters = [sum(r[2][q] for r in runs) for q in range(4)]
        return {"success": sum(1 for _, v, _ in runs if v == 95), "ends": dict(ends),
                "downhill_by_quarter": quarters}

    base, hot = study(20.0), study(40.0)
    assert base["success"] == t.fate_test(range(1, 21))

    heats, coolings = (10, 20, 40, 80), (0.95, 0.97, 0.99)
    sweep = {(h, c): study(float(h), c)["success"] for h in heats for c in coolings}

    steps = (0, 25, 50, 100, 150, 199)
    schedule = [{"n": n, "T20": 20 * 0.97 ** n, "T40": 40 * 0.97 ** n,
                 "p20": math.exp(-dip / (20 * 0.97 ** n)),
                 "p40": math.exp(-dip / (40 * 0.97 ** n))} for n in steps]
    out = {"t20": base, "t40": hot, "sweep": sweep, "heats": heats, "coolings": coolings,
           "schedule": schedule, "dip": dip,
           "below_one": {20: math.log(1 / 20) / math.log(0.97),
                         40: math.log(1 / 40) / math.log(0.97)},
           # iteration after which crossing the dip has a chance below 1%
           "dip_window_end": {h: math.log(dip / math.log(100) / h) / math.log(0.97) for h in (20, 40)},
           "end_temp_80_99": 80 * 0.99 ** 200}

    say(show, "\nQ2  Gennai: simulated annealing")
    say(show, f"  T0=20: {base['success']}/20 reach 95; endings {base['ends']}")
    say(show, f"  T0=40: {hot['success']}/20 reach 95; endings {hot['ends']}")
    say(show, f"  downhill moves accepted per quarter (20 seeds): T0=20 {base['downhill_by_quarter']}, "
              f"T0=40 {hot['downhill_by_quarter']}")
    say(show, "  chance of accepting the dip (-%d) as the run cools:" % dip)
    for row in schedule:
        say(show, f"    iteration {row['n']:3d}: T0=20 T={row['T20']:6.2f} p={row['p20']:.4f}   "
                  f"T0=40 T={row['T40']:6.2f} p={row['p40']:.4f}")
    say(show, "  crossing the dip drops below a 1%% chance after iteration %.0f (T0=20) and %.0f (T0=40)"
        % (out["dip_window_end"][20], out["dip_window_end"][40]))
    say(show, "  successes out of 20 (rows heat, columns cooling rate):")
    say(show, "         " + "".join(f"{c:>6}" for c in coolings))
    for h in heats:
        say(show, f"    T0={h:<3}" + "".join(f"{sweep[(h, c)]:>6}" for c in coolings))
    return out


# ======================================================================
# Q3  Rin: GA versus the true optimum
# ======================================================================
def mutate_rate(chrom, rng, rate):
    """thornwood.mutate with the per-bit rate as a parameter."""
    child = list(chrom)
    for i in range(15):
        if rng.random() < rate:
            child[i] = 1 - child[i]
    return child


def ga_variant(seed=12, generations=50, mutation=1 / 15):
    """thornwood.genetic_algorithm with the mutation rate as a parameter.
    Returns (best fitness per generation, population per generation)."""
    rng = random.Random(seed)
    pop = [[int(b) for b in chrom] for chrom in t.GEN0]
    history, pops = [], []
    for g in range(generations + 1):
        ranked = t.rank_population(pop)
        history.append(t.fitness(pop[ranked[0]]))
        pops.append([list(c) for c in pop])
        if g == generations:
            break
        nxt = [list(pop[ranked[0]]), list(pop[ranked[1]])]
        while len(nxt) < 20:
            p1 = t.tournament(pop, rng)
            p2 = t.tournament(pop, rng)
            c1, c2 = t.crossover(p1, p2, rng)
            nxt.append(mutate_rate(c1, rng, mutation))
            nxt.append(mutate_rate(c2, rng, mutation))
        pop = nxt
    return history, pops


def pouch_totals(bits):
    """(load, volume, usefulness) of a chromosome string, ignoring the limits."""
    load = vol = use = 0
    for b, (l, v, u) in zip(bits, t.TOOLS):
        if b == "1":
            load, vol, use = load + l, vol + v, use + u
    return load, vol, use


def q3_rin_ga_vs_optimum(show=True, quick=False):
    """Compare the GA best (234) and the true optimum seed by seed, and test
    one fix (a higher mutation rate)."""
    names = ["Kunai set", "Wire spool", "Smoke bombs", "Paper bombs", "Energy pills",
             "Flash tags", "Messenger scroll", "Giant shuriken", "Spare rations",
             "Wind shuriken", "Twin blades", "Caltrops", "Medical kit",
             "Grappling hook", "Binding tags"]
    ga = t.genetic_algorithm()
    opt_fit, opt = t.brute_force_optimum()
    got = ga["best_chromosome"]
    hist, pops = ga_variant()
    assert [hist[g] for g in (0, 10, 20, 30, 40, 50)] == ga["generation_best"]

    rows = [{"i": i, "name": names[i], "load": l, "vol": v, "use": u,
             "ga": int(got[i]), "opt": int(opt[i])} for i, (l, v, u) in enumerate(t.TOOLS)]
    diff = [i for i in range(15) if got[i] != opt[i]]

    def score(bits):
        return t.fitness([int(b) for b in bits])

    # every partial move between the two pouches (flip some, not all, of the differences)
    partial = []
    for k in range(1, len(diff)):
        for sub in itertools.combinations(diff, k):
            bits = list(got)
            for i in sub:
                bits[i] = opt[i]
            bits = "".join(bits)
            partial.append({"flip": sub, "totals": pouch_totals(bits), "score": score(bits)})
    infeasible = sum(1 for p in partial if p["score"] == 0)
    lower = sum(1 for p in partial if 0 < p["score"] < ga["best_fitness"])

    def better_within(k):
        return sum(1 for sub in itertools.combinations(range(15), k)
                   if score("".join(str(1 - int(b)) if j in sub else b
                                    for j, b in enumerate(got))) > ga["best_fitness"])

    zeros_final = sum(1 for c in pops[50] if t.fitness(c) == 0)
    stuck_since = ga["first_generation"]
    distinct_at = {g: len({tuple(c) for c in pops[g]}) for g in (0, stuck_since, 50)}

    fix = {"seed12": {}, "study": {}}
    for label, rate, gens in (("mutation 1/15 (assignment)", 1 / 15, 50),
                              ("mutation 2/15", 2 / 15, 50),
                              ("mutation 3/15", 3 / 15, 50),
                              ("mutation 1/15, 150 generations", 1 / 15, 150)):
        h, _ = ga_variant(12, gens, rate)
        first = next(g for g, v in enumerate(h) if v == max(h))
        fix["seed12"][label] = {"final": h[-1], "best": max(h), "first": first}
    if not quick:
        for label, rate, gens in (("mutation 1/15 (assignment)", 1 / 15, 50),
                                  ("mutation 2/15", 2 / 15, 50),
                                  ("mutation 3/15", 3 / 15, 50),
                                  ("mutation 1/15, 150 generations", 1 / 15, 150)):
            hits = sum(1 for s in range(1, 201) if ga_variant(s, gens, rate)[0][-1] == opt_fit)
            fix["study"][label] = hits

    out = {"rows": rows, "ga": {"bits": got, "fit": ga["best_fitness"], "totals": pouch_totals(got),
                                "first": stuck_since, "avg": ga["final_average"]},
           "opt": {"bits": opt, "fit": opt_fit, "totals": pouch_totals(opt)},
           "diff": diff, "partial": partial, "partial_infeasible": infeasible,
           "partial_lower": lower,
           "better_within": {k: better_within(k) for k in (1, 2, 3, 4)},
           "distinct": distinct_at, "zeros_final": zeros_final, "fix": fix}

    say(show, "\nQ3  Rin: GA versus optimum")
    say(show, f"  GA  {got} fitness {ga['best_fitness']} (load, volume, use) = {out['ga']['totals']}")
    say(show, f"  OPT {opt} fitness {opt_fit} (load, volume, use) = {out['opt']['totals']}")
    say(show, "  tools that differ: " + ", ".join(f"{i} {names[i]} (GA {got[i]}, opt {opt[i]})" for i in diff))
    say(show, f"  better pouches within 1/2/3/4 bit flips of the GA pouch: "
              f"{[out['better_within'][k] for k in (1, 2, 3, 4)]}")
    say(show, f"  the {len(partial)} partial moves between the pouches: {infeasible} break a limit "
              f"(score 0), {lower} are feasible but score below {ga['best_fitness']}")
    for p in partial:
        if p["score"] == 0 and p["totals"][2] > ga["best_fitness"]:
            say(show, f"    near miss: flips {p['flip']} would be worth {p['totals'][2]} "
                      f"but uses load {p['totals'][0]}, volume {p['totals'][1]}")
    say(show, f"  distinct chromosomes in the population: gen 0 {distinct_at[0]}, "
              f"gen {stuck_since} {distinct_at[stuck_since]}, gen 50 {distinct_at[50]}")
    say(show, f"  members of the generation-50 population that break a limit (fitness 0): {zeros_final} of 20")
    say(show, "  seed 12 under each setting (best reached, first generation):")
    for label, r in fix["seed12"].items():
        say(show, f"    {label:34s} final {r['final']}  first reached {r['best']} at gen {r['first']}")
    if fix["study"]:
        say(show, f"  seeds 1..200 that reach {opt_fit}:")
        for label, hits in fix["study"].items():
            say(show, f"    {label:34s} {hits}/200")
    return out


# ======================================================================
# Q4  Vesper: how every losing first move is punished
# ======================================================================
_value_memo = {}


def exact_value(board, player):
    """Exact minimax value, memoised HERE only (never inside thornwood.py)."""
    key = (tuple(tuple(r) for r in board), player)
    if key not in _value_memo:
        u = t.terminal_utility(board)
        if u is None:
            vals = [exact_value(t.drop(board, c, player), t.other_player(player))
                    for c in t.legal_moves(board, t.FULL_ORDER)]
            u = max(vals) if player == "X" else min(vals)
        _value_memo[key] = u
    return _value_memo[key]


def q4_vesper_losing_moves(show=True):
    """For each root move, play out best play on both sides.  Losing moves are
    punished by Vesper's reply; the winning move shows how X survives."""
    start = t.initial_board()
    top = lambda b: ["".join(b[r]) for r in range(4, -1, -1)]  # noqa: E731
    rows = []
    for col in t.legal_moves(start, t.FULL_ORDER):
        board, player, line, c = t.drop(start, col, "X"), "O", [("X", col)], None
        while t.terminal_utility(board) is None:
            target = exact_value(board, player)
            c = next(cc for cc in t.legal_moves(board, t.FULL_ORDER)
                     if exact_value(t.drop(board, cc, player), t.other_player(player)) == target)
            board = t.drop(board, c, player)
            line.append((player, c))
            player = t.other_player(player)
        who = t.winner(board)
        cells = []
        for w in t.WINDOWS:
            if all(board[r][cc] == who for r, cc in w):
                cells = list(w)
                break
        empty = sum(r.count(".") for r in board)
        rows.append({"col": col, "value": exact_value(t.drop(start, col, "X"), "O"),
                     "line": line, "winner": who, "cells": cells, "empty": empty,
                     "utility": t.terminal_utility(board), "final": top(board)})
    assert max(r["value"] for r in rows) == t.solve_minimax()[0]
    out = {"rows": rows, "start": top(start)}

    say(show, "\nQ4  Vesper: best play after each first move")
    for r in rows:
        seq = " ".join(f"{p}{c}" for p, c in r["line"])
        say(show, f"  X{r['col']}: value {r['value']:>3}  {seq}  -> {r['winner']} wins on "
                  f"{r['cells']} with {r['empty']} empty, utility {r['utility']}")
    return out


# ======================================================================
# Q5  Jun: the ki
# ======================================================================
def alphabeta_nodes(order_for):
    """Fail-soft alpha-beta from the start position, where order_for(board,
    player) gives the column order at each node.  Returns (value, nodes)."""
    counter = [0]

    def go(board, player, alpha, beta):
        counter[0] += 1
        u = t.terminal_utility(board)
        if u is not None:
            return u
        other = t.other_player(player)
        if player == "X":
            v = -INF
            for c in order_for(board, player):
                v = max(v, go(t.drop(board, c, player), other, alpha, beta))
                if v >= beta:
                    return v
                alpha = max(alpha, v)
        else:
            v = INF
            for c in order_for(board, player):
                v = min(v, go(t.drop(board, c, player), other, alpha, beta))
                if v <= alpha:
                    return v
                beta = min(beta, v)
        return v

    value = go(t.initial_board(), "X", -INF, INF)
    return value, counter[0]


def count_leaves(node):
    """Number of terminal leaves under a tree node."""
    if "value" in node:
        return 1
    return sum(count_leaves(k) for k in node["children"])


def tree_rows(reverse=False):
    """Trace thornwood's fail-soft alpha-beta on Master Hyo's tree and keep one
    row per internal node down to depth 2 (A, A1, ..., C2)."""
    root = t.build_tree()
    rows, leaves = [], []

    def go(node, is_max, alpha, beta, depth):
        if "value" in node:
            leaves.append(node["name"])
            return node["value"]
        mark = len(leaves)
        kids = node["children"][::-1] if reverse else node["children"]
        v, cut, skipped = (-INF if is_max else INF), False, []
        a_in, b_in = alpha, beta
        for i, child in enumerate(kids):
            r = go(child, not is_max, alpha, beta, depth + 1)
            if is_max:
                v = max(v, r)
                if v >= beta:
                    cut, skipped = True, [k["name"] for k in kids[i + 1:]]
                    break
                alpha = max(alpha, v)
            else:
                v = min(v, r)
                if v <= alpha:
                    cut, skipped = True, [k["name"] for k in kids[i + 1:]]
                    break
                beta = min(beta, v)
        if depth <= 2:
            rows.append({"name": node["name"], "kind": "MAX" if is_max else "MIN",
                         "total": count_leaves(node),
                         "alpha": a_in, "beta": b_in, "value": v, "leaves": len(leaves) - mark,
                         "cut": cut and bool(skipped), "skipped": skipped})
        return v

    go(root, True, -INF, INF, 0)
    wanted = ["R", "A", "A1", "A2", "A3", "B", "B1", "B2", "C", "C1", "C2"]
    rows.sort(key=lambda r: wanted.index(r["name"]))
    return rows, leaves


def q5_jun_node_counts(show=True):
    """Compare node counts of every method; explain why middle-first barely
    helped, and why right-to-left read fewer leaves in the tree."""
    mm_value, mm_move, mm_nodes, mm_leaves = t.solve_minimax()
    dl_value, dl_move, dl_nodes = t.solve_depth_limited()
    ab1 = t.solve_alphabeta(None, t.FULL_ORDER)
    ab2 = t.solve_alphabeta(None, t.MIDDLE_FIRST)
    ab3 = t.solve_alphabeta(4, t.FULL_ORDER)
    counts = {"mm": mm_nodes, "dl": dl_nodes, "ab1": ab1[2], "ab2": ab2[2], "ab3": ab3[2]}

    # every possible fixed column order (120 of them)
    by_order = {}
    for perm in itertools.permutations(range(5)):
        v, n = alphabeta_nodes(lambda b, p, o=list(perm): t.legal_moves(b, o))
        assert v == mm_value
        by_order[perm] = n
    assert by_order[(0, 1, 2, 3, 4)] == ab1[2] and by_order[(2, 1, 3, 0, 4)] == ab2[2]
    ranked = sorted(by_order.values())

    def best_first(board, player):
        cols = t.legal_moves(board, t.FULL_ORDER)
        other = t.other_player(player)
        return sorted(cols, key=lambda c: exact_value(t.drop(board, c, player), other),
                      reverse=(player == "X"))

    def worst_first(board, player):
        return best_first(board, player)[::-1]

    perfect = alphabeta_nodes(best_first)[1]
    worst = alphabeta_nodes(worst_first)[1]
    ordering = {"min": ranked[0], "median": statistics.median(ranked), "max": ranked[-1],
                "best_perm": min(by_order, key=by_order.get),
                "rank_0_4": ranked.index(by_order[(0, 1, 2, 3, 4)]) + 1,
                "rank_mid": ranked.index(by_order[(2, 1, 3, 0, 4)]) + 1,
                "perfect": perfect, "worst": worst}

    lr_rows, lr_leaves = tree_rows(False)
    rl_rows, rl_leaves = tree_rows(True)
    tv, tm, lr_count, lr_list, b2 = t.solve_tree()
    assert lr_leaves == lr_list and len(rl_leaves) == t.solve_tree(reverse=True)[2]
    row_b2 = next(r for r in lr_rows if r["name"] == "B2")
    assert (row_b2["alpha"], row_b2["beta"]) == tuple(b2)

    def split(rows):
        return {r["name"]: r["leaves"] for r in rows if r["name"] in ("A", "B", "C")}

    values = {"mm": mm_value, "dl": dl_value, "ab1": ab1[0], "ab2": ab2[0], "ab3": ab3[0]}
    assert values["ab1"] == values["ab2"] == mm_value and values["ab3"] == dl_value
    out = {"counts": counts, "values": values, "ordering": ordering, "lr_rows": lr_rows, "rl_rows": rl_rows,
           "lr_split": split(lr_rows), "rl_split": split(rl_rows),
           "lr_leaves": len(lr_leaves), "rl_leaves": len(rl_leaves), "lr_list": lr_leaves,
           "tree_value": tv, "tree_move": tm, "b2": b2,
           "node_values": {r["name"]: r["value"] for r in lr_rows}}

    say(show, "\nQ5  Jun: node counts")
    for key, label in (("mm", "full minimax"), ("dl", "depth-limited minimax"),
                       ("ab1", "AB1 full, 0..4"), ("ab2", "AB2 full, middle first"),
                       ("ab3", "AB3 depth 4")):
        say(show, f"  {label:24s}{counts[key]:>9,}")
    say(show, f"  AB2 saves {counts['ab1'] - counts['ab2']} nodes over AB1 "
              f"({(counts['ab1'] - counts['ab2']) / counts['ab1']:.1%})")
    say(show, f"  all 120 fixed column orders: min {ordering['min']:,} {ordering['best_perm']}, "
              f"median {ordering['median']:,.0f}, max {ordering['max']:,}")
    say(show, f"  rank of 0..4 = {ordering['rank_0_4']}/120, rank of middle-first = {ordering['rank_mid']}/120")
    say(show, f"  best move first at every node: {perfect:,} nodes; worst move first: {worst:,}")
    say(show, f"  tree: value {tv} via {tm}; left-to-right reads {len(lr_leaves)} leaves "
              f"{out['lr_split']}, right-to-left reads {len(rl_leaves)} {out['rl_split']}; B2 window {b2}")
    return out


def collect(quick=False):
    """Run every experiment silently and return all results (used by the PDF builder)."""
    return {"q1": q1_kaito_local_maximum(False), "q2": q2_gennai_temperature(False),
            "q3": q3_rin_ga_vs_optimum(False, quick), "q4": q4_vesper_losing_moves(False),
            "q5": q5_jun_node_counts(False)}


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    q1_kaito_local_maximum()
    q2_gennai_temperature()
    q3_rin_ga_vs_optimum(quick=quick)
    q4_vesper_losing_moves()
    q5_jun_node_counts()
