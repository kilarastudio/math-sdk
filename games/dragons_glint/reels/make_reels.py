"""Generate the Dragon's Glint reel strips from symbol counts.

Run from anywhere:  python games/dragons_glint/reels/make_reels.py

Each strip has 6 reels of 250 stops. A reel holds exactly the listed number of every symbol
(the same on all six reels), shuffled with a fixed seed, so a reel change is a change to one
number here and gives the same strip on every run. Scatters sit on stops 5 apart, so a reel
never shows more than one at the reveal (tumbles can still bring a second one down).
"""

import os
import random

LENGTH = 250
STRIPS = {
    # name: (symbol stops per reel, scatters on each of the six reels, seed)
    # Base game: free spins trigger about 1 in 300 spins from these scatter counts.
    "BR0": ({"H1": 19, "H2": 22, "H3": 24, "H4": 28, "L1": 31, "L2": 36, "L3": 40, "L4": 45}, [6, 6, 6, 5, 5, 5], 7),
    # Free spins: 3+ scatters retrigger, in about one session in seven.
    "FR0": ({"H1": 19, "H2": 22, "H3": 25, "H4": 28, "L1": 31, "L2": 36, "L3": 40, "L4": 45}, [4, 4, 4, 4, 4, 4], 11),
}


def make_strip(counts: dict, scatters: list, seed: int) -> list:
    rng = random.Random(seed)
    reels = []
    for n_scatter in scatters:
        symbols = [s for s, n in counts.items() for _ in range(n)]
        # The counts fill the reel with the fewest scatters; a reel with more drops random symbols.
        assert len(symbols) == LENGTH - min(scatters), f"counts must add up to {LENGTH - min(scatters)}"
        rng.shuffle(symbols)
        symbols = symbols[: LENGTH - n_scatter]
        stops = set(rng.sample(range(0, LENGTH, 5), n_scatter))
        reel, it = [], iter(symbols)
        for stop in range(LENGTH):
            reel.append("S" if stop in stops else next(it))
        reels.append(reel)
    return reels


def write_strips(names=None) -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    for name, (counts, scatters, seed) in STRIPS.items():
        if names and name not in names:
            continue
        reels = make_strip(counts, scatters, seed)
        with open(os.path.join(here, f"{name}.csv"), "w", encoding="UTF-8") as f:
            for stop in range(LENGTH):
                f.write(",".join(reel[stop] for reel in reels) + "\n")
        print(f"wrote {name}.csv")


if __name__ == "__main__":
    write_strips()
