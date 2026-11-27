"""Exact keno arithmetic: every draw pattern of a mode, its weight and its win.

A pattern is the draw in order, one symbol per ball: MISS, HIT (a number the player picked) or
KILAU (a marked number the player did not pick). A round is a pattern together with the number
of Kilau numbers its board marks: a level with Kilau rounds has rounds that mark 1 and rounds
that mark 3.
"""

from itertools import combinations
from math import perm

try:
    from src.executables.executables import Executables
except ImportError:  # design_tables.py runs without the SDK on the path
    Executables = object

MISS, HIT, KILAU = 0, 1, 2


def all_patterns(picks: int, draws: int, kilau: int) -> list:
    """Every ordered pattern with at most `picks` hits and `kilau` marked balls, fewest hits first."""
    patterns = []
    for hits in range(min(picks, draws) + 1):
        for hit_positions in combinations(range(draws), hits):
            hit_at = set(hit_positions)
            rest = [i for i in range(draws) if i not in hit_at]
            for marked in range(min(kilau, len(rest)) + 1):
                for kilau_positions in combinations(rest, marked):
                    kilau_at = set(kilau_positions)
                    patterns.append(
                        [HIT if i in hit_at else KILAU if i in kilau_at else MISS for i in range(draws)]
                    )
    return patterns


def pattern_weight(pattern: list, picks: int, kilau: int, board: int) -> int:
    """Number of ordered draws from `board` numbers that give this pattern."""
    hits = pattern.count(HIT)
    marked = pattern.count(KILAU)
    misses = len(pattern) - hits - marked
    return perm(picks, hits) * perm(kilau, marked) * perm(board - picks - kilau, misses)


def mode_rounds(picks: int, draws: int, kilau_options: list, board: int) -> list:
    """Every round of a mode: (pattern, Kilau numbers marked, weight).

    The weight is the number of ordered draws that give the pattern, times the share of rounds
    that mark that many Kilau numbers. Every Kilau count has the same number of ordered draws
    in all, so the shares are the real shares.
    """
    rounds = []
    for kilau, share in kilau_options:
        for pattern in all_patterns(picks, draws, kilau):
            rounds.append((pattern, kilau, share * pattern_weight(pattern, picks, kilau, board)))
    return rounds


def best_run(pattern: list, soft: bool) -> int:
    """Highest run of hits. A miss ends the run (soft: lowers it by one); a Kilau ball leaves it."""
    best = run = 0
    for ball in pattern:
        if ball == HIT:
            run += 1
        elif ball == MISS:
            run = max(0, run - 1) if soft else 0
        best = max(best, run)
    return best


def meter_level(pattern: list, soft: bool) -> int:
    """Best run plus one step for every Kilau ball drawn."""
    return best_run(pattern, soft) + pattern.count(KILAU)


class GameCalculations(Executables):
    """Win of one draw pattern."""

    def evaluate_pattern(self, pattern: list, picks: int, level: str) -> dict:
        hits = pattern.count(HIT)
        soft = level in self.config.soft_levels
        streak = best_run(pattern, soft)
        kilau = pattern.count(KILAU)
        # a round with no hit has nothing to multiply: its meter stays empty
        step = streak + kilau if hits else 0
        multiplier = self.config.streak_multiplier[min(step, self.config.top_streak)]
        pay = self.config.pay_tables[level][picks][hits]
        return {
            "hits": hits,
            "streak": streak,
            "kilau": kilau,
            "multiplier": multiplier,
            "pay": pay,
            "win": round(pay * multiplier, 2),
        }
