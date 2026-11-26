"""Main file for generating results for Dwanda.

Usage (from the math-sdk root):
    uv run python games/dwanda/run.py                    # full pipeline, every mode
    uv run python games/dwanda/run.py --sims 2000 --raw  # books only, small sample
    uv run python games/dwanda/run.py --natural 2000000  # only measure the unforced base game
    uv run python games/dwanda/run.py --feature 100000   # only measure unforced The Job sessions per mode
    uv run python games/dwanda/run.py --skip-sims        # reweight existing books and re-check

Weights come from game_weights.py (natural frequencies), not the Rust optimizer.
The design, its targets and the last measurements are in MATH.md.
"""

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
from multiprocessing import Pool

from gamestate import GameState
from game_config import GameConfig
from game_weights import write_natural_lookups, describe_as_conditions
from utils.game_analytics.run_analysis import create_stat_sheet
from utils.rgs_verification import execute_all_tests
from src.state.run_sims import create_books
from src.write_data.write_configs import generate_configs

MODES = ["base", "ante", "bonus", "blaze", "eclipse"]
BUY_MODES = ["bonus", "blaze", "eclipse"]
DEFAULT_SIMS = {"base": 200_000, "ante": 200_000, "bonus": 100_000, "blaze": 100_000, "eclipse": 100_000}
SAME_BOOKS = {"ante": "base"}


def copy_books(config, mode: str, source: str) -> None:
    """Give `mode` the books, lookup tables and records that were simulated for `source`."""
    lib = config.library_path
    pairs = [
        (os.path.join(config.publish_path, f"books_{source}.jsonl.zst"), os.path.join(config.publish_path, f"books_{mode}.jsonl.zst")),
        (os.path.join(lib, "lookup_tables", f"lookUpTable_{source}.csv"), os.path.join(lib, "lookup_tables", f"lookUpTable_{mode}.csv")),
        (os.path.join(lib, "lookup_tables", f"lookUpTableSegmented_{source}.csv"), os.path.join(lib, "lookup_tables", f"lookUpTableSegmented_{mode}.csv")),
        (os.path.join(lib, "forces", f"force_record_{source}.json"), os.path.join(lib, "forces", f"force_record_{mode}.json")),
        (os.path.join(lib, "configs", f"books_{source}.verification.json"), os.path.join(lib, "configs", f"books_{mode}.verification.json")),
    ]
    for src, dst in pairs:
        if os.path.exists(src):
            shutil.copyfile(src, dst)
    published = os.path.join(config.publish_path, f"lookUpTable_{source}_0.csv")
    if os.path.exists(published):
        shutil.copyfile(published, os.path.join(config.publish_path, f"lookUpTable_{mode}_0.csv"))
    force_path = os.path.join(lib, "forces", "force.json")
    with open(force_path, encoding="UTF-8") as f:
        force = json.load(f)
    force[mode] = force[source]
    with open(force_path, "w", encoding="UTF-8") as f:
        json.dump(force, f, indent=4)
    print(f"{mode}: books copied from {source}")


def natural_chunk(args) -> dict:
    spins, seed = args
    gs = GameState(GameConfig())
    gs.betmode, gs.criteria = "base", "basegame"
    random.seed(seed)
    out = {"spins": spins, "hits": 0, "win": 0.0, "win_sq": 0.0, "below_bet": 0, "triggers": {}, "crew_wins": 0}
    trigger = min(gs.config.freespin_triggers[gs.config.basegame_type])
    for _ in range(spins):
        win, scatters = gs.run_natural_spin()
        if scatters >= trigger:
            out["triggers"][scatters] = out["triggers"].get(scatters, 0) + 1
        elif win > 0:
            out["hits"] += 1
            out["win"] += win
            out["win_sq"] += win * win
            out["below_bet"] += win < 1
            out["crew_wins"] += gs.clashes_made > 0
    return out


def measure_natural(config, spins: int, threads: int) -> dict:
    GameState(config)
    per = spins // threads
    with Pool(threads) as pool:
        parts = pool.map(natural_chunk, [(per, 7919 * (i + 1)) for i in range(threads)])
    n = sum(p["spins"] for p in parts)
    triggers = {}
    for p in parts:
        for k, v in p["triggers"].items():
            triggers[k] = triggers.get(k, 0) + v
    hits = sum(p["hits"] for p in parts)
    r = {
        "spins": n,
        "p_freegame": sum(triggers.values()) / n,
        "p_basegame": hits / n,
        "basegame_avg": sum(p["win"] for p in parts) / max(1, hits),
        "basegame_win_sq": sum(p["win_sq"] for p in parts) / n,
        "below_bet_of_hits": sum(p["below_bet"] for p in parts) / max(1, hits),
        "crew_mult_hits": sum(p["crew_wins"] for p in parts) / max(1, hits),
        "trigger_scatters": {str(k): v for k, v in sorted(triggers.items())},
    }
    print(
        f"natural base: free spins 1 in {1 / r['p_freegame']:.1f}, base win 1 in {1 / r['p_basegame']:.2f} "
        f"averaging {r['basegame_avg']:.3f}x (base value {r['p_basegame'] * r['basegame_avg']:.4f}), "
        f"below the bet {r['below_bet_of_hits']:.1%} of hits, a Clash cell made on {r['crew_mult_hits']:.1%} of hits, "
        f"scatters at trigger {r['trigger_scatters']}"
    )
    with open(os.path.join(config.library_path, "natural.json"), "w", encoding="UTF-8") as f:
        json.dump({"base": r}, f, indent=1)
    return r


def feature_chunk(args) -> list:
    mode, scatters, sessions, seed = args
    gs = GameState(GameConfig())
    gs.betmode, gs.criteria = mode, "freegame"
    gs.config.wincap = 1e12
    random.seed(seed)
    return [gs.run_natural_feature(scatters, mode) for _ in range(sessions)]


def summarise(rows, rtp, cap):
    n = len(rows)
    wins = sorted(min(r["win"], cap) for r in rows)
    mean = sum(wins) / n
    price = mean / rtp
    return {
        "sessions": n,
        "mean": round(mean, 2),
        "price": round(price, 1),
        "median_of_cost": round(wins[n // 2] / price, 3),
        "pays_back_cost": round(sum(1 for w in wins if w >= price) / n, 4),
        "below_tenth_of_cost": round(sum(1 for w in wins if w < price / 10) / n, 4),
        "p_cap": sum(1 for r in rows if r["win"] >= cap) / n,
        "ge": {t: sum(1 for w in wins if w >= t) for t in (1000, 5000, 10000, 15000, 20000, 25000)},
        "spins": round(sum(r["spins"] for r in rows) / n, 2),
        "clashes": round(sum(r["clashes"] for r in rows) / n, 2),
        "cells": round(sum(r["cells"] for r in rows) / n, 2),
        "cascades": round(sum(r["cascades"] for r in rows) / n, 2),
        "top": {str(k): round(sum(1 for r in rows if r["top"] == k) / n, 4) for k in sorted({r["top"] for r in rows})},
    }


def measure_feature(config, sessions: int, threads: int, modes: list, scatters: int = 3) -> dict:
    GameState(config)
    per = sessions // threads
    result = {}
    for mode in modes:
        with Pool(threads) as pool:
            parts = pool.map(feature_chunk, [(mode, scatters, per, 104729 * (i + 1) + len(mode)) for i in range(threads)])
        rows = [r for p in parts for r in p]
        s = summarise(rows, config.rtp, config.wincap)
        result[mode] = s
        print(
            f"feature {mode} ({scatters} sc), {s['sessions']} sessions: mean {s['mean']}x -> price {s['price']}x, median {s['median_of_cost']}, "
            f"pays back {s['pays_back_cost']:.1%}, under a tenth {s['below_tenth_of_cost']:.1%}, cap 1 in {1 / max(s['p_cap'], 1e-12):,.0f}; "
            f">= {s['ge']}; spins {s['spins']}, clashes made {s['clashes']}, clash cells at end {s['cells']}, cascades {s['cascades']}, top clash {s['top']}"
        )
    with open(os.path.join(config.library_path, f"feature_{scatters}.json"), "w", encoding="UTF-8") as f:
        json.dump(result, f, indent=1)
    return result


def forced_chunk(args) -> dict:
    forced, boards, seed = args
    gs = GameState(GameConfig())
    gs.betmode, gs.criteria = "base", "freegame"
    gs.quiet = True
    random.seed(seed)
    counts = {}
    for _ in range(boards):
        gs.reset_book()
        gs.force_special_board("scatter", forced)
        gs.run_tumbles()
        final = gs.count_special_symbols("scatter")
        counts[final] = counts.get(final, 0) + 1
    return counts


def measure_forced(config, boards: int, threads: int) -> None:
    """How many scatters a board forced to show 3, 4 or 5 at the reveal ends its tumbles with."""
    GameState(config)
    per = boards // threads
    for forced in (3, 4, 5):
        with Pool(threads) as pool:
            parts = pool.map(forced_chunk, [(forced, per, 15485863 * (i + 1) + forced) for i in range(threads)])
        counts = {}
        for p in parts:
            for k, v in p.items():
                counts[k] = counts.get(k, 0) + v
        n = sum(counts.values())
        print(f"forced {forced}: " + ", ".join(f"{k}: {v / n:.4%}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sims", type=int, default=None)
    parser.add_argument("--modes", nargs="+", default=MODES)
    parser.add_argument("--raw", action="store_true", help="only create books")
    parser.add_argument("--skip-sims", action="store_true", help="reuse the books already in library/")
    parser.add_argument("--natural", type=int, default=None)
    parser.add_argument("--feature", type=int, default=None)
    parser.add_argument("--scatters", type=int, default=3)
    parser.add_argument("--forced", type=int, default=None)
    parser.add_argument("--threads", type=int, default=12)
    args = parser.parse_args()

    config = GameConfig()
    gamestate = GameState(config)

    if args.forced is not None:
        measure_forced(config, args.forced, args.threads)
        sys.exit(0)
    if args.natural is not None or args.feature is not None:
        if args.natural is not None:
            measure_natural(config, args.natural, args.threads)
        if args.feature is not None:
            measure_feature(config, args.feature, args.threads, [m for m in args.modes if m in BUY_MODES] or BUY_MODES, args.scatters)
        sys.exit(0)

    if not args.skip_sims:
        copied = {mode: source for mode, source in SAME_BOOKS.items() if mode in args.modes}
        simulated = [mode for mode in args.modes if mode not in copied]
        simulated += [source for source in copied.values() if source not in simulated]
        num_sim_args = {mode: args.sims or DEFAULT_SIMS[mode] for mode in simulated}
        fewest = min(num_sim_args.values())
        batching_size = 10000 if fewest >= 10000 * args.threads else max(1, fewest // args.threads)
        create_books(gamestate, config, num_sim_args, batching_size, args.threads, True, False)
        for mode, source in copied.items():
            copy_books(config, mode, source)
        if not os.path.exists(os.path.join(config.library_path, "natural.json")):
            measure_natural(config, 4_000_000, args.threads)
    generate_configs(gamestate)

    if not args.raw:
        report = write_natural_lookups(config, MODES)
        for mode, categories in report.items():
            print(f"\n{mode}:")
            for criteria, s in categories.items():
                print(
                    f"  {criteria:9s} 1 in {s['hr']:,.2f}  avg {s['avg']:.2f}x"
                    f"  (natural: 1 in {s['natural_hr']:,.2f}, avg {s['natural_avg']:.2f}x, tilt {s['theta']:+.4f})"
                )
        config.opt_params = describe_as_conditions(config, report)
        generate_configs(gamestate)
        create_stat_sheet(gamestate, custom_keys=[{"symbol": "scatter"}])
        execute_all_tests(config)
        workspace = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        audit = os.path.join(workspace, ".claude", "skills", "stake-reviewer", "scripts", "math_audit.py")
        profile = os.path.join(workspace, ".claude", "skills", "stake-math", "scripts", "math_profile.py")
        game_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(audit):
            subprocess.run([sys.executable, audit, config.publish_path], check=False)
        if os.path.exists(profile):
            subprocess.run([sys.executable, profile, game_dir, "--targets", os.path.join(game_dir, "math_targets.json")], check=False)
