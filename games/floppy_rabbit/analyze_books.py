"""Counters the standard files do not hold, read from the published books and their weights.

Usage (from the math-sdk root):
    uv run python games/floppy_rabbit/analyze_books.py [mode ...]

Per mode, weighted by the published lookup table:
* winning cascades per board (a board is one base spin or one free spin),
* how often a base spin has a win that a footprint multiplied, and how often it shows a flop,
* the share of the mode's RTP paid through footprints,
* for rounds with Flop Time: spins played, retriggers, hops and flops per session, sessions
  without a flop, sessions that return under a tenth of the mode's cost, footprints on the
  board and the largest one when the session ends, and the share of sessions and of RTP by the
  number of rabbits.
Writes library/book_stats.json, which MATH.md quotes.
"""

import csv
import io
import json
import os
import sys

import zstandard as zstd

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLISH = os.path.join(HERE, "library", "publish_files")


def read_weights(mode: dict) -> dict:
    weights = {}
    with open(os.path.join(PUBLISH, mode["weights"]), encoding="UTF-8") as f:
        for sim, weight, _ in csv.reader(f):
            weights[int(sim)] = int(weight)
    total = sum(weights.values())
    return {sim: w / total for sim, w in weights.items()}


def analyze(mode: dict) -> dict:
    probs = read_weights(mode)
    cost = float(mode["cost"])
    s = {
        k: 0.0
        for k in (
            "boards cascades win multiplied_win base_multiplied base_flop fs_rounds fs_spins fs_retriggered "
            "fs_hops fs_flops fs_no_flop fs_under_tenth fs_cells"
        ).split()
    }
    top_cell, by_rabbits = {}, {}
    with open(os.path.join(PUBLISH, mode["events"]), "rb") as raw:
        reader = io.TextIOWrapper(zstd.ZstdDecompressor().stream_reader(raw, read_across_frames=True), encoding="UTF-8")
        for line in reader:
            book = json.loads(line)
            p = probs[book["id"]]
            in_fs = base_multiplied = base_flop = False
            spins = retriggers = hops = flops = rabbits = 0
            prints = None
            for event in book["events"]:
                kind = event["type"]
                if kind == "reveal":
                    s["boards"] += p
                elif kind == "winInfo":
                    s["cascades"] += p
                    for win in event["wins"]:
                        s["win"] += p * win["win"] / 100
                        if win["meta"]["clusterMult"] > 1:
                            s["multiplied_win"] += p * win["win"] / 100
                            if not in_fs:
                                base_multiplied = True
                elif kind == "rabbitsEnter":
                    in_fs = True
                    rabbits = len(event["rabbits"])
                    prints = event["footprints"]
                elif kind == "rabbitHop":
                    if in_fs:
                        hops += 1
                        prints = event["footprints"]
                elif kind == "rabbitFlop":
                    if in_fs:
                        flops += 1
                        prints = event["footprints"]
                    else:
                        base_flop = True
                elif kind == "updateFreeSpin":
                    spins += 1
                elif kind == "freeSpinRetrigger":
                    retriggers += 1
            s["base_multiplied"] += p * base_multiplied
            s["base_flop"] += p * base_flop
            if in_fs:
                payout = book["payoutMultiplier"] / 100
                s["fs_rounds"] += p
                s["fs_spins"] += p * spins
                s["fs_retriggered"] += p * (retriggers > 0)
                s["fs_hops"] += p * hops
                s["fs_flops"] += p * flops
                s["fs_no_flop"] += p * (flops == 0)
                s["fs_under_tenth"] += p * (payout < 0.1 * cost)
                s["fs_cells"] += p * sum(1 for column in prints for v in column if v)
                top = max(max(column) for column in prints)
                top_cell[top] = top_cell.get(top, 0.0) + p
                entry = by_rabbits.setdefault(rabbits, [0.0, 0.0])
                entry[0] += p
                entry[1] += p * payout
    fs = s["fs_rounds"]
    return {
        "mode": mode["name"],
        "cascades_per_board": s["cascades"] / s["boards"],
        "rounds_with_base_win_multiplied": s["base_multiplied"],
        "rounds_with_base_flop": s["base_flop"],
        "rtp_through_footprints": s["multiplied_win"] / s["win"] if s["win"] else 0.0,
        "rtp_from_events": s["win"] / cost,
        "free_spins_played": s["fs_spins"] / fs if fs else 0.0,
        "sessions_retriggered": s["fs_retriggered"] / fs if fs else 0.0,
        "hops_per_session": s["fs_hops"] / fs if fs else 0.0,
        "flops_per_session": s["fs_flops"] / fs if fs else 0.0,
        "sessions_without_flop": s["fs_no_flop"] / fs if fs else 0.0,
        "sessions_under_tenth_of_cost": s["fs_under_tenth"] / fs if fs else 0.0,
        "footprints_at_end": s["fs_cells"] / fs if fs else 0.0,
        "top_footprint_at_end": {str(k): v / fs for k, v in sorted(top_cell.items())} if fs else {},
        "sessions_by_rabbits": {str(k): {"share": v[0] / fs, "rtp_points": 100 * v[1] / cost} for k, v in sorted(by_rabbits.items())},
    }


if __name__ == "__main__":
    index = json.load(open(os.path.join(PUBLISH, "index.json"), encoding="UTF-8"))
    wanted = sys.argv[1:]
    stats = {}
    for mode in index["modes"]:
        if wanted and mode["name"] not in wanted:
            continue
        r = analyze(mode)
        stats[r["mode"]] = r
        tops = ", ".join(f"{k}x {100 * v:.2f}%" for k, v in r["top_footprint_at_end"].items() if v >= 0.00005)
        rabbits = ", ".join(f"{k}: {100 * v['share']:.3f}% of sessions, {v['rtp_points']:.2f} RTP points" for k, v in r["sessions_by_rabbits"].items())
        print(
            f"\n{r['mode']}: {r['cascades_per_board']:.2f} winning cascades per board; rounds with a base win through a "
            f"footprint {100 * r['rounds_with_base_win_multiplied']:.1f}%, with a base flop {100 * r['rounds_with_base_flop']:.2f}%; "
            f"RTP through footprints {100 * r['rtp_through_footprints']:.1f}% (RTP from events {100 * r['rtp_from_events']:.2f}%)\n"
            f"  Flop Time: {r['free_spins_played']:.1f} spins played, {100 * r['sessions_retriggered']:.1f}% retrigger, "
            f"{r['hops_per_session']:.1f} hops and {r['flops_per_session']:.2f} flops per session "
            f"({100 * r['sessions_without_flop']:.1f}% of sessions have no flop), "
            f"{100 * r['sessions_under_tenth_of_cost']:.1f}% return under a tenth of the cost, "
            f"{r['footprints_at_end']:.1f} footprints at the end\n"
            f"  rabbits: {rabbits}\n"
            f"  largest footprint at the end: {tops}"
        )
    path = os.path.join(HERE, "library", "book_stats.json")
    old = json.load(open(path, encoding="UTF-8")) if os.path.exists(path) else {}
    old.update(stats)
    json.dump(old, open(path, "w", encoding="UTF-8"), indent=1)
