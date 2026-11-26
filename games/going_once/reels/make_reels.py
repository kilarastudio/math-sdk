"""Generate the Going Once reel strip from exact symbol counts.

Run from anywhere:  python games/going_once/reels/make_reels.py

Exact stop counts and a fixed seed: a change here is one known change. Lots (P) may stack up
to three high, like the stacks hold & win players expect; other symbols never repeat more than
twice in a row.
"""

import os
import random

PAYING = {"H1": 6, "H2": 7, "H3": 8, "H4": 9, "L1": 12, "L2": 13, "L3": 14, "L4": 15}
REELS = [
    {"P": 12},
    {"P": 13, "W": 3},
    {"P": 12, "W": 3, "G": 2},
    {"P": 13, "W": 3},
    {"P": 12},
]
SEED = 5


def ok(strip):
    n = len(strip)
    for i in range(n):
        run = [strip[(i + k) % n] for k in range(4)]
        if len(set(run)) == 1:
            return False
        if run[0] != "P" and run[0] == run[1] == run[2]:
            return False
    return True


def main():
    rng = random.Random(SEED)
    length = sum(PAYING.values()) + max(sum(r.values()) for r in REELS)
    reels = []
    for extra in REELS:
        stops = [s for s, n in PAYING.items() for _ in range(n)] + [s for s, n in extra.items() for _ in range(n)]
        stops += ["L4"] * (length - len(stops))
        for _ in range(10000):
            rng.shuffle(stops)
            if ok(stops):
                break
        else:
            raise RuntimeError("no strip")
        reels.append(list(stops))
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "BR0.csv"), "w", encoding="UTF-8") as f:
        for i in range(length):
            f.write(",".join(r[i] for r in reels) + "\n")
    print("BR0", length)


if __name__ == "__main__":
    main()
