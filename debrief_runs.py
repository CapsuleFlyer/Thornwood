"""Extra experiments for the debrief (NOT part of the Owl Cipher submission).

Import functions from thornwood.py and run the extra analyses the five
Chapter 5 questions ask for. Keep thornwood.py itself clean.

Run from the repo root:  python -m extras.debrief_runs
(or: python extras/debrief_runs.py after adding the repo root to sys.path)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import thornwood  # noqa: E402,F401


def q1_kaito_local_maximum():
    """Kaito: show the exact cell where hill climbing from (0,0) got stuck and
    all of its neighbours."""
    # TODO
    pass


def q2_gennai_temperature():
    """Gennai: explain how starting heat and cooling rate decide success.
    Re-run the 20 seeds with T0 = 40 and compare the success count."""
    # TODO
    pass


def q3_rin_ga_vs_optimum():
    """Rin: compare GA best (234) and the true optimum seed by seed, and
    propose one fix (e.g. higher mutation, bigger tournament, repair)."""
    # TODO
    pass


def q4_vesper_losing_moves():
    """Vesper: for each root move that would have lost, show how X still wins
    (principal variation / best reply)."""
    # TODO
    pass


def q5_jun_node_counts():
    """Jun: compare node counts of every method; explain why middle-first
    barely helped, and why right-to-left read fewer leaves in the tree."""
    # TODO
    pass


if __name__ == "__main__":
    q1_kaito_local_maximum()
    q2_gennai_temperature()
    q3_rin_ga_vs_optimum()
    q4_vesper_losing_moves()
    q5_jun_node_counts()
