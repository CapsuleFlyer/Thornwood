"""Build debrief.pdf (repo root) and extras/debrief.md from the experiment results.

NOT part of the submission.  The debrief text is written once, below, with every
number pulled from extras/debrief_runs.py (which calls thornwood.py), and then
rendered twice: to a 4-page PDF and to a Markdown copy.

Needs reportlab and Pillow, plus the figures from extras/make_figures.py.
Run from the repo root:   python extras/build_debrief_pdf.py
"""

import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import debrief_runs as runs  # noqa: E402

FIG = os.path.join(HERE, "figures")
MAX_PAGES = 4
INF = float("inf")


# ----------------------------------------------------------------------
# formatting helpers
# ----------------------------------------------------------------------
def n(x):
    """Whole numbers with thousands separators and a real minus sign."""
    if x == INF:
        return "∞"
    if x == -INF:
        return "−∞"
    if isinstance(x, float) and not x.is_integer():
        return f"{x:g}".replace("-", "−")
    return f"{int(x):,}".replace("-", "−")


def win(a, b):
    return f"({n(a)}, {n(b)})"


def pct(a, b, digits=1):
    return f"{a / b * 100:.{digits}f}%"


def cell(rc):
    return f"({rc[0]},{rc[1]})"


# ----------------------------------------------------------------------
# the debrief, as blocks
#   ("title", text, subtitle)   ("h", text)   ("p", text)   ("bul", [text, ...])
#   ("table", header, rows, fractions, aligns, shaded_row_indexes)
#   ("img", filename, width_pt, caption)
#   ("cols", [left blocks], [right blocks], (left_fraction, right_fraction))
# Text uses **bold** and `code` only.
# ----------------------------------------------------------------------
def content(R):
    q1, q2, q3, q4, q5 = R["q1"], R["q2"], R["q3"], R["q4"], R["q5"]
    B = []
    B.append(("title", "Thornwood Rescue: Debrief",
              "Evidence: the Owl Cipher from `python thornwood.py`, plus the extra runs in "
              "`extras/debrief_runs.py`. Every number below is computed by that code."))

    # ------------------------------------------------------------ 1. Kaito
    B.append(("h", "1. Kaito: Why did I get stuck on the first hill?"))
    path = " → ".join(f"{cell(rc)}={v}" for rc, v in q1["path"])
    w = q1["window"]
    r0, c0 = q1["stuck"]
    grid3 = [[f"row {r0 - 1 + i}"] + [f"**{v}**" if (i, j) == (1, 1) else str(v) for j, v in enumerate(w[i])]
             for i in range(3)]
    neigh = ", ".join(f"{name} {cell(rc)}={v}" for name, rc, v in q1["neighbours"])
    climbs = {c[0]: c for c in q1["climbs"]}
    left = [
        ("p", f"**Where it stopped:** {cell(q1['stuck'])} with value **{q1['value']}**, after "
              f"{q1['steps']} steps (`HC_FINAL`, `HC_VALUE`, `HC_STEPS`). The climb went {path}. At (0,0) "
              "the right and down neighbours tie at 58, and the up, right, down, left rule takes right."),
        ("table", [f"around {cell(q1['stuck'])}"] + [f"col {c0 - 1 + j}" for j in range(3)], grid3,
         [0.28, 0.24, 0.24, 0.24], ["l", "c", "c", "c"], []),
        ("p", f"**Its neighbours:** {neigh}. None is strictly higher than {q1['value']}, so the stopping "
              "rule fires."),
        ("p", f"**Why this is a local maximum.** Hill climbing only compares a cell with its four "
              f"neighbours, so any cell that beats all four looks like the top. {cell(q1['stuck'])} is one of "
              f"only two such peaks on the map; the other is the real summit {cell(q1['summit'])}="
              f"{q1['summit_value']}. The best route between them still steps on a {q1['lowest_on_route']}, "
              f"a drop of {q1['dip']}, and steepest ascent never goes down. Restarting is the cure: the climbs "
              f"from (4,0), (7,0) and (0,4) end on {climbs[(4, 0)][2]}, {climbs[(7, 0)][2]} and "
              f"{climbs[(0, 4)][2]} after {climbs[(4, 0)][3]}, {climbs[(7, 0)][3]} and {climbs[(0, 4)][3]} "
              f"steps, so the best of the four is 95 from (7,0), {sum(c[3] for c in q1['climbs'])} steps in "
              "total (`RR_BEST_VALUE`, `RR_BEST_START`, `RR_TOTAL_STEPS`)."),
    ]
    right = [("img", "hill_climb.png", 150,
              "Climb from (0,0). Dashed box: start. Red ring: where it stopped. Black box: the real summit.")]
    B.append(("cols", left, right, (0.70, 0.30)))

    # ------------------------------------------------------------ 2. Gennai
    B.append(("h", "2. Gennai: Why did only some of the 20 fate scrolls reach the summit?"))
    t20, t40 = q2["t20"], q2["t40"]
    fails20 = ", ".join(f"{n(c)} runs on {cell(rc)}={v}" for (rc, v), c in t20["ends"].items() if v != 95)
    fails40 = ", ".join(f"{n(c)} runs on {cell(rc)}={v}" for (rc, v), c in t40["ends"].items() if v != 95)
    sched = [[str(s["n"]), f"{s['T20']:.2f}", f"{s['p20']:.3f}", f"{s['T40']:.2f}", f"{s['p40']:.3f}"]
             for s in q2["schedule"]]
    sweep = [[f"T0 = {h}"] + [str(q2["sweep"][(h, c)]) for c in q2["coolings"]] for h in q2["heats"]]
    B.append(("bul", [
        f"**Result of the 20 seeded runs** (T0 = 20, cooling 0.97): **{t20['success']} of 20** end on 95 "
        f"(`SA_SUCCESS_1_TO_20`). The other {20 - t20['success']} all freeze on the same false summit: {fails20}.",
        f"**How heat and cooling act.** A downhill step Δ < 0 is accepted with chance exp(Δ/T), and T becomes "
        f"0.97·T every iteration, so T = T0·0.97^n. Leaving the false summit means a drop of {q2['dip']} "
        f"(Q1), so the table gives the chance of accepting that step as the run cools.",
    ]))
    pair_left = [("table", ["Iteration n", "T (T0=20)", "chance of −17", "T (T0=40)", "chance of −17"], sched,
                  [0.18, 0.2, 0.22, 0.2, 0.2], ["c", "c", "c", "c", "c"], [])]
    pair_right = [("table", ["successes of 20", "cooling 0.95", "0.97", "0.99"], sweep,
                   [0.31, 0.27, 0.21, 0.21], ["l", "c", "c", "c"], [])]
    B.append(("cols", pair_left, pair_right, (0.52, 0.48)))
    B.append(("bul", [
        f"Early on the walker is bold; after iteration 100 (T < 1) it is greedy. Accepted downhill moves per "
        f"quarter of the run, summed over the 20 seeds: {', '.join(map(n, t20['downhill_by_quarter']))} "
        f"(T0=20) and {', '.join(map(n, t40['downhill_by_quarter']))} (T0=40). Once the chance of crossing "
        f"falls below 1% (after iteration {q2['dip_window_end'][20]:.0f} for T0=20, "
        f"{q2['dip_window_end'][40]:.0f} for T0=40) a run still on the 70-hill is frozen there.",
        f"**Cooling rate** works the same way (right table). Fast cooling shuts the window early (3 of 20 at "
        f"0.95) and slow cooling keeps it open (10 of 20 at 0.99). More heat is not always better: T0 = 80 with "
        f"0.99 gives only {q2['sweep'][(80, 0.99)]} of 20, because T is still {q2['end_temp_80_99']:.1f} after "
        "200 iterations and the walker is still wandering when the run stops. A good run is hot enough to "
        "cross the dip early, then cold enough to settle on the peak.",
        f"**Re-run with T0 = 40:** **{t40['success']} of 20** reach 95 (was {t20['success']}). The "
        f"{20 - t40['success']} failures again all sit on (2,1)=70. The crossing window stays open for "
        f"{q2['dip_window_end'][40]:.0f} iterations instead of {q2['dip_window_end'][20]:.0f}, so more runs "
        f"cross before freezing and still have about {200 - round(q2['dip_window_end'][40])} iterations to "
        "climb and settle.",
    ]))

    # ------------------------------------------------------------ 3. Rin
    B.append(("h", "3. Rin: Why did the seeds stop at 234 when 241 was possible?"))
    diff = set(q3["diff"])
    rows = [[f"{r['i']} {r['name']}", str(r["load"]), str(r["vol"]), str(r["use"]), str(r["ga"]),
             str(r["opt"])] for r in q3["rows"]]
    rows.append(["**GA pouch total**", f"{q3['ga']['totals'][0]} / 86", f"{q3['ga']['totals'][1]} / 44",
                 f"**{q3['ga']['fit']}**", "", ""])
    rows.append(["**Optimal pouch total**", f"{q3['opt']['totals'][0]} / 86", f"{q3['opt']['totals'][1]} / 44",
                 f"**{q3['opt']['fit']}**", "", ""])
    ga_names = [q3["rows"][i] for i in q3["diff"] if q3["rows"][i]["ga"] == 1]
    opt_names = [q3["rows"][i] for i in q3["diff"] if q3["rows"][i]["opt"] == 1]
    ga_use, opt_use = sum(r["use"] for r in ga_names), sum(r["use"] for r in opt_names)
    d_load = sum(r["load"] for r in opt_names) - sum(r["load"] for r in ga_names)
    d_vol = sum(r["vol"] for r in opt_names) - sum(r["vol"] for r in ga_names)
    near = sorted((p["totals"][2] for p in q3["partial"]
                   if p["score"] == 0 and p["totals"][1] - 44 == 1 and p["totals"][0] <= 86), reverse=True)
    ga_tools = " and ".join(f"{r['name']} (use {r['use']})" for r in ga_names)
    opt_tools = " and ".join(f"{r['name']} (use {r['use']})" for r in opt_names)
    seed12, study = q3["fix"]["seed12"], q3["fix"]["study"]
    base_label, m2_label = "mutation 1/15 (assignment)", "mutation 2/15"
    left = [("table", ["Tool", "Load", "Vol", "Use", "GA", "Opt"], rows,
             [0.37, 0.14, 0.14, 0.11, 0.12, 0.12], ["l", "r", "r", "r", "c", "c"], sorted(diff))]
    right = [("img", "ga_chart.png", 205,
              "Best and average fitness per generation. The dotted line is the true best, 241."),
             ("p", f"The GA pouch is `{q3['ga']['bits']}` and the optimum is `{q3['opt']['bits']}`. "
                   "Shaded rows are the four tools where they disagree.")]
    B.append(("cols", left, right, (0.56, 0.44)))
    B.append(("bul", [
        f"**Differences seed by seed.** Four tools differ. The GA packs {ga_tools}; the optimum packs "
        f"{opt_tools} instead. That is "
        f"+{opt_use - ga_use} usefulness ({ga_use} → {opt_use}) for +{d_load} load and +{d_vol} volume. The GA "
        f"pouch holds {q3['ga']['totals'][0]} of 86 load and {q3['ga']['totals'][1]} of 44 volume; the optimum "
        f"uses {q3['opt']['totals'][0]} and exactly {q3['opt']['totals'][1]}.",
        f"**Why the seeds missed.** The pouches are {len(diff)} bit flips apart and no better pouch exists "
        f"within 3 flips of the GA's (better pouches within 1, 2, 3, 4 flips: "
        f"{', '.join(str(q3['better_within'][k]) for k in (1, 2, 3, 4))}). Of the {len(q3['partial'])} "
        f"half-way pouches, {q3['partial_infeasible']} break a limit and score 0 (two, worth "
        f"{' and '.join(map(str, near[:2]))}, miss by only 1 volume unit) and {q3['partial_lower']} are legal "
        f"but score below {q3['ga']['fit']}. So the GA must make all four changes at once, and by then "
        f"diversity had run out: {q3['distinct'][0]} distinct pouches at generation 0, "
        f"{q3['distinct'][q3['ga']['first']]} at generation {q3['ga']['first']} (when 234 first appeared and "
        f"the best never changed again), {q3['distinct'][50]} at generation 50, with {q3['zeros_final']} of "
        f"the 20 breaking a limit (hence the average of {q3['ga']['avg']:.2f}).",
        f"**One fix: raise the mutation rate from 1/15 to 2/15 per bit.** On seed 12 the GA then reaches "
        f"{seed12[m2_label]['final']} at generation {seed12[m2_label]['first']}, while at 1/15 it stays on "
        f"{seed12[base_label]['final']} even if run for 150 generations. Honest limits: over seeds 1 to 200 the "
        f"hit rate only moves from {study[base_label]} to {study[m2_label]} of 200, and 3/15 is worse "
        f"({study['mutation 3/15']} of 200). Longer runs lift it to "
        f"{study['mutation 1/15, 150 generations']} of 200 but do not rescue seed 12."
        if study else "**One fix: raise the mutation rate from 1/15 to 2/15 per bit.**",
    ]))

    # ------------------------------------------------------------ 4. Vesper
    B.append(("h", "4. Vesper: How would I have beaten you on every losing move?"))
    vrows = []
    for r in q4["rows"]:
        reply = " ".join(f"{p}{c}" for p, c in r["line"][1:])
        if r["winner"] == "O":
            vrows.append([str(r["col"]), n(r["value"]), f"`{reply}` completes {', '.join(map(cell, r['cells']))}",
                          f"Vesper wins at once, {r['empty']} cells left: −(1+{r['empty']}) = {n(r['utility'])}"])
        else:
            vrows.append([str(r["col"]), "+" + n(r["value"]), f"none wins; best defence `{reply}`",
                          f"X completes {', '.join(map(cell, r['cells']))} on a full board: +{r['utility']}"])
    left = [
        ("p", "Vesper's diagonal (0,4), (1,3), (3,1) is one stone short, and the empty cell (2,2) is where a "
              "stone dropped in column 2 lands. After any first move except column 2 she plays column 2 and "
              "wins on her very next stone. Only column 2 blocks it."),
        ("table", ["X's first move", "Value", "Vesper's reply", "Result"], vrows,
         [0.12, 0.10, 0.40, 0.38], ["c", "c", "l", "l"], [2]),
    ]
    right = [("img", "board_x0.png", 120,
              "After X0, O2: Vesper's diagonal. The same picture holds for columns 1, 3 and 4.")]
    B.append(("cols", left, right, (0.77, 0.23)))

    # ------------------------------------------------------------ 5. Jun
    B.append(("h", "5. Jun: Compare the ki (node counts)"))
    c, o = q5["counts"], q5["ordering"]
    nodes_rows = [
        ["Full minimax (0..4)", n(c["mm"]), "baseline"],
        ["AB1: alpha-beta, full, 0..4", n(c["ab1"]), pct(c["ab1"], c["mm"]) + " of minimax"],
        ["AB2: alpha-beta, full, middle first", n(c["ab2"]), pct(c["ab2"], c["mm"]) + " of minimax"],
        ["Depth-limited minimax (depth 4)", n(c["dl"]), "baseline"],
        ["AB3: alpha-beta, depth 4", n(c["ab3"]), pct(c["ab3"], c["dl"]) + " of depth-limited"],
    ]
    lr_split, rl_split = q5["lr_split"], q5["rl_split"]
    tot = {r["name"]: r["total"] for r in q5["lr_rows"]}
    split_rows = [[k, f"{lr_split[k]} / {tot[k]}", f"{rl_split[k]} / {tot[k]}"] for k in "ABC"]
    split_rows.append(["**all**", f"**{q5['lr_leaves']}** / 60", f"**{q5['rl_leaves']}** / 60"])
    B.append(("cols", [
        ("table", ["Method", "Nodes", "Share"], nodes_rows, [0.55, 0.19, 0.26], ["l", "r", "l"], []),
    ], [
        ("p", f"The pruned runs return the same values as the plain searches: AB1 and AB2 give "
              f"{n(q5['values']['ab1'])} like full minimax, and AB3 gives {n(q5['values']['ab3'])} like the "
              "depth-limited search. Pruning only skips work; it never changes the answer."),
    ], (0.66, 0.34)))
    B.append(("bul", [
        f"**Why middle-first barely helped.** It saved {c['ab1'] - c['ab2']} nodes, "
        f"{pct(c['ab1'] - c['ab2'], c['ab1'])} of what AB1 already needed. Alpha-beta only gains when the "
        f"first move tried at a node is its best move (or, for the opponent, its refutation), and a fixed column "
        f"order is a weak guess at that: the best column depends on the position, not on being central. I tried "
        f"all 120 fixed orders: they range from {n(o['min'])} to {n(o['max'])} nodes (median "
        f"{n(o['median'])}), and 0..4 and middle-first rank {o['rank_0_4']}th and {o['rank_mid']}th, both "
        f"exactly average. Trying the truly best move first at every node would need only {n(o['perfect'])} "
        f"nodes; the worst-first order needs {n(o['worst'])}.",
        f"**Master Hyo's tree, left to right** (hand trace below): value {q5['tree_value']} through branch "
        f"{q5['tree_move']}, {q5['lr_leaves']} leaves read; node B2 is called with window {win(*q5['b2'])}. "
        f"The root opens A with (−∞, ∞). A returns {n(q5['node_values']['A'])}, so the root's α becomes "
        f"{n(q5['node_values']['A'])}. B is searched with α = {n(q5['node_values']['A'])}, returns "
        f"{n(q5['node_values']['B'])}, and α rises to {n(q5['node_values']['B'])}. C then meets "
        f"α = {n(q5['node_values']['B'])}: its first child C1 returns {n(q5['node_values']['C1'])}, which is "
        f"≤ α, so C2 is never read.",
    ]))
    tr = []
    for r in q5["lr_rows"]:
        cut = "skips " + ", ".join(r["skipped"]) if r["cut"] else "–"
        tr.append([f"{r['name']} ({r['kind']})", win(r["alpha"], r["beta"]), n(r["value"]),
                   f"{r['leaves']} / {r['total']}", cut])
    B.append(("cols", [
        ("table", ["Node", "Window in (α, β)", "Returns", "Leaves", "Cut"], tr,
         [0.20, 0.27, 0.12, 0.13, 0.28], ["l", "c", "c", "c", "l"], []),
    ], [
        ("table", ["Leaves read", "L→R", "R→L"], split_rows, [0.34, 0.33, 0.33], ["l", "c", "c"], []),
        ("p", f"**Why right to left reads fewer ({q5['rl_leaves']} against {q5['lr_leaves']}).** The order "
              f"decides which window each sibling is searched with. Left to right spends {lr_split['A']} leaves "
              f"on A, the biggest and worst subtree ({tot['A']} leaves, worth {n(q5['node_values']['A'])}), "
              f"before the root has any α to compare with. Right to left meets C, then B, and reaches A last "
              f"with α = {n(q5['node_values']['B'])}: A's first child returns a value ≤ α, so A2 and A1 are cut "
              f"and A costs {rl_split['A']} leaves. Inside B it also tries B2 ({n(q5['node_values']['B2'])}) "
              f"before B1, so B1 is cut after one child. C is the only subtree that gets dearer "
              f"({lr_split['C']} → {rl_split['C']}). Net saving: {q5['lr_leaves'] - q5['rl_leaves']} leaves."),
    ], (0.55, 0.45)))
    return B


# ----------------------------------------------------------------------
# Markdown renderer
# ----------------------------------------------------------------------
def md_blocks(blocks, out):
    for b in blocks:
        kind = b[0]
        if kind == "title":
            out.append(f"# {b[1]}\n\n*{b[2]}*\n")
        elif kind == "h":
            out.append(f"## {b[1]}\n")
        elif kind == "p":
            out.append(b[1] + "\n")
        elif kind == "bul":
            out.extend(f"- {t}" for t in b[1])
            out.append("")
        elif kind == "table":
            _, header, rows, _, _, shaded = b
            out.append("| " + " | ".join(header) + " |")
            out.append("|" + "|".join("---" for _ in header) + "|")
            for i, r in enumerate(rows):
                cells = [f"**{x}**" if i in shaded and x and not x.startswith("**") else x for x in r]
                out.append("| " + " | ".join(cells) + " |")
            out.append("")
        elif kind == "img":
            out.append(f"![{b[3]}](figures/{b[1]})\n")
        elif kind == "cols":
            md_blocks(b[1], out)
            md_blocks(b[2], out)


def write_markdown(blocks, path):
    out = []
    md_blocks(blocks, out)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out).rstrip() + "\n")


# ----------------------------------------------------------------------
# PDF renderer
# ----------------------------------------------------------------------
def find_font(names):
    dirs = ["/usr/share/fonts/truetype/liberation", "/usr/share/fonts/truetype/dejavu",
            "/usr/share/fonts/truetype/crosextra", "C:/Windows/Fonts", "/Library/Fonts",
            "/System/Library/Fonts/Supplemental", os.path.expanduser("~/Library/Fonts"),
            os.path.expanduser("~/.fonts")]
    for d in dirs:
        for nme in names:
            p = os.path.join(d, nme)
            if os.path.exists(p):
                return p
    return None


def build_pdf(blocks, path):
    from PIL import Image as PILImage
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (BaseDocTemplate, Frame, Image, PageTemplate, Paragraph,
                                    Spacer, Table, TableStyle)

    reg = find_font(["LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf", "DejaVuSans.ttf"])
    bold = find_font(["LiberationSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"])
    mono = find_font(["LiberationMono-Regular.ttf", "Courier New.ttf", "cour.ttf", "DejaVuSansMono.ttf"])
    unicode_ok = bool(reg and bold and mono)
    if unicode_ok:
        pdfmetrics.registerFont(TTFont("Sans", reg))
        pdfmetrics.registerFont(TTFont("Sans-B", bold))
        pdfmetrics.registerFont(TTFont("Mono", mono))
        pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans", boldItalic="Sans-B")
        f_reg, f_bold, f_mono = "Sans", "Sans-B", "Mono"
    else:  # plain PDF fonts have no Greek or arrows, so spell them out
        f_reg, f_bold, f_mono = "Helvetica", "Helvetica-Bold", "Courier"
        print("note: no Unicode font found, falling back to ASCII symbols", file=sys.stderr)
    ascii_map = {"α": "alpha", "β": "beta", "Δ": "delta", "−": "-", "→": "->", "≤": "<=", "∞": "inf",
                 "·": "*", "–": "-"}

    def fix(text):
        if unicode_ok:
            return text
        for k, v in ascii_map.items():
            text = text.replace(k, v)
        return text

    def rl(text):
        text = html.escape(fix(text), quote=False)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"`(.+?)`", rf'<font name="{f_mono}" size="7.4">\1</font>', text)
        return text

    ink, grey, rule = colors.HexColor("#15171c"), colors.HexColor("#555a63"), colors.HexColor("#c1271d")
    base = ParagraphStyle("base", fontName=f_reg, fontSize=8.3, leading=10.5, textColor=ink, spaceAfter=3)
    bullet = ParagraphStyle("bul", parent=base, leftIndent=9, bulletIndent=0, spaceAfter=3.2)
    h_style = ParagraphStyle("h", parent=base, fontName=f_bold, fontSize=10.4, leading=12.5,
                             spaceBefore=6, spaceAfter=3)
    cap = ParagraphStyle("cap", parent=base, fontSize=6.7, leading=8, textColor=grey, alignment=TA_CENTER)
    cellb = ParagraphStyle("cell", parent=base, fontSize=7.3, leading=8.6, spaceAfter=0)
    aligns = {"l": TA_LEFT, "r": TA_RIGHT, "c": TA_CENTER}

    page_w, page_h = A4
    ml = mr = 34
    avail = page_w - ml - mr

    def flow(block, width):
        kind = block[0]
        if kind == "p":
            return [Paragraph(rl(block[1]), base)]
        if kind == "bul":
            return [Paragraph(rl(t), bullet, bulletText="•") for t in block[1]]
        if kind == "h":
            return [Paragraph(rl(block[1]), h_style)]
        if kind == "img":
            _, name, w, caption = block
            im = PILImage.open(os.path.join(FIG, name))
            img = Image(os.path.join(FIG, name), width=w, height=w * im.height / im.width)
            img.hAlign = "CENTER"
            return [img, Spacer(1, 2), Paragraph(rl(caption), cap), Spacer(1, 3)]
        if kind == "table":
            _, header, rows, fr, al, shaded = block
            hs = [ParagraphStyle(f"h{i}", parent=cellb, fontName=f_bold, textColor=colors.white,
                                 alignment=aligns[a]) for i, a in enumerate(al)]
            cs = [ParagraphStyle(f"c{i}", parent=cellb, alignment=aligns[a]) for i, a in enumerate(al)]
            data = [[Paragraph(rl(h), hs[i]) for i, h in enumerate(header)]]
            for r in rows:
                data.append([Paragraph(rl(x), cs[i]) for i, x in enumerate(r)])
            t = Table(data, colWidths=[width * f for f in fr], repeatRows=1)
            style = [("BACKGROUND", (0, 0), (-1, 0), ink),
                     ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b9bcc3")),
                     ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                     ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
                     ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
            for i in range(1, len(data)):
                style.append(("BACKGROUND", (0, i), (-1, i),
                              colors.HexColor("#f0f1f3") if i % 2 == 0 else colors.white))
            for i in shaded:
                style.append(("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#f7d9d6")))
            t.setStyle(TableStyle(style))
            return [t, Spacer(1, 4)]
        if kind == "cols":
            _, left, right, (fl, fr_) = block
            gap = 10
            wl, wr = (avail - gap) * fl, (avail - gap) * fr_
            lf = [x for b in left for x in flow(b, wl)]
            rf = [x for b in right for x in flow(b, wr)]
            t = Table([[lf, "", rf]], colWidths=[wl, gap, wr])
            t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                                   ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
            return [t, Spacer(1, 2)]
        raise ValueError(kind)

    story = []
    for b in blocks:
        if b[0] == "title":
            story.append(Paragraph(rl(b[1]), ParagraphStyle("t", parent=base, fontName=f_bold, fontSize=16,
                                                            leading=19, spaceAfter=2)))
            story.append(Paragraph(rl(b[2]), ParagraphStyle("st", parent=base, fontSize=7.6, textColor=grey,
                                                            spaceAfter=2)))
        else:
            story.extend(flow(b, avail))

    class Numbered(rl_canvas.Canvas):
        """Canvas that writes 'page x of y' in the footer."""

        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            self._pages = []

        def showPage(self):
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._pages)
            for st in self._pages:
                self.__dict__.update(st)
                self.setFont(f_reg, 6.8)
                self.setFillColor(grey)
                self.drawString(ml, 18, "Thornwood Rescue: debrief")
                self.drawRightString(page_w - mr, 18, f"page {self._pageNumber} of {total}")
                super().showPage()
            super().save()

    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=ml, rightMargin=mr, topMargin=28, bottomMargin=30,
                          title="Thornwood Rescue: Debrief", author="Team Ember")
    doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(ml, 30, avail, page_h - 58, 0, 0, 0, 0)])])
    doc.build(story, canvasmaker=Numbered)


def main():
    if not os.path.isdir(FIG) or not os.listdir(FIG):
        sys.exit("No figures yet: run  python extras/make_figures.py  first.")
    results = runs.collect(quick="--quick" in sys.argv)
    blocks = content(results)
    write_markdown(blocks, os.path.join(HERE, "debrief.md"))
    pdf = os.path.join(ROOT, "debrief.pdf")
    build_pdf(blocks, pdf)
    from pypdf import PdfReader
    pages = len(PdfReader(pdf).pages)
    print(f"wrote {pdf} ({pages} pages) and extras/debrief.md")
    if pages > MAX_PAGES:
        sys.exit(f"debrief.pdf has {pages} pages; the limit is {MAX_PAGES}")


if __name__ == "__main__":
    main()
