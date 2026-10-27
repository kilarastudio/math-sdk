"""Generate the DEEP GLINT reel strips from symbol weights.

Run from anywhere:  python games/deep_glint/reels/make_reels.py
Each strip has 6 reels of 250 stops. Scatters sit on stops 5 apart, so a reel never
shows more than one at the reveal (tumbles can still bring a second one down).
"""

import os
import random

LENGTH = 250
STRIPS = {
    # name: (symbol weights, scatters per reel, seed)
    "BR0": ({"H1": 8, "H2": 10, "H3": 12, "H4": 14, "L1": 16, "L2": 18, "L3": 20, "L4": 22}, 6, 7),
    "FR0": ({"H1": 9, "H2": 11, "H3": 13, "H4": 15, "L1": 17, "L2": 19, "L3": 22, "L4": 26}, 3, 11),
    # Richer free spins strip, only used to find max-win rounds.
    # It drops L4, so wins chain more often and about 1 in 60 sessions reaches the cap.
    "WCAP": ({"H1": 12, "H2": 12, "H3": 12, "H4": 12, "L1": 20, "L2": 24, "L3": 28}, 3, 11),
}


def make_strip(weights: dict, scatters: int, seed: int) -> list:
    rng = random.Random(seed)
    pool = [s for s, w in weights.items() for _ in range(w)]
    reels = []
    for _ in range(6):
        reel = [pool[rng.randrange(len(pool))] for _ in range(LENGTH)]
        for stop in rng.sample(range(0, LENGTH, 5), scatters):
            reel[stop] = "S"
        reels.append(reel)
    return reels


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    for name, (weights, scatters, seed) in STRIPS.items():
        reels = make_strip(weights, scatters, seed)
        with open(os.path.join(here, f"{name}.csv"), "w", encoding="UTF-8") as f:
            for stop in range(LENGTH):
                f.write(",".join(reel[stop] for reel in reels) + "\n")
        print(f"wrote {name}.csv")
