"""Generate the Dwanda reel strips from symbol counts.

Run from anywhere:  python games/dwanda/reels/make_reels.py

A cluster game's hit rate depends on how often a reel shows the same symbol twice in a row, and a
plain shuffle leaves that to chance (one reshuffle moved the base game by several percent of RTP).
So a strip is built from runs: each symbol's stops are split into runs of 1 to 4 in fixed
numbers ("clump" sets how stacked they are), the runs are ordered so that two runs of one symbol
never touch, and scatters go between runs, at least a board's height apart, so a reel never shows
more than one at the reveal (cascades can still bring a second one down). Every reel of a strip
holds the same stops; only the order and the scatters differ. The seed is fixed, so a change here
is one known change and gives the same strip on every run.
"""

import os
import random

ROWS = 7
STRIPS = {
    # name: (symbol stops per reel, clump, scatters on each of the seven reels, seed)
    "BR0": ({"P1": 14, "D1": 14, "P2": 20, "D2": 20, "P3": 28, "D3": 28, "P4": 36, "D4": 36}, 1.35, [2, 2, 1, 1, 1, 1, 1], 7),
    "FR0": ({"P1": 14, "D1": 14, "P2": 20, "D2": 20, "P3": 28, "D3": 28, "P4": 36, "D4": 36}, 2.0, [3, 3, 3, 3, 2, 2, 2], 11),
}


def make_runs(counts: dict, clump: float) -> list:
    """Split each symbol's stops into runs of 1 to 4, as a shuffle would on average.

    A symbol holding the share p of a reel sits in runs of length k on k * q^(k-1) * (1-q)^2 of
    its stops, with q = clump * p. clump = 1 is what a plain shuffle gives on average; a higher
    value stacks the symbols more, which raises the hit rate.
    """
    total = sum(counts.values())
    runs = []
    for symbol, n in counts.items():
        q = min(clump * n / total, 0.6)
        left = n
        for k in (4, 3, 2):
            for _ in range(round(n * q ** (k - 1) * (1 - q) ** 2)):
                if left >= k:
                    runs.append([symbol] * k)
                    left -= k
        runs += [[symbol]] * left
    return runs


def order_runs(runs: list, rng: random.Random) -> list:
    """Shuffle the runs, then move runs until no two of one symbol touch (the strip wraps round)."""
    runs = list(runs)
    rng.shuffle(runs)
    n = len(runs)
    for _ in range(100):
        clean = True
        for i in range(n):
            if runs[i][0] != runs[i - 1][0]:
                continue
            clean = False
            candidates = [
                j
                for j in range(n)
                if runs[j][0] != runs[i - 1][0]
                and runs[j][0] != runs[(i + 1) % n][0]
                and runs[i][0] != runs[j - 1][0]
                and runs[i][0] != runs[(j + 1) % n][0]
                and abs(i - j) > 1
                and abs(i - j) < n - 1
            ]
            j = rng.choice(candidates)
            runs[i], runs[j] = runs[j], runs[i]
        if clean:
            return runs
    raise RuntimeError("could not separate the runs")


def make_reel(counts: dict, clump: float, n_scatter: int, rng: random.Random) -> list:
    runs = order_runs(make_runs(counts, clump), rng)
    # Scatter slots: run boundaries at least ROWS stops apart, the wrap-around included.
    starts, stop = [], 0
    for run in runs:
        starts.append(stop)
        stop += len(run)
    length = stop
    while True:
        chosen = sorted(rng.sample(range(len(runs)), n_scatter))
        stops = [starts[i] for i in chosen]
        gaps = [(b - a) % length for a, b in zip(stops, stops[1:] + stops[:1])]
        if n_scatter == 1 or min(gaps) >= ROWS:
            break
    reel = []
    for i, run in enumerate(runs):
        if i in chosen:
            reel.append("S")
        reel += run
    return reel


def make_strip(counts: dict, clump: float, scatters: list, seed: int) -> list:
    rng = random.Random(seed)
    reels = [make_reel(counts, clump, n, rng) for n in scatters]
    # The SDK reads a strip as a table, so every reel must be as long as the longest: a reel
    # with fewer scatters gets its first symbols again at the end.
    length = max(len(reel) for reel in reels)
    return [reel + reel[: length - len(reel)] for reel in reels]


def write_strips(names=None) -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    for name, (counts, clump, scatters, seed) in STRIPS.items():
        if names and name not in names:
            continue
        reels = make_strip(counts, clump, scatters, seed)
        with open(os.path.join(here, f"{name}.csv"), "w", encoding="UTF-8") as f:
            for stop in range(len(reels[0])):
                f.write(",".join(reel[stop] for reel in reels) + "\n")
        same = sum(1 for reel in reels for i in range(len(reel)) if reel[i] == reel[i - 1] and reel[i] != "S")
        print(f"wrote {name}.csv: {len(reels[0])} stops, same symbol twice in a row on {same / (7 * len(reels[0])):.1%} of stops")


if __name__ == "__main__":
    write_strips()
