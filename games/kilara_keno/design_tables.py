"""Design tool: find tidy pay tables that land every mode inside the RTP window.

    python3 games/kilara_keno/design_tables.py

RTP is linear in the pay table: RTP x cost = sum over hits of pay[h] x A[h], where
A[h] = P(hits = h) x E[multiplier | h]. So the search only tries round numbers near a draft
and keeps the roundest table whose RTP is inside the window. Paste the result into
game_config.py; nothing here is read at run time.
"""

import os
import sys
from itertools import product
from math import comb

sys.path.insert(0, os.path.dirname(__file__))
from game_calculations import all_patterns, pattern_weight, meter_level  # noqa: E402

BOARD = 40
DRAWS = {"low": 10, "high": 10, "chain": 12, "chainmax": 12}
COST = {"low": 1, "high": 1, "chain": 10, "chainmax": 100}
KILAU = {"low": 1, "high": 1, "chain": 1, "chainmax": 3}
SOFT = {"chain", "chainmax"}
MULT = {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15, 7: 25}
TOP = 7
WINDOW = (0.9650, 0.9670)
AIM = 0.9662

DRAFT = {
    ("low", 2): [0, 1, 4], ("low", 3): [0, 1.2, 1.5, 9.9], ("low", 4): [0, 0.5, 1.5, 4, 20],
    ("low", 5): [0, 0.4, 1.2, 1.5, 7.5, 50], ("low", 6): [0, 0, 1, 1.5, 4, 12, 50],
    ("low", 7): [0, 0, 0.6, 1.2, 2.5, 6, 15, 50], ("low", 8): [0, 0, 0.5, 0.8, 1.5, 5, 7.5, 15, 20],
    ("low", 9): [0, 0, 0.3, 0.8, 1.2, 3, 6, 10, 20, 20], ("low", 10): [0, 0, 0, 0.5, 1, 2, 5, 7.5, 12, 20, 20],
    ("high", 2): [0, 0.3, 10], ("high", 3): [0, 0, 1.5, 37.1], ("high", 4): [0, 0, 1, 8, 80],
    ("high", 5): [0, 0, 0.5, 2.2, 12, 250], ("high", 6): [0, 0, 0.3, 1.5, 8, 60, 500],
    ("high", 7): [0, 0, 0, 1, 4, 25, 200, 1000], ("high", 8): [0, 0, 0, 0.3, 1.5, 5, 50, 500, 2000],
    ("high", 9): [0, 0, 0, 0.3, 1, 3, 20, 150, 1500, 1500],
    ("high", 10): [0, 0, 0, 0, 0.6, 1.5, 6, 60, 600, 2000, 2000],
    ("chain", 10): [0, 0, 2, 3, 5, 5, 10, 25, 500, 2000, 2000],
    ("chainmax", 10): [0, 0, 10, 30, 40, 50, 100, 400, 1500, 4000, 4000],
}
# Entries kept as drafted (the top of each table is a design decision, not a tuning knob).
FIXED = {("low", 8): [8], ("low", 9): [8, 9], ("low", 10): [9, 10], ("high", 6): [6], ("high", 7): [7],
         ("high", 8): [8], ("high", 9): [8, 9], ("high", 10): [9, 10], ("chain", 10): [2, 3, 4, 5, 6, 7, 8, 9, 10],
         ("chainmax", 10): [9, 10]}


def mode_table(level: str, picks: int) -> dict:
    """{(hits, multiplier): probability} of a mode."""
    draws = DRAWS[level]
    total = 0
    out = {}
    for pattern in all_patterns(picks, draws, KILAU[level]):
        w = pattern_weight(pattern, picks, KILAU[level], BOARD)
        key = (pattern.count(1), MULT[min(meter_level(pattern, level in SOFT), TOP)])
        out[key] = out.get(key, 0) + w
        total += w
    return {k: v / total for k, v in out.items()}


def roundness(x: float) -> int:
    """0 = one significant figure or a familiar step, 1 = two figures, 2 = three."""
    if x == 0:
        return 0
    mant = x
    while mant >= 10:
        mant /= 10
    while mant < 1:
        mant *= 10
    mant = round(mant, 6)
    if mant in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 7.5, 8):
        return 0
    if round(mant * 10) == round(mant * 10, 6):
        return 1
    return 2


def candidates(d: float, fine: bool = False) -> list:
    lo, hi = d * 0.72, d * 1.35
    step = 0.1 if d < 10 or fine else 0.5 if d < 30 else 1 if d < 100 else 5 if d < 400 else 50
    vals, v = [], round(lo / step) * step
    while v <= hi + 1e-9:
        v = round(v, 1)
        if v > 0:
            vals.append(v)
        v += step
    vals.sort(key=lambda x: (roundness(x), abs(x - d)))
    return vals[:40 if fine else 9]


def solve(level: str, picks: int):
    table = mode_table(level, picks)
    A = [0.0] * (picks + 1)
    for (h, m), p in table.items():
        A[h] += p * m
    draft = DRAFT[(level, picks)][:]
    fixed = set(FIXED.get((level, picks), []))
    free = [h for h in range(picks + 1) if draft[h] > 0 and h not in fixed]
    base = sum(draft[h] * A[h] for h in range(picks + 1) if h not in free)
    cost = COST[level]
    # Bring the draft to the aim first, so the search looks at round numbers near a valid table.
    scale = (AIM * cost - base) / sum(draft[h] * A[h] for h in free)
    for h in free:
        draft[h] = draft[h] * scale
    best = None
    fine = len(free) <= 3
    for combo in product(*[candidates(draft[h], fine) for h in free]):
        rtp = (base + sum(v * A[h] for v, h in zip(combo, free))) / cost
        if not WINDOW[0] <= rtp < WINDOW[1]:
            continue
        pay = draft[:]
        for v, h in zip(combo, free):
            pay[h] = v
        nz = [x for x in pay[1:] if x > 0]
        if any(b < a for a, b in zip(nz, nz[1:])):
            continue
        score = (sum(roundness(v) for v in combo), sum(abs(v - draft[h]) / draft[h] for v, h in zip(combo, free)))
        if best is None or score < best[0]:
            best = (score, pay, rtp)
    return best, table


def describe(level, picks, pay, table):
    cost = COST[level]
    wins = {}
    for (h, m), p in table.items():
        w = round(pay[h] * m, 2)
        wins[w] = wins.get(w, 0) + p
    rtp = sum(w * p for w, p in wins.items()) / cost
    std = sum(p * (w / cost - rtp) ** 2 for w, p in wins.items()) ** 0.5
    hit = sum(p for w, p in wins.items() if w > 0)
    back = sum(p for w, p in wins.items() if w >= cost)
    top = max(wins)
    return (f"rtp={100 * rtp:.3f}% std={std:5.2f} hit={100 * hit:4.1f}% back={100 * back:4.1f}% "
            f"max={top:g} (1 in {1 / wins[top]:,.0f}) distinct={len(wins)}")


if __name__ == "__main__":
    only = sys.argv[1:]
    for (level, picks) in DRAFT:
        if only and f"{level}_{picks}" not in only:
            continue
        best, table = solve(level, picks)
        if best is None:
            print(f"{level}_{picks}: no tidy table in the window; widen the candidates")
            continue
        (rough, _), pay, _ = best
        print(f"{level}_{picks:<2d} rough={rough} {pay}\n         {describe(level, picks, pay, table)}")
