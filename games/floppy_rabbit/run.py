"""Main file for generating results for Floppy Rabbit.

Usage (from the math-sdk root):
    uv run python games/floppy_rabbit/run.py                    # full pipeline, every mode
    uv run python games/floppy_rabbit/run.py --sims 2000 --raw  # books only, small sample
    uv run python games/floppy_rabbit/run.py --natural 2000000  # only measure what the reels do unforced
    uv run python games/floppy_rabbit/run.py --feature 100000   # only measure unforced Flop Time sessions
    uv run python games/floppy_rabbit/run.py --forced 200000    # scatters a forced reveal ends with
    uv run python games/floppy_rabbit/run.py --skip-sims        # reweight existing books and re-check

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

MODES = ["base", "ante", "bonus", "double", "fluffle"]
# Spin modes get more books: only a tenth of them are free spins.
DEFAULT_SIMS = {"base": 200_000, "ante": 200_000, "bonus": 100_000, "double": 100_000, "fluffle": 100_000}
NATURAL_MODES = ["base"]
# Ante plays the base mode's rounds at other odds: same rules, same seeds, so the same books.
# They are simulated once and copied; only the weights differ (game_weights.py).
SAME_BOOKS = {"ante": "base"}


def copy_books(config, mode: str, source: str) -> None:
    """Give `mode` the books, lookup tables and records that were simulated for `source`."""
    lib = config.library_path
    pairs = [
        (os.path.join(config.publish_path, f"books_{source}.jsonl.zst"), os.path.join(config.publish_path, f"books_{mode}.jsonl.zst")),
        (os.path.join(lib, "lookup_tables", f"lookUpTable_{source}.csv"), os.path.join(lib, "lookup_tables", f"lookUpTable_{mode}.csv")),
        (
            os.path.join(lib, "lookup_tables", f"lookUpTableSegmented_{source}.csv"),
            os.path.join(lib, "lookup_tables", f"lookUpTableSegmented_{mode}.csv"),
        ),
        (os.path.join(lib, "forces", f"force_record_{source}.json"), os.path.join(lib, "forces", f"force_record_{mode}.json")),
        (
            os.path.join(lib, "configs", f"books_{source}.verification.json"),
            os.path.join(lib, "configs", f"books_{mode}.verification.json"),
        ),
    ]
    for src, dst in pairs:
        shutil.copyfile(src, dst)
    # The config writer hashes every mode's published lookup table; game_weights.py rewrites it.
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
    """Play unforced base spins of one mode and count what happens."""
    mode, spins, seed = args
    gamestate = GameState(GameConfig())
    gamestate.betmode, gamestate.criteria = mode, "basegame"
    random.seed(seed)
    out = {"spins": spins, "hits": 0, "win": 0.0, "win_sq": 0.0, "below_bet": 0, "cascades": 0, "flops": 0, "triggers": {}}
    trigger = min(gamestate.config.freespin_triggers[gamestate.config.basegame_type])
    for _ in range(spins):
        win, scatters = gamestate.run_natural_spin()
        out["cascades"] += gamestate.cascade_count
        out["flops"] += gamestate.flop_count
        if scatters >= trigger:
            out["triggers"][scatters] = out["triggers"].get(scatters, 0) + 1
        elif win > 0:
            out["hits"] += 1
            out["win"] += win
            out["win_sq"] += win * win
            if win < 1:
                out["below_bet"] += 1
    return out


def measure_natural(config, spins: int, threads: int) -> dict:
    """Unforced base game numbers per mode, written to library/natural.json for game_weights.py."""
    result = {}
    per = spins // threads
    # Each worker builds its own game state, which creates the SDK's output folders if they are
    # missing; make them here first so the workers do not race to create the same one.
    GameState(config)
    for mode in NATURAL_MODES:
        with Pool(threads) as pool:
            parts = pool.map(natural_chunk, [(mode, per, 7919 * (i + 1)) for i in range(threads)])
        n = sum(p["spins"] for p in parts)
        triggers = {}
        for p in parts:
            for k, v in p["triggers"].items():
                triggers[k] = triggers.get(k, 0) + v
        n_trigger = sum(triggers.values())
        hits = sum(p["hits"] for p in parts)
        result[mode] = {
            "spins": n,
            "p_freegame": n_trigger / n,
            "p_basegame": hits / n,
            "basegame_avg": sum(p["win"] for p in parts) / max(1, hits),
            "basegame_win_sq": sum(p["win_sq"] for p in parts) / n,
            "below_bet_of_hits": sum(p["below_bet"] for p in parts) / max(1, hits),
            "cascades_per_spin": sum(p["cascades"] for p in parts) / n,
            "flops_per_spin": sum(p["flops"] for p in parts) / n,
            "trigger_scatters": {str(k): v for k, v in sorted(triggers.items())},
        }
        r = result[mode]
        print(
            f"natural {mode}: free spins 1 in {1 / r['p_freegame']:.1f}, base win 1 in {1 / r['p_basegame']:.2f} "
            f"averaging {r['basegame_avg']:.3f}x (base value {r['p_basegame'] * r['basegame_avg']:.4f}), "
            f"below the bet {r['below_bet_of_hits']:.1%} of hits, cascades per spin {r['cascades_per_spin']:.3f}, "
            f"flops per spin {r['flops_per_spin']:.4f}, scatters at trigger {r['trigger_scatters']}"
        )
    with open(os.path.join(config.library_path, "natural.json"), "w", encoding="UTF-8") as f:
        json.dump(result, f, indent=1)
    return result


def feature_chunk(args) -> list:
    scatters, sessions, seed = args
    gamestate = GameState(GameConfig())
    gamestate.betmode, gamestate.criteria = "bonus", "freegame"
    gamestate.config.wincap = 1e12  # measure the uncapped session; caps are applied when reading
    random.seed(seed)
    return [gamestate.run_natural_feature(scatters) for _ in range(sessions)]


def measure_feature(config, sessions: int, threads: int, only=None) -> dict:
    """Unforced Flop Time sessions per trigger size, written to library/feature.json."""
    GameState(config)
    rtp = config.rtp
    result = {}
    per = sessions // threads
    for scatters in only or sorted(config.rabbits_by_scatters):
        with Pool(threads) as pool:
            parts = pool.map(feature_chunk, [(scatters, per, 104729 * (i + 1) + scatters) for i in range(threads)])
        rows = [row for part in parts for row in part]
        n = len(rows)
        wins = sorted(r["win"] for r in rows)
        out = {"sessions": n, "rabbits": config.rabbits_by_scatters[scatters]}
        for cap in (25000, 50000):
            mean = sum(min(w, cap) for w in wins) / n
            sq = sum(min(w, cap) ** 2 for w in wins) / n
            price = mean / rtp
            out[f"cap_{cap}"] = {
                "mean": round(mean, 2),
                "mean_square": round(sq, 1),
                "price": round(price, 1),
                "median_of_cost": round(wins[n // 2] / price, 3),
                "pays_back_cost": round(sum(1 for w in wins if w >= price) / n, 4),
                "below_tenth_of_cost": round(sum(1 for w in wins if w < price / 10) / n, 4),
            }
        for threshold in (1000, 5000, 10000, 25000, 50000):
            k = sum(1 for w in wins if w >= threshold)
            out[f"p_ge_{threshold}"] = {"count": k, "p": k / n}
        out["zero_win"] = sum(1 for w in wins if w == 0) / n
        out["hops"] = round(sum(r["hops"] for r in rows) / n, 2)
        out["flops"] = round(sum(r["flops"] for r in rows) / n, 2)
        out["no_flop"] = round(sum(1 for r in rows if r["flops"] == 0) / n, 4)
        out["spins"] = round(sum(r["spins"] for r in rows) / n, 2)
        out["retriggered"] = round(sum(1 for r in rows if r["spins"] > 12) / n, 4)
        out["cells"] = round(sum(r["cells"] for r in rows) / n, 1)
        tops = {}
        for r in rows:
            tops[r["top"]] = tops.get(r["top"], 0) + 1
        out["top_cell"] = {str(k): round(v / n, 4) for k, v in sorted(tops.items())}
        result[str(scatters)] = out
        c = out["cap_25000"]
        print(
            f"feature {scatters} scatters ({out['rabbits']} rabbits), {n} sessions: mean {c['mean']}x -> price {c['price']}x, "
            f"median {c['median_of_cost']}, pays back {c['pays_back_cost']:.1%}, under a tenth {c['below_tenth_of_cost']:.1%}; "
            + ", ".join(f">={t}: {out[f'p_ge_{t}']['count']}" for t in (5000, 10000, 25000, 50000))
            + f"; hops {out['hops']}, flops {out['flops']}, no flop {out['no_flop']:.1%}, spins {out['spins']}, "
            f"retriggered {out['retriggered']:.1%}, cells {out['cells']}, zero {out['zero_win']:.2%}"
        )
    with open(os.path.join(config.library_path, "feature.json"), "w", encoding="UTF-8") as f:
        json.dump(result, f, indent=1)
    return result


def forced_chunk(args) -> dict:
    forced, boards, seed = args
    gamestate = GameState(GameConfig())
    gamestate.betmode, gamestate.criteria = "base", "freegame"
    random.seed(seed)
    counts = {}
    for _ in range(boards):
        gamestate.reset_book()
        gamestate.force_special_board("scatter", forced)
        gamestate.reveal_hop()
        gamestate.run_tumbles()
        final = gamestate.count_special_symbols("scatter")
        counts[final] = counts.get(final, 0) + 1
    return counts


def measure_forced(config, boards: int, threads: int) -> None:
    """How many scatters a board forced to show 3, 4 or 5 at the reveal ends its cascades with."""
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
    parser.add_argument("--sims", type=int, default=None, help="simulations per mode (default: 200k spin modes, 100k buy modes)")
    parser.add_argument("--modes", nargs="+", default=MODES)
    parser.add_argument("--raw", action="store_true", help="only create books")
    parser.add_argument("--skip-sims", action="store_true", help="reuse the books already in library/")
    parser.add_argument("--natural", type=int, default=None, help="only measure this many unforced base spins per mode")
    parser.add_argument("--feature", type=int, default=None, help="only measure this many unforced Flop Time sessions per trigger size")
    parser.add_argument("--forced", type=int, default=None, help="only measure this many forced reveals per scatter count")
    parser.add_argument("--scatters", type=int, nargs="+", default=None, help="with --feature: only these trigger sizes")
    parser.add_argument("--threads", type=int, default=10)
    args = parser.parse_args()

    num_threads = args.threads
    compression = True
    profiling = False

    config = GameConfig()
    gamestate = GameState(config)

    if args.natural is not None or args.feature is not None or args.forced is not None:
        if args.natural is not None:
            measure_natural(config, args.natural, num_threads)
        if args.feature is not None:
            measure_feature(config, args.feature, num_threads, args.scatters)
        if args.forced is not None:
            measure_forced(config, args.forced, num_threads)
        sys.exit(0)

    if not args.skip_sims:
        copied = {mode: source for mode, source in SAME_BOOKS.items() if mode in args.modes}
        simulated = [mode for mode in args.modes if mode not in copied]
        simulated += [source for source in copied.values() if source not in simulated]
        num_sim_args = {mode: args.sims or DEFAULT_SIMS[mode] for mode in simulated}
        fewest = min(num_sim_args.values())
        batching_size = 10000 if fewest >= 10000 * num_threads else max(1, fewest // num_threads)
        create_books(gamestate, config, num_sim_args, batching_size, num_threads, compression, profiling)
        for mode, source in copied.items():
            copy_books(config, mode, source)
        if not os.path.exists(os.path.join(config.library_path, "natural.json")):
            measure_natural(config, 4_000_000, num_threads)
    generate_configs(gamestate)

    if not args.raw:
        # Always reweight every mode: the published index lists them all.
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
        # Engine's limits and the design targets are checked by the studio's two scripts, when present.
        workspace = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        audit = os.path.join(workspace, ".claude", "skills", "stake-reviewer", "scripts", "math_audit.py")
        profile = os.path.join(workspace, ".claude", "skills", "stake-math", "scripts", "math_profile.py")
        game_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(audit):
            subprocess.run([sys.executable, audit, config.publish_path], check=False)
        if os.path.exists(profile):
            subprocess.run(
                [sys.executable, profile, game_dir, "--targets", os.path.join(game_dir, "math_targets.json")], check=False
            )
