"""Design tool: find tidy pay tables that land every mode inside the RTP window.

    python3 games/keno_chain/design_tables.py [--share 43/200] [mode ...]

--share tries another share of Kilau rounds (rounds of Calm, Bold, Wild and Chain that mark 3 Kilau
numbers instead of 1) than the one in use. --list N prints the N tidiest tables of each mode.
--check prints the tables in use as they are, without searching.

RTP is linear in the pay table: RTP x cost = sum over hits of pay[h] x A[h], where
A[h] = P(hits = h) x E[multiplier | h]. So the search only tries round numbers near a draft
and keeps the roundest table whose RTP is inside the window. Paste the result into
game_config.py; nothing here is read at run time.
"""

import os
import sys
from fractions import Fraction
from itertools import product

sys.path.insert(0, os.path.dirname(__file__))
from game_calculations import all_patterns, pattern_weight, meter_level  # noqa: E402

BOARD = 40
DRAWS = {"calm": 10, "bold": 10, "wild": 10, "chain": 12, "chainmax": 12}
COST = {"calm": 1, "bold": 1, "wild": 1, "chain": 10, "chainmax": 100}
KILAU = {"calm": 1, "bold": 1, "wild": 1, "chain": 1, "chainmax": 3}
# Kilau round: a share of the rounds of these levels marks 3 Kilau numbers instead of 1.
KILAU_ROUND_LEVELS = {"calm", "bold", "wild", "chain"}
KILAU_ROUND_NUMBERS = 3
KILAU_ROUND_SHARE = Fraction(1, 5)
SOFT = {"chain", "chainmax"}
MULT = {0: 1, 1: 1, 2: 2, 3: 3, 4: 5, 5: 10, 6: 15, 7: 25}
TOP = 7
WINDOW = (0.9650, 0.9670)
AIM = 0.9662

# The tables in use (math v2). In every level the volatility and the top win rise with the
# numbers played, and at every size Calm < Bold < Wild. Bold pays from the same number of hits as
# Wild, flatter.
# The search looks at round numbers near these.
DRAFT = {
    ("calm", 3): [0, 0.8, 1.5, 7.8], ("calm", 4): [0, 0.3, 1.5, 2.5, 18], ("calm", 5): [0, 0.3, 1, 1.2, 6, 30],
    ("calm", 6): [0, 0, 0.8, 1.3, 2.5, 12, 50], ("calm", 8): [0, 0, 0.2, 1, 1.3, 2, 10, 40, 60],
    ("calm", 10): [0, 0, 0, 0.5, 0.6, 1.5, 5, 10, 20, 100, 100],
    ("bold", 3): [0, 0, 2.8, 16.5], ("bold", 4): [0, 0, 1, 5.5, 38], ("bold", 5): [0, 0, 0.6, 2.2, 11, 80],
    ("bold", 6): [0, 0, 0.5, 1.2, 4, 20, 160], ("bold", 8): [0, 0, 0, 0.5, 1.5, 6.5, 20, 100, 300],
    ("bold", 10): [0, 0, 0, 0, 1, 1.5, 6, 25, 120, 400, 400],
    ("wild", 3): [0, 0, 1, 32.5], ("wild", 4): [0, 0, 0.6, 2.5, 100], ("wild", 5): [0, 0, 0.3, 2, 8.4, 250],
    ("wild", 6): [0, 0, 0.2, 0.8, 6, 25, 500], ("wild", 8): [0, 0, 0, 0.3, 1.2, 4.4, 40, 400, 2000],
    ("wild", 10): [0, 0, 0, 0, 0.5, 1.2, 5, 50, 600, 2000, 2000],
    ("chain", 10): [0, 0, 1.2, 2.5, 5, 5, 10, 20, 500, 2000, 2000],
    ("chainmax", 10): [0, 0, 0, 20, 40, 40, 120, 300, 2500, 4000, 4000],
}
# Entries kept as drafted (the top of each table is a design decision, not a tuning knob).
FIXED = {("calm", 8): [8], ("calm", 10): [9, 10], ("bold", 5): [5], ("bold", 6): [6], ("bold", 8): [8],
         ("bold", 10): [9, 10], ("wild", 6): [6], ("wild", 8): [8], ("wild", 10): [9, 10],
         ("chain", 10): [8, 9, 10], ("chainmax", 10): [9, 10]}

def kilau_options(level: str) -> list:
    """[(Kilau numbers marked, share of the rounds)] of a level."""
    if level not in KILAU_ROUND_LEVELS or not KILAU_ROUND_SHARE:
        return [(KILAU[level], Fraction(1))]
    return [(KILAU[level], 1 - KILAU_ROUND_SHARE), (KILAU_ROUND_NUMBERS, KILAU_ROUND_SHARE)]


def mode_table(level: str, picks: int) -> dict:
    """{(hits, multiplier): probability} of a mode."""
    draws = DRAWS[level]
    out = {}
    for kilau, share in kilau_options(level):
        total = 0
        part = {}
        for pattern in all_patterns(picks, draws, kilau):
            w = pattern_weight(pattern, picks, kilau, BOARD)
            hits = pattern.count(1)
            # a round with no hit has nothing to multiply
            step = meter_level(pattern, level in SOFT) if hits else 0
            key = (hits, MULT[min(step, TOP)])
            part[key] = part.get(key, 0) + w
            total += w
        for key, w in part.items():
            out[key] = out.get(key, 0) + float(share) * w / total
    return out


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


def solve(level: str, picks: int, keep: int = 1):
    """The `keep` tidiest tables of a mode inside its window, best first, and the mode's table."""
    table = mode_table(level, picks)
    A = [0.0] * (picks + 1)
    for (h, m), p in table.items():
        A[h] += p * m
    original = DRAFT[(level, picks)]
    draft = original[:]
    fixed = set(FIXED.get((level, picks), []))
    free = [h for h in range(picks + 1) if draft[h] > 0 and h not in fixed]
    base = sum(draft[h] * A[h] for h in range(picks + 1) if h not in free)
    cost = COST[level]
    if not free:
        return [((0, 0), draft, base / cost)], table
    # Bring the draft to the aim first, so the search looks at round numbers near a valid table.
    scale = (AIM * cost - base) / sum(draft[h] * A[h] for h in free)
    for h in free:
        draft[h] = draft[h] * scale
    found = []
    fine = len(free) <= 3
    for combo in product(*[candidates(draft[h], fine) for h in free]):
        rtp = (base + sum(v * A[h] for v, h in zip(combo, free))) / cost
        if not WINDOW[0] <= rtp < WINDOW[1]:
            continue
        pay = draft[:]
        for v, h in zip(combo, free):
            pay[h] = v
        # more hits never pay less, and pay more wherever the draft did
        steps = [(h, h + 1) for h in range(1, picks) if pay[h] > 0]
        if any(pay[b] < pay[a] or (pay[b] == pay[a] and original[b] > original[a]) for a, b in steps):
            continue
        score = (sum(roundness(v) for v in combo), sum(abs(v - draft[h]) / draft[h] for v, h in zip(combo, free)))
        found.append((score, pay, rtp))
    found.sort(key=lambda f: f[0])
    return found[:keep], table


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
    keep = 1
    if "--share" in only:
        at = only.index("--share")
        KILAU_ROUND_SHARE = Fraction(only[at + 1])
        del only[at:at + 2]
    if "--list" in only:
        at = only.index("--list")
        keep = int(only[at + 1])
        del only[at:at + 2]
    check = "--check" in only
    if check:
        only.remove("--check")
    print(f"Kilau rounds: {float(KILAU_ROUND_SHARE):.2%} of the rounds of {sorted(KILAU_ROUND_LEVELS)}")
    for (level, picks) in DRAFT:
        if only and f"{level}_{picks}" not in only:
            continue
        if check:
            table = mode_table(level, picks)
            print(f"{level}_{picks:<2d} {DRAFT[(level, picks)]}\n         {describe(level, picks, DRAFT[(level, picks)], table)}")
            continue
        found, table = solve(level, picks, keep)
        if not found:
            print(f"{level}_{picks}: no tidy table in the window; widen the candidates")
            continue
        for (rough, _), pay, _ in found:
            print(f"{level}_{picks:<2d} rough={rough} {pay}\n         {describe(level, picks, pay, table)}")
