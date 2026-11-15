"""Counters the standard files do not hold, read from the published books and their weights.

Usage (from the math-sdk root):
    uv run python games/pratala/analyze_books.py [mode ...]

Per mode, weighted by the published lookup table:
* tumble wins per board (a board is one base spin or one free spin),
* how often a base spin shows a Glint Strike and how often a win is multiplied,
* the share of the mode's RTP paid through a Glint multiplier,
* the highest multiplier applied in a round,
* for rounds with free spins: how many spins were played, how often they retriggered, and
  how often the session ended without any multiplied win.
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
        "boards": 0.0,
        "tumble_wins": 0.0,
        "strike_spins": 0.0,
        "multiplied_base_spins": 0.0,
        "win": 0.0,
        "multiplied_win": 0.0,
        "fs_rounds": 0.0,
        "fs_spins": 0.0,
        "fs_retriggered": 0.0,
        "fs_no_multiplier": 0.0,
    }
    top_mult = {}
    with open(os.path.join(PUBLISH, mode["events"]), "rb") as raw:
        reader = io.TextIOWrapper(zstd.ZstdDecompressor().stream_reader(raw), encoding="UTF-8")
        for line in reader:
            book = json.loads(line)
            p = probs[book["id"]]
            in_fs = False
            top = 1
            fs_top = 1
            base_strike = base_multiplied = False
            spins = retriggers = 0
            for event in book["events"]:
                kind = event["type"]
                if kind == "reveal":
                    s["boards"] += p
                elif kind == "winInfo":
                    s["tumble_wins"] += p
                    for win in event["wins"]:
                        mult = win["meta"]["clusterMult"]
                        s["win"] += p * win["win"] / 100
                        if mult > 1:
                            s["multiplied_win"] += p * win["win"] / 100
                            top = max(top, mult)
                            if in_fs:
                                fs_top = max(fs_top, mult)
                            else:
                                base_multiplied = True
                elif kind == "glintStrike" and not in_fs:
                    base_strike = True
                elif kind == "freeSpinTrigger":
                    in_fs = True
                elif kind == "updateFreeSpin":
                    spins += 1
                elif kind == "freeSpinRetrigger":
                    retriggers += 1
            if base_strike:
                s["strike_spins"] += p
            if base_multiplied:
                s["multiplied_base_spins"] += p
            if in_fs:
                s["fs_rounds"] += p
                s["fs_spins"] += p * spins
                if retriggers:
                    s["fs_retriggered"] += p
                if fs_top == 1:
                    s["fs_no_multiplier"] += p
            top_mult[top] = top_mult.get(top, 0.0) + p
    fs = s["fs_rounds"]
    return {
        "mode": mode["name"],
        "tumble_wins_per_board": s["tumble_wins"] / s["boards"],
        "base_spins_with_strike": s["strike_spins"],
        "base_spins_with_multiplied_win": s["multiplied_base_spins"],
        "rtp_through_multipliers": s["multiplied_win"] / s["win"] if s["win"] else 0.0,
        "rtp_from_events": s["win"] / cost,
        "free_spins_played": s["fs_spins"] / fs if fs else 0.0,
        "sessions_retriggered": s["fs_retriggered"] / fs if fs else 0.0,
        "sessions_without_multiplied_win": s["fs_no_multiplier"] / fs if fs else 0.0,
        "top_multiplier_in_round": {str(k): v for k, v in sorted(top_mult.items())},
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
        tops = ", ".join(f"{k}x {100 * v:.2f}%" for k, v in r["top_multiplier_in_round"].items() if v >= 0.00005)
        print(
            f"\n{r['mode']}: {r['tumble_wins_per_board']:.2f} tumble wins per board; "
            f"base spins with a strike {100 * r['base_spins_with_strike']:.1f}%, with a multiplied win "
            f"{100 * r['base_spins_with_multiplied_win']:.1f}%; RTP through multipliers "
            f"{100 * r['rtp_through_multipliers']:.1f}% (RTP from events {100 * r['rtp_from_events']:.2f}%)\n"
            f"  free spins: {r['free_spins_played']:.1f} spins played, {100 * r['sessions_retriggered']:.1f}% retrigger, "
            f"{100 * r['sessions_without_multiplied_win']:.1f}% end without a multiplied win\n"
            f"  top multiplier in a round: {tops}"
        )
    path = os.path.join(HERE, "library", "book_stats.json")
    old = json.load(open(path, encoding="UTF-8")) if os.path.exists(path) else {}
    old.update(stats)
    json.dump(old, open(path, "w", encoding="UTF-8"), indent=1)
