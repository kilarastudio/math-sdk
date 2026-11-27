"""Exact weights: a book's weight is the number of ordered draws that give its pattern, times
the share of rounds that mark its number of Kilau numbers.

No optimizer and no sampling. Every round is published the same number of times, so the
lookup table of a mode is the true keno distribution for that pick count and its RTP is an
exact sum. Weights are divided by their common factor to keep their total inside uint64.
"""

import csv
import os
from functools import reduce
from math import gcd

from game_calculations import mode_rounds


def write_exact_lookups(config) -> dict:
    """Rewrite library/publish_files/lookUpTable_<mode>_0.csv with exact weights."""
    report = {}
    for bm in config.bet_modes:
        mode = bm.get_name()
        _, picks, draws, options = config.mode_parts(mode)
        rounds = mode_rounds(picks, draws, options, config.board_numbers)
        source = os.path.join(config.library_path, "lookup_tables", f"lookUpTable_{mode}.csv")
        with open(source, encoding="UTF-8") as f:
            rows = [(int(r[0]), int(float(r[2]))) for r in csv.reader(f)]
        assert len(rows) % len(rounds) == 0, f"{mode}: {len(rows)} books for {len(rounds)} rounds"
        weights = [weight for _, _, weight in rounds]
        factor = reduce(gcd, weights)
        weights = [w // factor for w in weights]
        total = paid = 0
        path = os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv")
        with open(path, "w", encoding="UTF-8") as f:
            for sim, cents in rows:
                weight = weights[sim % len(rounds)]
                f.write(f"{sim},{weight},{cents}\n")
                total += weight
                paid += weight * cents
        assert total < 2**64, f"{mode}: weights sum to {total}, beyond uint64"
        report[mode] = {"books": len(rows), "rtp": paid / total / 100 / bm.get_cost()}
    return report
