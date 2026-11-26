"""Generate The Vault Job reel strips from exact symbol counts.

Run from anywhere:  python games/vault_job/reels/make_reels.py

Every strip is built from exact stop counts with a fixed seed, so a change here is one known
change and gives the same strip on every run. Special symbols (crew and scatters) are spread
along the strip, at least a board's height apart from another special, so one reel never shows
two of them at once; the paying symbols fill the gaps in a seeded shuffle that never puts the same
symbol on more than `MAX_RUN` stops in a row.
"""

import os
import random

ROWS = 4
MAX_RUN = 2
SPECIALS = ("S", "WD", "WC", "WM", "WH")

PAYING = {"H1": 6, "H2": 8, "H3": 10, "H4": 12, "L1": 15, "L2": 16, "L3": 17, "L4": 18}
STRIPS = {
    # name: per reel {special: stops}, paying stops per reel, seed
    "BR0": (
        [
            {"S": 2},
            {"S": 2, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
            {"S": 2, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
            {"S": 2, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
            {"S": 2, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
        ],
        PAYING,
        7,
    ),
    "FR0": (
        [
            {"S": 1},
            {"S": 1, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
            {"S": 1, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
            {"S": 1, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
            {"S": 1, "WD": 1, "WC": 1, "WM": 1, "WH": 1},
        ],
        {sym: 2 * n for sym, n in PAYING.items()},
        11,
    ),
}


def build_reel(specials: dict, paying: dict, rng: random.Random, length: int) -> list:
    """One reel of `length` stops; stops the specials leave free beyond `paying` go to L4."""
    fill = [sym for sym, n in paying.items() for _ in range(n)]
    fill += ["L4"] * (length - len(fill) - sum(specials.values()))
    for _ in range(1000):
        rng.shuffle(fill)
        if all(
            len({fill[(i + k) % len(fill)] for k in range(MAX_RUN + 1)}) > 1 for i in range(len(fill))
        ):
            break
    special = [sym for sym, n in specials.items() for _ in range(n)]
    rng.shuffle(special)
    length = len(fill) + len(special)
    if special:
        gap = length / len(special)
        assert gap >= ROWS, "specials too dense to keep one per window"
        slots = sorted(int(i * gap + rng.uniform(0, gap - ROWS + 1)) for i in range(len(special)))
    else:
        slots = []
    strip, f, s = [], 0, 0
    for i in range(length):
        if s < len(slots) and i == slots[s]:
            strip.append(special[s])
            s += 1
        else:
            strip.append(fill[f])
            f += 1
    for i in range(length):
        window = [strip[(i + k) % length] for k in range(ROWS)]
        assert sum(1 for sym in window if sym in SPECIALS) <= 1, "two specials in one window"
    return strip


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, (specials_per_reel, paying, seed) in STRIPS.items():
        rng = random.Random(seed)
        length = sum(paying.values()) + max(sum(s.values()) for s in specials_per_reel)
        reels = [build_reel(specials, paying, rng, length) for specials in specials_per_reel]
        with open(os.path.join(here, f"{name}.csv"), "w", encoding="UTF-8") as f:
            for i in range(length):
                f.write(",".join(reel[i] for reel in reels) + "\n")
        print(name, [len(r) for r in reels])


if __name__ == "__main__":
    main()
